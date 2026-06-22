"""ANE speculative ACTIONS (#4, the fast+correct plan) — the ANE router (16-core) predicts the agent's NEXT
tool from the recent context, BEFORE the big model decides. When the prediction matches what the big model
would do (it usually does for obvious steps), the agent pre-warms/pre-fetches that tool → ~1/3 of turns get a
head start, LOSSLESS (the big model still decides — this only speculates). Reuses #78 embeddings + #80 router.

    from spec_action import speculate_next_tool
    tool, conf = speculate_next_tool("the pytest failed with ImportError: no module named utils")
    # -> ("read_file", 0.55)   # likely needs to read the missing module — pre-warm that tool
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

TOOLS = {
    "read_file": "read open view inspect a file's contents to understand the code",
    "write_file": "write edit modify fix implement patch change save code to a file",
    "run": "run execute a command tests build compile pytest cargo npm shell",
    "search": "search grep find locate a symbol pattern function across the codebase",
    "done": "the task is complete all tests pass finished nothing left to do",
}
TOOL_KW = {
    "read_file": ["see ", "view", "read", "look at", "contents", "what's in", "inspect", "show me"],
    "write_file": ["fix", "edit", "change", " add ", "modify", "implement", "patch", "rewrite"],
    "run": ["run", "execute", " test", "build", "compile", "pytest", "cargo", "npm", "re-run"],
    "search": ["find", "search", "grep", "where is", "locate", "which file"],
    "done": ["done", "complete", "all pass", "finished", "all green", "works now", "success"],
}


def speculate_next_tool(context, tools=None, threshold=0.25, kw_boost=0.2):
    """Predict the agent's next tool from context, on the ANE. Returns (tool, confidence) — or (None, conf)
    below threshold (defer entirely to the big model). Lossless: the big model still decides; this pre-warms."""
    from ane_embed import ANEEmbedder
    t = tools or TOOLS
    labels = list(t.keys())
    c = context.lower()
    e = ANEEmbedder()
    sims = e.embed([t[k] for k in labels]) @ e.embed([context])[0]
    scored = [(k, float(sims[i]) + kw_boost * sum(1 for w in TOOL_KW.get(k, []) if w in c))
              for i, k in enumerate(labels)]
    scored.sort(key=lambda x: -x[1])
    best, conf = scored[0]
    return (best if conf >= threshold else None, round(conf, 3))


if __name__ == "__main__":
    cases = [
        ("the pytest failed with ImportError: no module named utils", ("read_file", "search")),
        ("I need to fix the add function so it returns a plus b", ("write_file",)),
        ("re-run the test suite to check", ("run",)),
        ("all tests pass now, the bug is fixed and done", ("done",)),
        ("where is the User model defined", ("search", "read_file")),
    ]
    ok = 0
    for ctx, want in cases:
        tool, conf = speculate_next_tool(ctx)
        hit = tool in want
        ok += hit
        print(f"  {'OK ' if hit else 'XX '} {str(tool):11} ({conf}) want {want}")
    print(f"  spec_action selftest {'PASS' if ok >= 4 else 'CHECK'} — {ok}/5 next-tool predictions on the ANE")
