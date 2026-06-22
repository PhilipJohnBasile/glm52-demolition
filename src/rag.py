"""Local code RAG for agentic coding — index your repos, retrieve the few
relevant chunks for a query. Smarter (right files), faster (small focused
context vs whole-repo dumps), more agile (no context bloat).

Default retriever is BM25 (pure Python, zero model, strong on code symbols).
If a local embedding backend is available it adds semantic recall via a hybrid
score. Designed to be called as an agent TOOL (`search_code`), so the model
decides when to retrieve.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict

# language-aware "start of definition" patterns -> chunk on these boundaries.
DEF_PATTERNS = {
    "python": re.compile(r"^\s*(?:async\s+)?(?:def|class)\s"),
    "javascript": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s|class\s|const\s+\w+\s*=\s*(?:async\s*)?\()"),
    "typescript": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s|class\s|interface\s|type\s|const\s+\w+\s*=\s*(?:async\s*)?\()"),
    "rust": re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?(?:fn|struct|impl|trait|enum)\s"),
    "go": re.compile(r"^\s*(?:func|type)\s"),
}
EXT_LANG = {".py": "python", ".ts": "typescript", ".tsx": "typescript",
            ".js": "javascript", ".jsx": "javascript", ".rs": "rust",
            ".go": "go", ".html": "html", ".htm": "html", ".css": "css",
            ".scss": "css", ".md": "markdown"}
SKIP_DIRS = ("/.git", "node_modules", "/target", "/dist", "/build", "/.venv",
             "/__pycache__", "/.next", "/vendor")
MAX_CHUNK_LINES = 80
WINDOW_OVERLAP = 10

# English-only: drop non-English natural-language chunks (e.g. translated docs).
# Code is ASCII so it always passes; CJK/Cyrillic/etc. prose is filtered out.
_FOREIGN = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x3040, 0x30FF),
            (0xAC00, 0xD7AF), (0x0400, 0x04FF), (0x0600, 0x06FF), (0x0590, 0x05FF)]


def _is_english(text, max_foreign=0.02):
    foreign = letters = 0
    for c in text:
        if c.isalpha():
            letters += 1
            o = ord(c)
            if any(lo <= o <= hi for lo, hi in _FOREIGN):
                foreign += 1
    return letters == 0 or foreign / letters <= max_foreign


def _split_ident(tok):
    # snake_case + camelCase -> subtokens, so "parse user" hits parseUser.
    parts = re.split(r"[^A-Za-z0-9]+", tok)
    out = []
    for p in parts:
        if not p:
            continue
        out += [s.lower() for s in re.findall(
            r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", p)] or [p.lower()]
    return out


def tokenize(text):
    toks = []
    for raw in re.findall(r"[A-Za-z0-9_]+", text):
        toks.append(raw.lower())
        toks += _split_ident(raw)
    return toks


def chunk_file(path, lang):
    try:
        lines = open(path, errors="ignore").read().splitlines()
    except Exception:  # noqa: BLE001
        return []
    pat = DEF_PATTERNS.get(lang)
    chunks, buf, start, symbol = [], [], 0, ""
    def flush(end):
        if buf and any(l.strip() for l in buf):
            chunks.append({"file": path, "start_line": start + 1,
                           "end_line": end, "symbol": symbol,
                           "lang": lang, "text": "\n".join(buf)})
    if pat:
        for i, ln in enumerate(lines):
            if pat.match(ln) and buf:
                flush(i)
                buf, start = [], i
                symbol = ln.strip()[:80]
            buf.append(ln)
            if len(buf) >= MAX_CHUNK_LINES:    # cap huge defs
                flush(i + 1)
                start = i + 1 - WINDOW_OVERLAP
                buf = lines[start:i + 1]
        flush(len(lines))
    else:                                       # html/css/md -> sliding window
        i = 0
        while i < len(lines):
            seg = lines[i:i + MAX_CHUNK_LINES]
            start, symbol = i, os.path.basename(path)
            buf = seg
            flush(min(i + MAX_CHUNK_LINES, len(lines)))
            i += MAX_CHUNK_LINES - WINDOW_OVERLAP
    return chunks


def index_paths(paths, langs=None):
    chunks = []
    for base in paths:
        if os.path.isfile(base):
            walk = [(os.path.dirname(base), [], [os.path.basename(base)])]
        else:
            walk = os.walk(base)
        for root, _, files in walk:
            if any(s in root for s in SKIP_DIRS):
                continue
            for fn in files:
                lang = EXT_LANG.get(os.path.splitext(fn)[1].lower())
                if not lang or (langs and lang not in langs):
                    continue
                for c in chunk_file(os.path.join(root, fn), lang):
                    if _is_english(c["text"]):     # drop translated/foreign docs
                        chunks.append(c)
    return chunks


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = [tokenize(d) for d in docs]
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(self.N, 1)
        self.df = Counter()
        self.tf = []
        for d in self.docs:
            c = Counter(d)
            self.tf.append(c)
            for term in c:
                self.df[term] += 1
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5))
                    for t, n in self.df.items()}

    def score(self, query):
        q = tokenize(query)
        scores = defaultdict(float)
        for term in q:
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i, c in enumerate(self.tf):
                f = c.get(term)
                if not f:
                    continue
                dl = len(self.docs[i])
                denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf * (f * (self.k1 + 1)) / denom
        return scores


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.bm25 = BM25([c["text"] + " " + c["symbol"] for c in chunks])
        self.emb = None  # optional; see load_embeddings()

    def search(self, query, k=6):
        bm = self.bm25.score(query)
        if self.emb is not None:
            import numpy as np
            qv = self.emb["model"](query)
            sims = self.emb["mat"] @ qv / (
                (np.linalg.norm(self.emb["mat"], axis=1) * np.linalg.norm(qv)) + 1e-9)
            # hybrid: normalize BOTH to [0,1] then sum (was: raw cosine [-1,1] added to [0,1] BM25 → scale mismatch)
            if bm:
                mx = max(bm.values()) or 1.0
                for i in bm:
                    bm[i] = bm[i] / mx
            smin, smax = float(sims.min()), float(sims.max())
            sims = (sims - smin) / (smax - smin + 1e-9)
            for i in range(len(self.chunks)):
                bm[i] = bm.get(i, 0.0) + float(sims[i])
        ranked = sorted(bm.items(), key=lambda x: x[1], reverse=True)[:k]
        out = []
        for i, s in ranked:
            c = self.chunks[i]
            out.append({"file": c["file"], "lines": f"{c['start_line']}-{c['end_line']}",
                        "symbol": c["symbol"], "lang": c["lang"],
                        "score": round(float(s), 4), "text": c["text"]})
        return out

    def enable_embeddings(self, cache_dir=None, model_name="BAAI/bge-large-en-v1.5"):
        """Best-effort: load the semantic backend so search() becomes hybrid
        (BM25 + embeddings) — the fallback that catches queries CallSieve's
        keyword/structural ranking misses. Returns True if enabled, False if no
        backend is installed (then retrieval stays BM25-only and still works)."""
        self.emb = load_embeddings(self.chunks, cache_dir, model_name)
        return self.emb is not None


def save_index(chunks, path):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "chunks.jsonl"), "w") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")


def load_index(path):
    cf = os.path.join(path, "chunks.jsonl")
    return [json.loads(l) for l in open(cf)]


def load_embeddings(chunks, cache_dir=None, model_name="BAAI/bge-large-en-v1.5"):
    """Semantic backend for the hybrid fallback. MLX-FIRST: prefers mlx-embeddings (Apple-Silicon
    native, GPU); falls back to fastembed (ONNX, local, no torch); else None (BM25-only still
    works). Caches the chunk matrix to {cache_dir}/emb-{n}.npy so it's built once."""
    import numpy as np
    n = len(chunks)
    cache = os.path.join(cache_dir, f"emb-{n}.npy") if cache_dir else None
    embed_one = None

    # 1) MLX-native (preferred on this machine)
    try:
        import mlx.core as mx
        from mlx_embeddings import load as _mlx_load
        _m, _tok = _mlx_load(model_name)

        def embed_one(text):                                  # noqa: E306
            out = _m(_tok.encode(text[:2000]))
            vec = getattr(out, "text_embeds", out)
            return np.asarray(mx.array(vec).astype(mx.float32).tolist(), np.float32).reshape(-1)

        embed_one("warmup")                                   # prove the API before committing
    except Exception:  # noqa: BLE001
        embed_one = None

    # 2) fastembed (ONNX) fallback
    if embed_one is None:
        try:
            from fastembed import TextEmbedding
            emb = TextEmbedding(model_name=model_name)

            def embed_one(text):                              # noqa: E306,F811
                return np.asarray(next(iter(emb.embed([text[:2000]]))), np.float32)
        except Exception:  # noqa: BLE001
            return None

    if cache and os.path.exists(cache):
        mat = np.load(cache)
        if mat.shape[0] == n:
            return {"model": embed_one, "mat": mat}
    texts = [((c.get("symbol", "") + " " + c.get("text", ""))[:2000]) for c in chunks]
    mat = np.asarray([embed_one(t) for t in texts], dtype=np.float32)
    if cache:
        try:
            np.save(cache, mat)
        except Exception:  # noqa: BLE001
            pass
    return {"model": embed_one, "mat": mat}


def _selftest():
    """GPU-free: code-aware tokenize + BM25 zero-model retrieval + Retriever.search (#6 CallSieve)."""
    toks = tokenize("def parseConfig(user_name): return userName")
    assert "parse" in toks and "config" in toks and "user" in toks and "name" in toks, toks
    bm = BM25(["def add(a, b): return a + b",
               "def parse_json(text): return json.loads(text)",
               "class HttpClient: pass"])
    sc = bm.score("parse json")
    assert sc and max(sc, key=sc.get) == 1, dict(sc)
    chunks = [
        {"text": "def add(a,b): return a+b", "symbol": "add", "file": "math.py",
         "start_line": 1, "end_line": 1, "lang": "python"},
        {"text": "def parse_json(t): return json.loads(t)", "symbol": "parse_json", "file": "io.py",
         "start_line": 5, "end_line": 6, "lang": "python"},
    ]
    hits = Retriever(chunks).search("parse json text", k=1)
    assert hits and hits[0]["symbol"] == "parse_json", hits
    print("  rag (CallSieve #6) selftest PASS — code-tokenize + BM25 zero-model retrieval + Retriever.search")


if __name__ == "__main__":
    _selftest()
