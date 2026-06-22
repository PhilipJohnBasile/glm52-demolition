"""Skill library — procedural memory (the 2026 self-improvement pattern: Voyager / AutoSkill).
The agent distills VERIFIED solutions into named, reusable skills, then retrieves + composes them
instead of re-reasoning from scratch (saves tokens, no catastrophic forgetting). Persistent across
sessions -> the agent COMPOUNDS on YOUR codebase, which a cloud agent structurally can't.
Skills live in skills/*.json.
"""
import glob
import json
import os
import re
import time

SKILL_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")


def _toks(s):
    return set(re.findall(r"[a-z0-9_]+", (s or "").lower()))


class SkillLibrary:
    def __init__(self, path=SKILL_DIR):
        self.path = path
        os.makedirs(path, exist_ok=True)

    def save(self, name, description, code, lang="python", harness="", tags=""):
        """Store a VERIFIED skill (code that passed its harness) for reuse."""
        name = re.sub(r"[^a-z0-9_]+", "_", (name or "skill").lower()).strip("_")[:50] or "skill"
        rec = {"name": name, "description": description, "code": code, "lang": lang,
               "harness": harness, "tags": tags, "uses": 0, "saved": round(time.time())}
        json.dump(rec, open(os.path.join(self.path, name + ".json"), "w"), indent=1)
        return f"saved skill '{name}' ({lang})"

    def find(self, query, k=5):
        """Retrieve relevant skills by description/tags/name (token overlap)."""
        q = _toks(query)
        scored = []
        for f in glob.glob(os.path.join(self.path, "*.json")):
            try:
                r = json.load(open(f))
            except Exception:  # noqa: BLE001
                continue
            score = len(q & _toks(r["description"] + " " + r.get("tags", "") + " " + r["name"]))
            if score:
                scored.append((score, r))
        scored.sort(key=lambda x: -x[0])
        hits = [f"{r['name']} ({r['lang']}, {r['uses']} uses): {r['description'][:70]}"
                for _, r in scored[:k]]
        return "\n".join(hits) if hits else "(no matching skills yet — solve it, then save it)"

    def get(self, name):
        """Retrieve a skill's code to reuse / compose (increments its use count)."""
        f = os.path.join(self.path, re.sub(r"[^a-z0-9_]+", "_", (name or "").lower()).strip("_") + ".json")
        if not os.path.exists(f):
            return f"no skill '{name}' — use find first"
        r = json.load(open(f))
        r["uses"] += 1
        json.dump(r, open(f, "w"), indent=1)
        return f"# skill: {r['name']} — {r['description']}\n{r['code']}"

    def list_skills(self):
        out = []
        for f in sorted(glob.glob(os.path.join(self.path, "*.json"))):
            try:
                r = json.load(open(f))
            except Exception:  # noqa: BLE001
                continue
            out.append(f"{r['name']} ({r['lang']}, {r['uses']}×): {r['description'][:60]}")
        return "\n".join(out) or "(empty library)"


def selftest():
    import tempfile
    lib = SkillLibrary(tempfile.mkdtemp())
    lib.save("retry_backoff", "retry an async fn with exponential backoff + jitter",
             "async function retry(fn){/* ... */}", "ts", tags="async resilience")
    found = lib.find("exponential backoff retry async")
    got = lib.get("retry_backoff")
    ok = "retry_backoff" in found and "retry" in got and "skill:" in got
    print(f"  skills selftest: save+find+get+compound  {'PASS ✅' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
