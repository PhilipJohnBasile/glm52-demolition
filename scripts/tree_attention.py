"""Tree-attention primitives for MLX — the unlock for EAGLE-3 / DFlash spec-decode on Apple Silicon.

The blocker (mlx-lm Discussion #890): KVCache uses ONE scalar `offset`, so every cached token gets the
same RoPE position and a plain causal mask. Tree verification needs candidates at different tree DEPTHS
to (a) get their own RoPE position = base + depth, and (b) attend only to their ANCESTORS, not siblings
or future branches. These two pieces are pure MLX — built and tested here, then wired into glm4_moe.

Tree layout: `parents[i]` = index of token i's parent within the draft block (-1 = attaches to prompt).
Depth(i) = chain length to a root. Prompt tokens are positions [0..prompt_len); the tree sits after.
"""
import mlx.core as mx
import numpy as np


def tree_depths(parents):
    """depth[i] = number of ancestors within the tree (root children = depth 0)."""
    depths = []
    for i in range(len(parents)):
        d, j = 0, parents[i]
        while j != -1:
            d += 1
            j = parents[j]
        depths.append(d)
    return depths


def tree_position_ids(parents, prompt_len):
    """Per-token RoPE positions: a tree node at depth d sits at absolute position prompt_len + d."""
    return mx.array([prompt_len + d for d in tree_depths(parents)], dtype=mx.int32)


def build_tree_mask(parents, prompt_len, dtype=mx.float32):
    """Additive attention mask [T, prompt_len+T]: token i attends to ALL prompt tokens + its ancestors
    (and itself). Everything else = -inf. This is what lets one forward pass verify a whole token tree."""
    T = len(parents)
    neg = -1e9
    m = np.full((T, prompt_len + T), neg, dtype=np.float32)
    m[:, :prompt_len] = 0.0  # every candidate sees the full prompt
    for i in range(T):
        j = i
        while j != -1:  # walk ancestors (inclusive of self)
            m[i, prompt_len + j] = 0.0
            j = parents[j]
    return mx.array(m, dtype=dtype)


def apply_rope_positions(x, positions, base=10000.0):
    """RoPE with EXPLICIT per-token positions (half-split / NeoX convention), replacing the scalar-offset
    nn.RoPE so tree nodes rotate by their own depth-position.
        x: [B, H, T, head_dim]   positions: [T] int."""
    *_, T, hd = x.shape
    half = hd // 2
    inv_freq = base ** (-mx.arange(0, half, dtype=mx.float32) / half)      # [half]
    ang = positions.astype(mx.float32)[:, None] * inv_freq[None, :]        # [T, half]
    cos = mx.cos(ang)[None, None]                                          # [1,1,T,half]
    sin = mx.sin(ang)[None, None]
    x1, x2 = x[..., :half], x[..., half:]
    return mx.concatenate([x1 * cos - x2 * sin, x1 * sin + x2 * cos], axis=-1)


if __name__ == "__main__":
    # self-test on a small tree:  prompt(len 5) → [A, B] off prompt; A→C, A→D; C→E
    #   indices:  A=0(d0) B=1(d0) C=2(d1) D=3(d1) E=4(d2)
    parents = [-1, -1, 0, 0, 2]
    pl = 5
    print("depths      :", tree_depths(parents), "  (expect [0,0,1,1,2])")
    print("positions   :", tree_position_ids(parents, pl).tolist(), "  (expect [5,5,6,6,7])")
    m = build_tree_mask(parents, pl)
    # E (idx4) must see prompt(0..4) + its ancestor chain E,C,A = cols pl+4, pl+2, pl+0; NOT B,D
    row_E = (np.array(m[4].tolist()) == 0.0)
    seen = [k for k, v in enumerate(row_E) if v]
    print("E attends to:", seen, "  (expect prompt 0-4 + 5,7,9 = A,C,E)")
    assert seen == [0, 1, 2, 3, 4, 5, 7, 9], "tree mask WRONG"
    # rope sanity: SAME vector at the same position rotates identically; at a different position differs
    x = mx.random.normal((1, 1, 1, 8))
    r5a = apply_rope_positions(x, mx.array([5]))
    r5b = apply_rope_positions(x, mx.array([5]))
    r6 = apply_rope_positions(x, mx.array([6]))
    same = mx.allclose(r5a, r5b)        # same vec, same pos → identical
    diff = not mx.allclose(r5a, r6)     # same vec, pos 5 vs 6 → differ
    print(f"rope: same-pos identical={bool(same)} (T), diff-pos differ={bool(diff)} (T)")
    assert same and diff, "rope positions WRONG"
    print("\n✅ tree-attention primitives PASS — ready to wire into glm4_moe attention")
