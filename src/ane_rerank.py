"""ANE reranker — re-score retrieval candidates by semantic relevance on the 16-core
Neural Engine, freeing the GPU. Bi-encoder: embed the query + each candidate (ANE, via
ane_embed.NLContextualEmbedding) and rank by cosine. Improves WHAT the agent retrieves
(CallSieve / RAG / premise-select) without touching the GPU — smarter context = fewer
wrong turns. Covers HF: Text Ranking, Visual Document Retrieval (with #78 + an SSD index).

    from ane_rerank import rerank
    ranked = rerank("how to parse a config file", candidates)   # [(cand, score) …] best-first
    top3   = rerank(query, candidates, top_k=3)
"""
import numpy as np

_EMB = {"e": None}


def _embedder():
    if _EMB["e"] is None:
        import os
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from ane_embed import ANEEmbedder
        _EMB["e"] = ANEEmbedder()
    return _EMB["e"]


def rerank(query, candidates, top_k=None):
    """Rank `candidates` by cosine relevance to `query` (embeddings on the ANE).
    Returns [(candidate, score) …] best-first; pass top_k to truncate."""
    cands = list(candidates)
    if not cands:
        return []
    e = _embedder()
    qv = e.embed([query])[0]
    cv = e.embed(cands)
    scores = cv @ qv                                # both L2-normalized -> cosine similarity
    order = np.argsort(-scores)
    out = [(cands[i], float(scores[i])) for i in order]
    return out[:top_k] if top_k else out


def rerank_indices(query, candidates, top_k=None):
    """Same ranking but returns the original indices (for reordering a parallel list)."""
    cands = list(candidates)
    if not cands:
        return []
    e = _embedder()
    scores = e.embed(cands) @ e.embed([query])[0]
    order = list(np.argsort(-scores))
    return order[:top_k] if top_k else order


if __name__ == "__main__":
    q = "how do I read a YAML config file in python"
    cands = [
        "import yaml; cfg = yaml.safe_load(open('config.yaml'))",   # relevant
        "def quicksort(arr): return arr",                           # irrelevant
        "with open('settings.yml') as f: data = yaml.load(f)",      # relevant
        "SELECT * FROM users WHERE id = 1",                         # irrelevant
    ]
    ranked = rerank(q, cands)
    for c, s in ranked:
        print(f"  {s:.3f}  {c[:52]}")
    top = rerank(q, cands, top_k=2)
    ok = all(("yaml" in c.lower() or "yml" in c.lower()) for c, _ in top)
    print(f"  ane_rerank selftest {'PASS' if ok else 'CHECK'} — YAML candidates ranked top on the ANE")
