# Copyright © 2025 Apple Inc.
#
# GLM-5 / GLM-5.2  (model_type: "glm_moe_dsa") — a DeepSeek-V3.2-style MoE with MLA +
# DeepSeek Sparse Attention (DSA). Built on top of the `deepseek_v32` model; the only
# architectural difference is the DSA `indexer_types` (full / shared) scheme: GLM places
# the lightning-indexer weights only on `'full'` layers, while `'shared'` layers reuse
# the top-k indices computed by the most recent full layer (in groups of `index_topk_freq`).
# A naive port that builds an indexer on every layer fails to load ("Missing parameters"
# on the shared layers); this handles both layer kinds.

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import mlx.core as mx
import mlx.nn as nn

from .base import BaseModelArgs
from . import deepseek_v32 as dsv32

# Stream eval per layer so a >RAM model can run on 128GB via mmap paging.
# Set GLM_STREAM_EVAL=0 to disable (faster when the model fits in RAM, e.g. pruned).
GLM_STREAM_EVAL = os.environ.get("GLM_STREAM_EVAL", "1") != "0"


@dataclass
class ModelArgs(BaseModelArgs):
    model_type: str
    vocab_size: int
    hidden_size: int
    index_head_dim: int
    index_n_heads: int
    index_topk: int
    intermediate_size: int
    moe_intermediate_size: int
    num_hidden_layers: int
    num_attention_heads: int
    num_key_value_heads: int
    n_shared_experts: Optional[int]
    n_routed_experts: Optional[int]
    routed_scaling_factor: float
    kv_lora_rank: int
    q_lora_rank: int
    qk_rope_head_dim: int
    v_head_dim: int
    qk_nope_head_dim: int
    topk_method: str
    scoring_func: str
    norm_topk_prob: bool
    n_group: int
    topk_group: int
    num_experts_per_tok: int
    moe_layer_freq: int
    first_k_dense_replace: int
    max_position_embeddings: int
    rms_norm_eps: float
    rope_parameters: Dict
    attention_bias: bool
    # GLM-5.2 DSA sharing: per-layer 'full' | 'shared'; full layers own an indexer.
    indexer_types: Optional[List[str]] = None
    index_topk_freq: int = 4
    rope_scaling: Dict = None
    rope_theta: Optional[float] = None

    def __post_init__(self):
        self.rope_scaling = self.rope_parameters
        self.rope_theta = self.rope_parameters["rope_theta"]


def _is_full(config: ModelArgs, layer_idx: int) -> bool:
    """Does this layer own a DSA indexer? Default to all-full if unspecified."""
    if not config.indexer_types:
        return True
    if layer_idx < len(config.indexer_types):
        return config.indexer_types[layer_idx] == "full"
    return True


class GlmDsaAttention(dsv32.DeepseekV32Attention):
    """DeepSeek-V3.2 attention, but the indexer exists only on 'full' layers.
    'shared' layers receive `shared_topk` (the full layer's topk) and reuse it."""

    def __init__(self, config: ModelArgs, is_full: bool):
        super().__init__(config)
        self.is_full = is_full
        if not is_full:
            # drop the indexer so no indexer weights are expected on this layer
            self.indexer = None

    def __call__(self, x, mask=None, cache=None, shared_topk=None):
        B, L, D = x.shape

        qr = self.q_a_layernorm(self.q_a_proj(x))
        q = self.q_b_proj(qr)
        q = q.reshape(B, L, self.num_heads, self.q_head_dim).transpose(0, 2, 1, 3)
        q_nope, q_pe = mx.split(q, [self.qk_nope_head_dim], axis=-1)
        compressed_kv = self.kv_a_proj_with_mqa(x)
        compressed_kv, k_pe = mx.split(compressed_kv, [self.kv_lora_rank], axis=-1)
        k_pe = k_pe.reshape(B, L, 1, self.qk_rope_head_dim).transpose(0, 2, 1, 3)
        kv_latent = self.kv_a_layernorm(compressed_kv)

        offset = cache[0].offset if cache is not None else 0
        q_pe = self.rope(q_pe, offset)
        k_pe = self.rope(k_pe, offset)

        kv_latent = mx.expand_dims(kv_latent, axis=1)
        if cache is not None:
            kv_latent, k_pe = cache[0].update_and_fetch(kv_latent, k_pe)
        else:
            cache = [None] * 2

        # topk: compute on full layers, reuse the shared one otherwise.
        if self.is_full and self.indexer is not None:
            topk_indices = self.indexer(x, qr, mask, cache=cache[1])
        else:
            topk_indices = shared_topk

        if topk_indices is not None:
            if L == 1:
                idx = topk_indices[:, :, 0, :, None]
                kv_latent = mx.take_along_axis(
                    kv_latent,
                    mx.broadcast_to(idx, idx.shape[:-1] + (kv_latent.shape[-1],)),
                    axis=2,
                )
                k_pe = mx.take_along_axis(
                    k_pe,
                    mx.broadcast_to(idx, idx.shape[:-1] + (k_pe.shape[-1],)),
                    axis=2,
                )
                if mask is not None:
                    mask = mx.take_along_axis(mask, topk_indices, axis=-1)
            else:
                shape = list(topk_indices.shape)
                shape[-1] = kv_latent.shape[2]
                sparse_mask = mx.zeros(shape, dtype=mx.bool_)
                sparse_mask = mx.put_along_axis(
                    sparse_mask, topk_indices, mx.array(True), axis=-1
                )
                if mask is not None:
                    sparse_mask = sparse_mask & mask
                mask = sparse_mask

        # keep the indexer cache in the graph only when this layer has one
        if (self.is_full and cache is not None and cache[0] is not None
                and cache[1] is not None):
            cache[0].keys = mx.depends(
                cache[0].keys, (cache[1].keys, cache[1].values))

        pe_scores = (q_pe * self.scale) @ k_pe.swapaxes(-1, -2)
        if mask is not None:
            pe_scores = mx.where(
                mask, pe_scores,
                mx.array(mx.finfo(pe_scores.dtype).min, pe_scores.dtype))

        if L == 1:
            q_nope = self.embed_q(q_nope)
            k = v = kv_latent
        else:
            k = self.embed_q(kv_latent, transpose=False)
            v = self.unembed_out(kv_latent)

        output = dsv32.scaled_dot_product_attention(
            q_nope, k, v, cache=cache, scale=self.scale, mask=pe_scores)
        if L == 1:
            output = self.unembed_out(output)

        output = output.transpose(0, 2, 1, 3).reshape(B, L, -1)
        return self.o_proj(output), topk_indices


class GlmDsaDecoderLayer(nn.Module):
    def __init__(self, config: ModelArgs, layer_idx: int):
        super().__init__()
        self.is_full = _is_full(config, layer_idx)
        self.self_attn = GlmDsaAttention(config, self.is_full)
        self.mlp = (
            dsv32.DeepseekV32MoE(config)
            if (config.n_routed_experts is not None
                and layer_idx >= config.first_k_dense_replace
                and layer_idx % config.moe_layer_freq == 0)
            else dsv32.DeepseekV32MLP(config))
        self.input_layernorm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = nn.RMSNorm(
            config.hidden_size, eps=config.rms_norm_eps)

    def __call__(self, x, mask=None, cache=None, shared_topk=None):
        r, topk = self.self_attn(self.input_layernorm(x), mask, cache, shared_topk)
        h = x + r
        r = self.mlp(self.post_attention_layernorm(h))
        return h + r, topk


class GlmDsaModel(dsv32.DeepseekV32Model):
    def __init__(self, config: ModelArgs):
        nn.Module.__init__(self)
        self.vocab_size = config.vocab_size
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.layers = [
            GlmDsaDecoderLayer(config, idx)
            for idx in range(config.num_hidden_layers)
        ]
        self.start_idx = 0
        self.end_idx = len(self.layers)
        self.num_layers = self.end_idx
        self.norm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.pipeline_rank = 0
        self.pipeline_size = 1

    def __call__(self, x, cache=None):
        h = self.embed_tokens(x)
        if cache is None:
            cache = [None] * self.num_layers
        mask = dsv32.create_attention_mask(
            h, cache[0][0] if cache[0] else None, return_array=True)
        shared_topk = None
        for i in range(self.num_layers):
            layer = self.layers[self.start_idx + i]
            h, topk = layer(h, mask, cache[i], shared_topk)
            if layer.is_full:
                shared_topk = topk     # propagate to subsequent shared layers
            # Incremental eval so the lazy graph doesn't hold ALL 78 layers'
            # weights at once — keeps the working set ~1 layer, lets mmap page
            # out used experts. Critical for running a >RAM model on 128GB.
            if GLM_STREAM_EVAL:
                mx.eval(h)
                if shared_topk is not None:
                    mx.eval(shared_topk)
        return self.norm(h)


class Model(dsv32.Model):
    def __init__(self, config: ModelArgs):
        nn.Module.__init__(self)
        self.args = config
        self.model_type = config.model_type
        self.model = GlmDsaModel(config)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

    def make_cache(self):
        # Shared DSA layers never run their indexer (the indexer call + the
        # mx.depends are both guarded by is_full), so the base make_cache's second
        # KVCache stays unpopulated (keys=None) and generate.py's per-prompt
        # `mx.eval([c.state for c in cache])` crashes ('NoneType' has no 'shape').
        # Give shared layers ONLY the kv cache: generation is unchanged (they never
        # touch cache[1]) and every cache now has a valid .state/from_state -> the
        # prompt-cache TTFT speedup works (set PROMPT_CACHE / --prompt-cache-size).
        from mlx_lm.models.cache import CacheList, KVCache
        caches = []
        for layer in self.model.layers:
            full = getattr(layer, "is_full", True) and getattr(
                getattr(layer, "self_attn", None), "indexer", None) is not None
            caches.append(CacheList(KVCache(), KVCache()) if full
                          else CacheList(KVCache()))
        return caches
