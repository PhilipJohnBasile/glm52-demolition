"""reap-mlx adapter for GLM-5.2 (architecture: glm_moe_dsa).

GLM-5.2 reuses MLX-LM's DeepSeek-V3.2 implementation (`deepseek_v32.py`) via the
`glm_moe_dsa` module, which subclasses `deepseek_v32.Model`. Its MoE block
(`DeepseekV32MoE`) exposes `layer.mlp.switch_mlp` (a `SwitchGLU`) plus a
`DeepseekV32MoE.gate` (`MoEGate`) and optional `shared_experts`.

reap-mlx's stock `Qwen3MoeModelAdapter` ALMOST works here because it keys off
`layer.mlp.switch_mlp`. The gaps this adapter closes:

  1. Expert count lives in config as `n_routed_experts` (not `num_experts`) and
     is NOT exposed as a live `moe.num_experts` attribute. -> override lookup.
  2. The post-prune config must rewrite `n_routed_experts`.
  3. GLM-5.2 uses GROUP-LIMITED routing (`n_group`, `topk_group`,
     `topk_method="noaux_tc"`). Experts are partitioned into `n_group` groups and
     routing selects `topk_group` groups first. Pruning routed experts changes
     group membership/sizes, so a naive expert drop can break the grouped gate.
     This adapter REFUSES to prune unless groups stay consistent (see
     `validate_group_safety`), and exposes the knobs to do group-aware pruning.

Install: place on PYTHONPATH and import `register()` before running reap's
entrypoint, e.g. `python -c "import glm52_reap_adapter as a; a.register()"` in the
same process, or use scripts/03_prune.sh which patches reap in-process.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from reap import model_adapters as _ma
from reap.model_adapters import (
    MoeLayerConfig,
    Qwen3MoeModelAdapter,
    _live_or_config_value,
    _positive_int,
)

GLM52_MODEL_TYPES = {"glm_moe_dsa"}
# deepseek_v32 shares the same MoE layout, so the adapter is valid for it too.
DEEPSEEK_MODEL_TYPES = {"deepseek_v32", "deepseek_v3"}


class Glm52MoeModelAdapter(Qwen3MoeModelAdapter):
    """Adapter for GLM-5.2 / DeepSeek-V3.2-style grouped MoE in MLX-LM."""

    adapter_name = "glm52_moe_dsa"

    def get_layer_config(
        self,
        layer: Any,
        config: Mapping[str, Any] | None = None,
    ) -> MoeLayerConfig:
        moe = self.get_moe(layer)

        # DeepSeek/GLM store the routed-expert count under `n_routed_experts`.
        num_experts = _positive_int(
            _live_or_config_value(
                moe,
                ("n_routed_experts", "num_experts"),
                config,
                ("n_routed_experts", "num_experts"),
            ),
            "n_routed_experts",
        )
        top_k = _positive_int(
            _live_or_config_value(
                moe,
                ("num_experts_per_tok", "top_k"),
                config,
                ("num_experts_per_tok", "top_k"),
            ),
            "num_experts_per_tok",
        )
        norm_topk_prob = bool(
            _live_or_config_value(
                moe,
                ("norm_topk_prob",),
                config,
                ("norm_topk_prob",),
                default=True,
            )
        )

        return MoeLayerConfig(
            num_experts=num_experts,
            top_k=top_k,
            norm_topk_prob=norm_topk_prob,
            adapter_name=self.adapter_name,
        )


def validate_group_safety(
    config: Mapping[str, Any],
    *,
    keep_experts: int,
) -> None:
    """Fail loudly unless the kept-expert count keeps grouped routing valid.

    GLM-5.2 partitions `n_routed_experts` into `n_group` groups. For grouped
    top-k routing to remain well-defined after pruning:
      * `keep_experts` must be divisible by `n_group` (equal-size groups), and
      * each surviving group must still hold >= (top_k // topk_group) experts.
    Otherwise you must also shrink `n_group`/`topk_group` and re-derive routing.
    """
    n_group = int(config.get("n_group", 1) or 1)
    topk_group = int(config.get("topk_group", 1) or 1)
    top_k = int(config.get("num_experts_per_tok", 1) or 1)

    if n_group <= 1:
        return  # ungrouped routing -> arbitrary expert drops are safe.

    if keep_experts % n_group != 0:
        raise ValueError(
            f"keep_experts={keep_experts} is not divisible by n_group={n_group}. "
            "Grouped routing needs equal-size groups. Choose a compression ratio "
            "whose surviving expert count is a multiple of n_group, or reduce "
            "n_group/topk_group and re-balance."
        )
    per_group = keep_experts // n_group
    need_per_group = -(-top_k // max(topk_group, 1))  # ceil
    if per_group < need_per_group:
        raise ValueError(
            f"After pruning, each of {n_group} groups holds {per_group} experts, "
            f"but routing needs >= {need_per_group} per selected group "
            f"(top_k={top_k}, topk_group={topk_group}). Prune less, or lower top_k."
        )


def update_glm52_moe_config(
    config: MutableMapping[str, Any],
    *,
    num_experts: int,
    top_k: int,
) -> MutableMapping[str, Any]:
    """Rewrite a GLM-5.2 config dict after expert pruning (group-aware)."""
    num_experts = _positive_int(num_experts, "n_routed_experts")
    validate_group_safety(config, keep_experts=num_experts)

    top_k = min(_positive_int(top_k, "num_experts_per_tok"), num_experts)
    config["n_routed_experts"] = num_experts
    config["num_experts_per_tok"] = top_k
    # Keep grouped-routing knobs internally consistent.
    n_group = int(config.get("n_group", 1) or 1)
    if n_group > 1:
        config["topk_group"] = min(int(config.get("topk_group", 1) or 1), n_group)
    return config


def register() -> None:
    """Monkeypatch reap-mlx so its inference picks this adapter for GLM-5.2."""
    _orig_infer = _ma.infer_model_adapter

    def infer_model_adapter(model=None, config=None):
        model_type = (config or {}).get("model_type")
        if model_type in GLM52_MODEL_TYPES or model_type in DEEPSEEK_MODEL_TYPES:
            return Glm52MoeModelAdapter()
        return _orig_infer(model=model, config=config)

    _ma.infer_model_adapter = infer_model_adapter
    # Also expose the config updater where reap looks up per-arch updaters.
    _ma.update_glm52_moe_config = update_glm52_moe_config
    _ma.Glm52MoeModelAdapter = Glm52MoeModelAdapter
