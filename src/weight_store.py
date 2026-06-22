"""On-demand per-layer weight loader for streaming a >RAM model on 128GB.

The 381GB GLM-5.2 can't be mmap-resident on 128GB (forward OOMs at ~120GB). But
its routed experts are stored PRE-STACKED as `switch_mlp.{proj}.weight` — one
~5GB tensor per layer. So we can stream LAYER BY LAYER: load one layer's tensors
(~5GB) from the safetensors shards, use them, free them. Working set stays small.

WeightStore maps tensor-name -> shard (via model.safetensors.index.json) and loads
only the tensors for a requested layer, grouping shard reads so each shard is read
at most once per layer.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict

import mlx.core as mx


class WeightStore:
    def __init__(self, model_dir: str):
        self.dir = model_dir
        self.index = json.load(
            open(os.path.join(model_dir, "model.safetensors.index.json")))["weight_map"]
        # group keys by shard for batched reads
        self.by_shard = defaultdict(list)
        for k, shard in self.index.items():
            self.by_shard[shard].append(k)

    def keys_for(self, prefix: str):
        return [k for k in self.index if k.startswith(prefix)]

    def load_prefix(self, prefix: str) -> dict:
        """Load all tensors whose name starts with `prefix` (e.g. one layer),
        reading each needed shard once. Returns {name: mx.array} (still lazy)."""
        wanted = self.keys_for(prefix)
        shards = defaultdict(list)
        for k in wanted:
            shards[self.index[k]].append(k)
        out = {}
        for shard, keys in shards.items():
            data = mx.load(os.path.join(self.dir, shard))   # whole shard (mmap)
            for k in keys:
                out[k] = data[k]
        return out

    def layer_prefix(self, i: int) -> str:
        return f"model.layers.{i}."
