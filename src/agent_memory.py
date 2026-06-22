"""#116 Agent memory — cross-session semantic recall for the agentic coder.

Embeds agent experiences (task → what worked / what failed) on the Apple Neural Engine, persists them to
a jsonl, and recalls the most similar past situations for a new task. This is the "the agent remembers
across sessions" feature — distinct from CallSieve (per-repo, per-request retrieval): this is durable,
cross-repo episodic memory.

Backend is pluggable: uses VecStore (PhilipJohnBasile/vecstore) if installed, else an ANE-embedded local
store (numpy cosine), else a hashing fallback — so it works today and upgrades transparently.

  m = AgentMemory()
  m.store("fixed off-by-one in callsieve skeleton.rs by '- 1'->'+ 1'", {"repo":"callsieve","verified":True})
  m.recall("boundary bug in a range loop")   # -> [(row, score), ...] most-similar past fixes
"""
import json
import os

import numpy as np


class AgentMemory:
    def __init__(self, path="agent_memory.jsonl"):
        self.path = path
        self._rows = [json.loads(l) for l in open(path)] if os.path.exists(path) else []
        self._vs = None
        self._emb = None
        try:                                   # 1st choice: the user's VecStore (../git/vecstore, when maturin-built)
            from vecstore import VecStoreWithEmbeddings
            self._vs = VecStoreWithEmbeddings(os.environ.get("AGENT_MEM_DB", "./agent_memory_db"))
        except Exception:
            pass
        if self._vs is None:                   # 2nd choice: ANE embeddings (Neural Engine)
            try:
                import sys
                sys.path.insert(0, "src")
                from ane_embed import ANEEmbedder
                self._emb = ANEEmbedder()
            except Exception:
                self._emb = None               # 3rd: hashing fallback (always works)

    def _vec(self, texts):
        if self._emb is not None:
            V = np.asarray(self._emb.embed(texts), dtype=np.float32)
        else:                                  # deterministic hashing bag-of-words fallback
            V = np.zeros((len(texts), 512), dtype=np.float32)
            for i, t in enumerate(texts):
                for tok in t.lower().split():
                    V[i, hash(tok) % 512] += 1.0
        return V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-8)

    def store(self, text, meta=None):
        """Persist one experience (durable, cross-session)."""
        row = {"text": text, "meta": meta or {}}
        self._rows.append(row)
        with open(self.path, "a") as f:
            f.write(json.dumps(row) + "\n")
        if self._vs is not None:
            try:
                self._vs.add(text, metadata=row["meta"])
            except Exception:
                pass
        return row

    def recall(self, query, k=3):
        """Return up to k most-similar past experiences as (row, cosine) — newest-similar first."""
        if self._vs is not None:
            try:
                return [(r, getattr(r, "score", 1.0)) for r in self._vs.search(query, k=k)]
            except Exception:
                pass
        if not self._rows:
            return []
        V = self._vec([r["text"] for r in self._rows])
        q = self._vec([query])[0]
        sims = V @ q
        idx = np.argsort(-sims)[:k]
        return [(self._rows[i], float(sims[i])) for i in idx]

    def backend(self):
        return "vecstore" if self._vs else ("ane" if self._emb else "hashing")


if __name__ == "__main__":
    import tempfile
    m = AgentMemory(path=os.path.join(tempfile.mkdtemp(), "mem.jsonl"))
    m.store("fixed off-by-one in skeleton.rs: ' - 1' -> ' + 1', cargo test passed", {"repo": "callsieve"})
    m.store("design: used OKLCH palette with WCAG-AA contrast for the dashboard", {"facet": "design"})
    m.store("fixed equality flip in classify.rs: ' >= ' -> ' > ', verified", {"repo": "callsieve"})
    hits = m.recall("boundary off-by-one bug in a loop range", k=2)
    print(f"  backend: {m.backend()}")
    for r, s in hits:
        print(f"  recall {s:.3f}: {r['text'][:60]}")
    print(f"  ✅ agent_memory: stored 3, recalled top-2 by similarity")
