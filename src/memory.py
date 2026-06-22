"""② Compounding context — a persistent verified-solution cache + project memory.
Every task the engine solves correctly is banked here; new tasks retrieve the most
similar PAST VERIFIED solutions to seed the loop, so the model accumulates a private,
growing library of YOUR verified code. This is compounding CONTEXT to pair with the
flywheel's compounding WEIGHTS — a cloud model starts cold every session; this
remembers your repo, your patterns, your decisions.

  from memory import SolutionCache, ProjectMemory
  cache.store(task, lang, verified_solution)
  hint = cache.hint(new_task, lang)     # inject into the prompt to seed the loop
"""
import json
import os
import re
from collections import Counter


def _toks(s):
    return Counter(re.findall(r"[a-zA-Z_][a-zA-Z_0-9]{2,}", (s or "").lower()))


def _sim(a, b):                                   # cosine over token counts (embedding-ready)
    if not a or not b:
        return 0.0
    inter = sum((a & b).values())
    return inter / ((sum(v * v for v in a.values()) ** 0.5) * (sum(v * v for v in b.values()) ** 0.5) + 1e-9)


class _JsonlStore:
    def __init__(self, path):
        self.path = path
        self.items = []
        if os.path.exists(path):
            self.items = [json.loads(line) for line in open(path) if line.strip()]

    def _append(self, rec):
        self.items.append(rec)
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps(rec) + "\n")


class SolutionCache(_JsonlStore):
    """A growing library of verified solutions, retrieved by task similarity."""

    def __init__(self, path="heal/solution_cache.jsonl"):
        super().__init__(path)

    def store(self, task, lang, solution):
        if solution and not any(r["task"] == task and r["lang"] == lang for r in self.items):
            self._append({"task": task, "lang": lang, "solution": solution})

    def retrieve(self, task, lang, k=2, thresh=0.12):
        q = _toks(task)
        scored = [(_sim(q, _toks(r["task"])), r) for r in self.items if r.get("lang") == lang]
        scored.sort(key=lambda x: -x[0])
        return [r for s, r in scored[:k] if s >= thresh]

    def hint(self, task, lang, k=2):
        rel = self.retrieve(task, lang, k)
        if not rel:
            return ""
        body = "\n".join(f"# {r['task']}\n```{lang}\n{r['solution']}\n```" for r in rel)
        return ("\n\nYou previously solved similar tasks (VERIFIED correct) — reuse these "
                f"proven patterns:\n{body}")


class ProjectMemory(_JsonlStore):
    """Durable facts about THIS project (conventions, decisions, gotchas), retrieved
    by relevance — persists across sessions so the model knows your repo cold."""

    def __init__(self, path="heal/project_memory.jsonl"):
        super().__init__(path)

    def remember(self, fact, kind="convention"):
        if fact and not any(r["fact"] == fact for r in self.items):
            self._append({"fact": fact, "kind": kind})

    def recall(self, query, k=4, thresh=0.08):
        q = _toks(query)
        scored = sorted(((_sim(q, _toks(r["fact"])), r) for r in self.items), key=lambda x: -x[0])
        hits = [r["fact"] for s, r in scored[:k] if s >= thresh]
        return ("\n\nProject memory (your conventions/decisions):\n- " + "\n- ".join(hits)) if hits else ""


def selftest():
    import tempfile
    d = tempfile.mkdtemp()
    c = SolutionCache(os.path.join(d, "sc.jsonl"))
    c.store("debounce a function with a delay in milliseconds", "ts", "export function debounce(){}")
    c.store("parse a postgres connection string", "ts", "export function parsePg(){}")
    hit = c.retrieve("write a debounce helper with millisecond delay", "ts", k=1)
    ok1 = bool(hit) and "debounce" in hit[0]["solution"]
    pm = ProjectMemory(os.path.join(d, "pm.jsonl"))
    pm.remember("we use OKLCH color tokens, never hex", "design")
    pm.remember("callsieve is the retrieval tool; never grep")
    ok2 = "OKLCH" in pm.recall("what color format for the design tokens")
    print(f"  selftest: cache retrieves the debounce solution={ok1}; project memory recalls "
          f"OKLCH rule={ok2}  {'PASS ✅' if ok1 and ok2 else 'FAIL'}")
    return ok1 and ok2


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
