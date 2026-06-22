"""ANE-offloaded embeddings — run sentence embeddings on the 16-core Apple Neural
Engine, freeing the GPU (busy decoding) and the CPU (busy verifying). Three routes:

  1. Apple NLContextualEmbedding  (PRIMARY, works today) — Apple's own sentence model,
     ANE-resident, assets already on-device, NO coremltools conversion. This is what
     backend == "ane" uses. 768-dim, ~9.5 ms/embed on its own silicon.
  2. CoreML .mlpackage             (for custom models, e.g. vision #79) — convert via
     coremltools. A standard BERT *text* encoder currently hits a coremltools aten::Int
     converter bug (reproduced on torch 2.7 AND 2.12), so for TEXT we use route 1.
  3. torch CPU fallback            — if neither ANE route is available (non-Apple, etc.).

    from ane_embed import ANEEmbedder
    emb = ANEEmbedder()                  # backend == "ane" on Apple Silicon
    vecs = emb.embed(["hello", "world"]) # (N, dim) L2-normalized, on the Neural Engine
    print(emb.backend)                   # "ane" | "torch-fallback"

Install for the ANE route:  uv pip install --python .venv pyobjc-framework-NaturalLanguage
"""
import os
import numpy as np

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # torch fallback only
DEFAULT_PKG = os.path.join(os.path.dirname(__file__), "..", "models", "ane_embed.mlpackage")
SEQ = 128


class ANEEmbedder:
    """Embed on the ANE via Apple's NLContextualEmbedding; torch CPU fallback."""

    def __init__(self, model_id=DEFAULT_MODEL):
        self.backend = "torch-fallback"
        self._nl = None
        try:  # Route 1: Apple NLContextualEmbedding — ANE-native, no converter
            import NaturalLanguage as nl
            self._lang = nl.NLLanguageEnglish
            e = nl.NLContextualEmbedding.contextualEmbeddingWithLanguage_(self._lang)
            if e is not None and e.hasAvailableAssets():
                e.loadSentenceEmbeddingWithError_(None)
                if e.isLoaded():
                    self._nl = e
                    self.dim = int(e.sentenceVectorDimension())
                    self.backend = "ane"
        except Exception as ex:  # noqa: BLE001
            print(f"  [ane_embed] Apple NL unavailable ({str(ex)[:50]}); torch fallback")
        if self.backend != "ane":  # Route 3: torch CPU fallback
            from transformers import AutoModel, AutoTokenizer
            self.tok = AutoTokenizer.from_pretrained(model_id)
            self._torch = AutoModel.from_pretrained(model_id).eval()
            self.dim = int(self._torch.config.hidden_size)

    def embed(self, texts):
        texts = list(texts)
        if self.backend == "ane":
            rows = []
            for s in texts:
                r = self._nl.sentenceEmbeddingVectorForString_language_error_(s, self._lang, None)
                v = r[0] if isinstance(r, tuple) else r
                rows.append(np.zeros(self.dim, np.float32) if v is None
                            else np.array(v, dtype=np.float32))
            vecs = np.vstack(rows)
        else:
            import torch
            enc = self.tok(texts, return_tensors="np", padding="max_length",
                           max_length=SEQ, truncation=True)
            with torch.no_grad():
                h = self._torch(input_ids=torch.tensor(enc["input_ids"]),
                                attention_mask=torch.tensor(enc["attention_mask"])
                                ).last_hidden_state
                w = torch.tensor(enc["attention_mask"]).unsqueeze(-1).float()
                vecs = ((h * w).sum(1) / w.sum(1).clamp(min=1e-9)).numpy()
        return vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)


def _pool_module(hf_model):
    """Wrap an HF encoder to return the masked mean-pooled embedding (one vector/input)."""
    import torch

    class Enc(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, ids, mask):
            h = self.m(input_ids=ids, attention_mask=mask).last_hidden_state
            w = mask.unsqueeze(-1).to(h.dtype)
            return (h * w).sum(1) / w.sum(1).clamp(min=1e-9)

    return Enc(hf_model).eval()


def build(model_id=DEFAULT_MODEL, out=DEFAULT_PKG, seq=SEQ):
    """[For #79 / custom models] Convert an HF encoder to a CoreML .mlpackage on CPU+ANE.

    NOTE: a standard BERT *text* encoder currently trips a coremltools aten::Int converter
    bug on torch 2.7 AND 2.12 — so for TEXT, prefer the NLContextualEmbedding route in
    ANEEmbedder. Kept for vision (#79), where a conversion-friendly model is chosen."""
    import coremltools as ct
    import torch
    from transformers import AutoModel, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id)
    enc = _pool_module(AutoModel.from_pretrained(model_id))
    ex = tok("warm up the trace", return_tensors="pt", padding="max_length",
             max_length=seq, truncation=True)
    shapes = [ct.TensorType(name="ids", shape=ex["input_ids"].shape, dtype=int),
              ct.TensorType(name="mask", shape=ex["attention_mask"].shape, dtype=int)]
    try:
        prog = torch.export.export(enc, (ex["input_ids"], ex["attention_mask"]))
        ml = ct.convert(prog, inputs=shapes, compute_units=ct.ComputeUnit.CPU_AND_NE,
                        minimum_deployment_target=ct.target.macOS15)
    except Exception as e:  # noqa: BLE001
        print(f"  [build] torch.export failed ({str(e)[:60]}); trying jit.trace")
        traced = torch.jit.trace(enc, (ex["input_ids"], ex["attention_mask"]))
        ml = ct.convert(traced, inputs=shapes, compute_units=ct.ComputeUnit.CPU_AND_NE,
                        minimum_deployment_target=ct.target.macOS15)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ml.save(out)
    print(f"  built {out}  (compute=CPU_AND_NE, seq={seq})")
    return out


if __name__ == "__main__":
    import time
    e = ANEEmbedder()
    v = e.embed(["the local agentic coder", "verify everything", "the local agentic coder"])
    t = time.time(); [e.embed(["warm cache line for the agentic coder"]) for _ in range(50)]
    print(f"  backend={e.backend}  dim={v.shape[1]}  same-text cos={float(v[0] @ v[2]):.3f}  "
          f"diff cos={float(v[0] @ v[1]):.3f}  {(time.time() - t) / 50 * 1000:.2f} ms/embed")
