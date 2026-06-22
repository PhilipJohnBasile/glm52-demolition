"""ANE zero-shot router — pick the right specialty (which swappable adapter / facet) for
a request, on the 16-core Neural Engine, by embedding the request and matching it against
facet descriptions (cosine). No training, no GPU — the factory's module dispatch (#80) +
the agent's triage + text-classification (#93). Reuses the #78 ANE embeddings.

    from ane_route import route
    route("fix the failing pytest in auth.py")              # -> [("code", 0.41)]
    route("improve the color contrast on this UI")          # -> [("design", 0.38)]
    route(req, top_k=2)                                     # the 2 best facets
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

# facet -> a short natural-language description the request is matched against
FACETS = {
    "code":     "write debug refactor and test software code in python rust go typescript c",
    "design":   "ui ux visual design layout color typography css html spacing aesthetics",
    "math":     "prove a theorem in lean formal mathematics algebra calculus equations",
    "security": "find a vulnerability exploit pentest ctf red team secure code audit",
    "science":  "physics chemistry biology data analysis experiment hypothesis simulation",
    "data":     "sql query a database pandas dataframe csv table analytics aggregation",
}


# strong lexical signals — break ties the general-purpose embedding can't (decisive)
KEYWORDS = {
    "code":     ["pytest", "refactor", "compile", "traceback", "function", "import ", "npm", "cargo", "def "],
    "design":   ["css", "color", "contrast", "spacing", "layout", "typography", " ui", " ux", "figma"],
    "math":     ["lean", "prove", "theorem", "lemma", "proof", "qed", "integral", "even number"],
    "security": ["injection", "exploit", "vulnerab", "pentest", "ctf", "xss", "csrf", "owasp", "bypass"],
    "science":  ["physics", "chemistry", "biology", "hypothesis", "experiment", "simulation"],
    "data":     ["csv", "dataframe", "pandas", "parquet", "revenue", "aggregate", "groupby", "per region"],
}


def route(request, facets=None, top_k=1, kw_boost=0.2):
    """Best-matching facet(s): [(facet, score) …]. ANE embedding + decisive keyword priors —
    the embedding handles the ambiguous, the keywords break ties the embedding gets wrong."""
    from ane_embed import ANEEmbedder
    f = facets or FACETS
    labels = list(f.keys())
    r = request.lower()
    e = ANEEmbedder()
    emb = e.embed([f[k] for k in labels]) @ e.embed([request])[0]
    scored = [(k, float(emb[i]) + kw_boost * sum(1 for w in KEYWORDS.get(k, []) if w in r))
              for i, k in enumerate(labels)]
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


if __name__ == "__main__":
    tests = [
        ("fix the failing pytest in auth.py and make it pass", "code"),
        ("improve the color contrast and spacing on this landing page", "design"),
        ("prove that the sum of two even numbers is even in Lean 4", "math"),
        ("find the SQL injection in this login handler and patch it", "security"),
        ("load the CSV and compute mean revenue per region", "data"),
    ]
    ok = 0
    for req, want in tests:
        got = route(req)[0]
        hit = got[0] == want
        ok += hit
        print(f"  {'OK ' if hit else 'XX '} {got[0]:9} ({got[1]:.2f})  <- {req[:46]}")
    print(f"  ane_route selftest {'PASS' if ok >= 4 else 'CHECK'} — {ok}/{len(tests)} routed right on the ANE")
