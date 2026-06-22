"""Pointer store — big tool outputs live OUTSIDE the context window; the model gets a short
HANDLE plus a preview, and pages/greps the full content on demand instead of overflowing the
context (the 2026 fix for large tool responses — store data outside, interact via identifiers).
Session-scoped, in-memory.
"""
import re

_STORE = {}
_N = [0]
THRESHOLD = 3000          # outputs longer than this get stored + handed back as a pointer


def store(content, kind="out"):
    """Stash a large output; return (handle, preview-with-instructions)."""
    _N[0] += 1
    h = f"ptr:{kind}:{_N[0]}"
    if len(_STORE) >= 256:                               # session cache, not unbounded — evict oldest (insertion-ordered dict)
        del _STORE[next(iter(_STORE))]
    _STORE[h] = content
    lines = content.count("\n") + 1
    head = content[:600]
    return h, (f"[{h} — {len(content)} chars / {lines} lines stored OUTSIDE context. "
               f"Use peek({h},start,n) or grep_ptr({h},pattern) to read it.]\nHEAD:\n{head}")


def maybe_store(content, kind="out"):
    """If `content` is large, store it and return the pointer+preview; else return it as-is."""
    s = str(content)
    if len(s) <= THRESHOLD:
        return s
    return store(s, kind)[1]


def peek(handle, start=0, n=2000):
    c = _STORE.get(handle)
    if c is None:
        return f"no such handle {handle} (expired or wrong id)"
    start = int(start)
    return c[start:start + int(n)] or "(past end)"


def grep_ptr(handle, pattern):
    c = _STORE.get(handle)
    if c is None:
        return f"no such handle {handle}"
    try:
        hits = [ln for ln in c.splitlines() if re.search(pattern, ln)]
    except re.error as e:
        return f"bad pattern: {e}"
    return "\n".join(hits[:80]) or "(no match)"


def selftest():
    big = "\n".join(f"line {i} alpha" if i != 42 else "line 42 NEEDLE" for i in range(500))
    out = maybe_store(big, "test")
    h = out.split(" ")[0].strip("[")
    ok = "ptr:test:" in out and "NEEDLE" in grep_ptr(h, "NEEDLE") and "line 0" in peek(h, 0, 40)
    small = maybe_store("short", "test")
    ok = ok and small == "short"
    print(f"  ptr_store selftest: store+peek+grep + small-passthrough  {'PASS ✅' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
