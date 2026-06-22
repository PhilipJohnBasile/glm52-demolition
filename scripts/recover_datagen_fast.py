"""#115+#114 FAST flywheel — in-process prompt-lookup spec-decode (2.5× on code-fixes), NO serve.

The HTTP-serve flywheel was slow (~30/hr, decode-bound) AND crashed under concurrent load. This loads the
model ONCE in-process (the one big model — crash-safe by construction) and generates fixes with
prompt-lookup speculative decoding (src/spec_decode.py): the fix reuses the buggy code, so ~56% of tokens
are drafted free → 2.5× faster. Greedy primary (fast, usually correct) + sampled fallbacks for diversity.

  HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 python scripts/recover_datagen_fast.py 500   # ONLY when serve is stopped
"""
import json
import sys

import mlx.core as mx
from mlx_lm import load
from mlx_lm.sample_utils import make_sampler

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
from spec_decode import prompt_lookup_generate_step          # noqa: E402
from recover_datagen_diverse import MUTS, problems           # noqa: E402  (reuse corpus + mutations)
from verifiers import verify                                 # noqa: E402

MODEL, TOK = None, None


def gen(prompt, temp=0.0, max_tokens=420):
    # MUST apply the chat template (the serve did this; raw encode → malformed prompt → garbage output)
    try:
        toks = TOK.apply_chat_template([{"role": "user", "content": prompt}],
                                       add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        toks = TOK.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True)
    ids = mx.array(toks)
    sampler = None if temp == 0 else make_sampler(temp=temp, top_p=0.95)
    out = []
    for t, _ in prompt_lookup_generate_step(ids, MODEL, max_tokens=max_tokens,
                                            n_gram=3, num_draft_tokens=10, sampler=sampler):
        out.append(t)
        if t in TOK.eos_token_ids:
            break
    return TOK.decode(out)


def extract(text):
    import re
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def main():
    global MODEL, TOK
    target = int(next((a for a in sys.argv[1:] if a.isdigit()), 500))
    print("  loading model+adapter (in-process, one big model)...", flush=True)
    MODEL, TOK = load("models/GLM-5.2-q3a4-v2", adapter_path="heal/adapters-recover")
    out = open("recover_data_diverse.jsonl", "a")
    kept = 0
    for code, tests, pid in problems():
        try:
            if not verify("python", code, harness=tests).passed:
                continue
            bugs = []
            for find, repl in MUTS:
                if find in code and len(bugs) < 3:
                    cand = code.replace(find, repl, 1)
                    v = verify("python", cand, harness=tests)
                    if not v.passed:
                        bugs.append((find, repl, cand, v.diag))
            for find, repl, buggy, diag in bugs:
                prompt = (f"This Python code has a bug — the test fails:\n```python\n{buggy}\n```\n"
                          f"Failing test output:\n{(diag or '')[:400]}\nTests:\n```python\n{tests}\n```\n"
                          f"Output ONLY the corrected full code.")
                # greedy prompt-lookup first (2.5×, usually the right fix), then sampled fallbacks
                import time as _t
                print(f"  · {pid} {find!r}->{repl!r} generating...", flush=True)
                for temp in (0.0, 0.5, 0.8):
                    _t0 = _t.time()
                    c = extract(gen(prompt, temp=temp))
                    _ok = bool(c and c.strip() != buggy.strip() and verify("python", c, harness=tests).passed)
                    print(f"    temp{temp}: {len(c)}ch in {_t.time()-_t0:.0f}s pass={_ok}", flush=True)
                    if _ok:
                        out.write(json.dumps({"messages": [{"role": "user", "content": prompt},
                                                            {"role": "assistant", "content": c}]}) + "\n")
                        out.flush()
                        kept += 1
                        print(f"  ✓ kept {pid} {find!r}->{repl!r} (total {kept}, temp {temp})", flush=True)
                        break
                if kept >= target:
                    break
            if kept >= target:
                break
        except Exception as e:
            print(f"  ! {pid}: {str(e)[:60]}", flush=True)
    print(f"  FAST flywheel: {kept} verified fixes (prompt-lookup spec-decode)")


if __name__ == "__main__":
    main()
