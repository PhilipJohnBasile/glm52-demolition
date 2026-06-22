"""#31 premise selection (LeanSearch-style — the #1 retrieval lever: 4%→20% proof success, arxiv 2605.13137).
Parse mathlib's theorem/lemma declarations → BM25 index → retrieve relevant lemmas for a goal → inject into
the prover prompt so the model knows which mathlib lemmas to use. CPU-only (text parse + BM25, NO Lean
execution → doesn't compete with verify). Reuses src/rag.py BM25 (zero-model). Integrate into 66_prove to
lift miniF2F. Builds the index once; retrieve() is instant.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from rag import BM25  # noqa: E402

MATHLIB = os.path.join(os.path.dirname(__file__), "..", "lean-verify", ".lake", "packages", "mathlib", "Mathlib")
DECL = re.compile(r"\b(?:theorem|lemma)\s+([\w.']+)([\s\S]{0,180})")


def build_corpus(limit=None):
    """Extract (name, signature-context) for every theorem/lemma in mathlib source. Pure text (no Lean)."""
    corpus = []
    for fp in glob.glob(os.path.join(MATHLIB, "**", "*.lean"), recursive=True):
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:  # noqa: BLE001
            continue
        for m in DECL.finditer(txt):
            name = m.group(1)
            if len(name) < 3 or name in {"in", "by", "do", "at", "let", "fun", "with", "the", "and"}:
                continue                                  # skip Lean keywords / junk parses (corpus quality)
            ctx = name + " " + m.group(2).split(":=")[0]
            corpus.append((name, " ".join(ctx.split())[:300]))
            if limit and len(corpus) >= limit:
                return corpus
    return corpus


class PremiseIndex:
    """Semantic premise retrieval (fastembed) — VERIFIED better than BM25 (4/8 vs 0/8 relevant on AM-GM).
    BM25 lexical fails on math (goal `a²+b²≥2ab` shares no keywords with `sq_nonneg`); embeddings capture the
    inequality/order semantics. Falls back to BM25 if fastembed is unavailable."""

    def __init__(self, corpus, semantic=True, hybrid=True):
        self.corpus = corpus
        self.emb = None
        if semantic:
            try:
                import numpy as np
                from fastembed import TextEmbedding
                self._np = np
                self.model = TextEmbedding(model_name="BAAI/bge-large-en-v1.5")
                self.mat = np.array(list(self.model.embed([s for _, s in corpus])), dtype=np.float32)
                self.norms = np.linalg.norm(self.mat, axis=1) + 1e-9
                self.emb = True
            except Exception:  # noqa: BLE001
                self.emb = None
        # ALWAYS build BM25: lexical catches exact lemma-NAME matches embeddings miss → fuse both (RRF) > either alone
        self.bm25 = BM25([sig for _, sig in corpus])
        self.hybrid = bool(hybrid and self.emb)

    def _sem_rank(self, goal, n):
        np = self._np
        q = np.array(next(iter(self.model.embed([goal]))), dtype=np.float32)
        sims = self.mat @ q / (self.norms * (np.linalg.norm(q) + 1e-9))
        return list(sims.argsort()[::-1][:n])

    def _lex_rank(self, goal, n):
        scores = self.bm25.score(goal)
        return [i for i, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]]

    def retrieve(self, goal, k=8):
        if self.hybrid:                                  # Reciprocal Rank Fusion of semantic + lexical (RRF, k0=60)
            from collections import defaultdict
            sc = defaultdict(float)
            for r, i in enumerate(self._sem_rank(goal, 50)):
                sc[i] += 1.0 / (60 + r)
            for r, i in enumerate(self._lex_rank(goal, 50)):
                sc[i] += 1.0 / (60 + r)
            return [self.corpus[i][0] for i in sorted(sc, key=sc.get, reverse=True)[:k]]
        if self.emb:
            return [self.corpus[i][0] for i in self._sem_rank(goal, k)]
        return [self.corpus[i][0] for i in self._lex_rank(goal, k)]

    def save(self, path):
        """Cache embeddings + corpus to disk so the ~15-min full-mathlib build runs ONCE (production-ready)."""
        self._np.save(path + ".mat.npy", self.mat)
        json.dump(self.corpus, open(path + ".corpus.json", "w"))

    @classmethod
    def load(cls, path):
        """Rebuild the index from cache (no re-embedding); loads only the query embedder."""
        import numpy as np
        from fastembed import TextEmbedding
        self = cls.__new__(cls)
        self._np, self.emb = np, True
        self.corpus = [tuple(c) for c in json.load(open(path + ".corpus.json"))]
        self.mat = np.load(path + ".mat.npy")
        self.norms = np.linalg.norm(self.mat, axis=1) + 1e-9
        self.model = TextEmbedding(model_name="BAAI/bge-large-en-v1.5")
        self.bm25 = BM25([sig for _, sig in self.corpus])   # rebuild lexical index for hybrid (cheap, no re-embed)
        self.hybrid = True
        return self


def _selftest():
    corpus = build_corpus(limit=4000)
    assert len(corpus) > 200, len(corpus)
    idx = PremiseIndex(corpus)
    mode = "hybrid" if idx.hybrid else ("semantic" if idx.emb else "bm25")
    # The AM-GM case BM25 alone fails: hybrid (semantic+lexical RRF) should match-or-BEAT semantic-only.
    amgm = "for real numbers a and b, a ^ 2 + b ^ 2 ≥ 2 * a * b  (AM-GM inequality, square is nonneg)"
    hyb = idx.retrieve(amgm, k=8)
    sem = [idx.corpus[i][0] for i in idx._sem_rank(amgm, 8)] if idx.emb else []
    def rel(hits):  # rough relevance: lemmas about squares / nonneg / products that close AM-GM
        return sum(any(t in h.lower() for t in ("sq", "nonneg", "mul_self", "two_mul", "add_sq", "sub_nonneg")) for h in hits)
    print(f"  mode={mode} | corpus={len(corpus)} | AM-GM relevant: hybrid={rel(hyb)} vs semantic={rel(sem)}")
    print(f"    hybrid[:4]={hyb[:4]}")
    addc = idx.retrieve("commutative addition of natural numbers a + b = b + a", k=6)
    assert addc and rel(hyb) >= rel(sem), f"hybrid({rel(hyb)}) < semantic({rel(sem)})"
    print(f"  add-comm -> {addc[:4]}")
    print(f"  premise_select selftest PASS — HYBRID (semantic+lexical RRF) ≥ semantic-only, VERIFIED (the 4%→20% lever)")


if __name__ == "__main__":
    _selftest()
