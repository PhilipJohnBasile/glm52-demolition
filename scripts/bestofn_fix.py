#!/usr/bin/env python3
"""#113 best-of-N LOCALIZED fix — the verifier-gated patch that beats the wandering agent.

Given a callsieve-pinpointed bug LINE + the expected behavior (failing-test names), sample N candidate
replacement lines directly from the model (over its 3-bit temp variance), compile+test each, and apply
the FIRST that passes. No agentic loop -> no escape hatches (clarify / peek-loop / garbage patch) that
derail the full-agent path. For a localized bug this is faster AND more reliable than the ReAct loop:
the model proposes, the verifier (cargo test) disambiguates — cracking both sampling variance and
subtle operator-flips (>/<) the single-shot fix-packet misses.
"""
import argparse
import json
import os
import re
import subprocess
import urllib.request


def gen(base_url, prompt, temp, max_tokens=160):
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp,
        "top_p": 0.95,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions", body, {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        msg = json.loads(r.read())["choices"][0]["message"]
        return msg.get("content") or ""


def clean_line(text):
    """Pull a single corrected code line out of the model's reply (tolerate fences/labels)."""
    text = re.sub(r"```\w*", "", text)
    for ln in text.splitlines():
        s = ln.strip()
        if s and not s.lower().startswith(("here", "the ", "output", "corrected", "//")):
            return ln.rstrip()
    stripped = text.strip().splitlines()
    return stripped[0].rstrip() if stripped else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--line", type=int, required=True)
    ap.add_argument("--expect", default="", help="expected-behavior hint; auto-extracted if empty")
    ap.add_argument("--test", default="cargo test")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--base-url", default="http://localhost:8080/v1")
    a = ap.parse_args()

    path = os.path.join(a.repo, a.file)
    orig = open(path).read().splitlines(keepends=True)
    buggy = orig[a.line - 1].rstrip("\n")
    ctx = "".join(orig[max(0, a.line - 4):a.line + 3])

    # fix-packet++: the failing test's ASSERTION body reveals the expected behavior (e.g. which way a
    # `>/<` should flip) where the test NAME alone can't. Auto-extract it when --expect is empty.
    expect = a.expect
    if not expect:
        out = subprocess.run(a.test, shell=True, cwd=a.repo, capture_output=True, text=True, timeout=600)
        names = re.findall(r"(\w+) \.\.\. FAILED", (out.stdout or "") + (out.stderr or ""))[:2]
        bodies = []
        for name in names:
            src = open(path).read()
            m = re.search(r"(fn " + re.escape(name) + r"\(.*?\n(?:    )?\})", src, re.S)
            if m:
                bodies.append(m.group(1)[:600])
        expect = ("\n".join(f"test {n}:\n{b}" for n, b in zip(names, bodies))
                  if bodies else ", ".join(names))

    prompt = (
        f"Bug in {a.file}. Context:\n```rust\n{ctx}```\n"
        f"Line {a.line} is: `{buggy.strip()}`\n"
        f"The failing test(s) below describe the EXPECTED behavior — use them to infer the fix "
        f"(e.g. the correct comparison/operator/value), even if it differs from the current line:\n"
        f"{expect}\n"
        f"Output ONLY the corrected version of line {a.line} as a single line of VALID Rust "
        f"(same indentation, no explanation, no code fence)."
    )

    seen = set()
    for i in range(a.n):
        cand = clean_line(gen(a.base_url, prompt, temp=0.45 + 0.15 * i))
        if not cand or cand.strip() == buggy.strip() or cand.strip() in seen:
            print(f"  cand {i + 1}: skip ({cand.strip()!r})", flush=True)
            continue
        seen.add(cand.strip())
        new = orig[:]
        new[a.line - 1] = cand + ("\n" if not cand.endswith("\n") else "")
        open(path, "w").writelines(new)
        rc = subprocess.run(a.test, shell=True, cwd=a.repo,
                            capture_output=True, text=True, timeout=600).returncode
        print(f"  cand {i + 1}: {'PASS' if rc == 0 else 'fail'} -> {cand.strip()!r}", flush=True)
        if rc == 0:
            print(f"BESTOFN_FIX: PASS in {i + 1} candidate(s) — applied {cand.strip()!r}")
            return
        open(path, "w").writelines(orig)  # revert before next candidate
    # FUNCTION-LEVEL FALLBACK (arXiv 2604.00167: function-level repair 45.6% > line 43.6%, esp. multi-line
    # bugs like off-by-one). If line-level failed all N, regenerate the whole enclosing function.
    fn_start = a.line - 1
    while fn_start > 0 and not re.match(r"\s*(def |fn |function |pub fn )", orig[fn_start]):
        fn_start -= 1
    fn_end = a.line
    while fn_end < len(orig) and not (orig[fn_end].rstrip() in ("}", "    }") or (fn_end>a.line and orig[fn_end] and not orig[fn_end][0].isspace())):
        fn_end += 1
    fn_text = "".join(orig[fn_start:fn_end+1])
    fprompt = (f"This function has a bug; the test fails.\n```\n{fn_text}```\n"
               f"Expected behavior:\n{expect}\nOutput ONLY the corrected full function (valid code).")
    for i in range(3):
        cand = gen(a.base_url, fprompt, temp=0.4 + 0.15 * i, max_tokens=400)
        import re as _re
        m = _re.search(r"```(?:\w+)?\n(.*?)```", cand, _re.S)
        body = (m.group(1) if m else cand).strip()
        if not body:
            continue
        new = orig[:fn_start] + [body + "\n"] + orig[fn_end+1:]
        open(path, "w").writelines(new)
        rc = subprocess.run(a.test, shell=True, cwd=a.repo, capture_output=True, text=True, timeout=600).returncode
        print(f"  fn-cand {i+1}: {'PASS' if rc==0 else 'fail'} (function-level)", flush=True)
        if rc == 0:
            print(f"BESTOFN_FIX: PASS via function-level fallback (cand {i+1})"); return
        open(path, "w").writelines(orig)
    print("BESTOFN_FIX: all candidates failed")


if __name__ == "__main__":
    main()
