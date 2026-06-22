"""#4b Mine REAL Rust fn+test pairs from the sibling repos (callsieve, vecstore) for the Rust flywheel.

The flywheel's 4 toy samples don't generalize. The user's own Rust repos have 1300+ #[test] fns — real
code. This extracts self-contained `pub fn` + a `#[test]` that exercises it, pairs them, and keeps only
pairs that compile+pass standalone via `cargo test` (the same filter the flywheel uses). Serve-free.

  python scripts/mine_rust_samples.py ../callsieve ../vecstore   # -> rust_samples.jsonl (verified pairs)
"""
import json
import os
import re
import sys

sys.path.insert(0, "scripts")
from recover_datagen_rust import cargo_test  # reuse the real cargo-test verify


def _block(src, brace_start):
    """Return src[start..matching-close] for the block beginning at the first '{' >= brace_start."""
    i = src.find("{", brace_start)
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[brace_start:j + 1]
    return None


def extract_fns(src):
    fns = {}
    for m in re.finditer(r"\bpub fn (\w+)\s*\([^;{]*?\)\s*(?:->[^{;]+?)?\s*\{", src):
        body = _block(src, m.start())
        if body and len(body) < 600:                 # small, self-contained-ish
            fns[m.group(1)] = "pub " + body[body.find("fn "):] if "fn " in body else body
    return fns


def extract_tests(src):
    tests = []
    for m in re.finditer(r"#\[test\]\s*fn (\w+)\s*\(\s*\)\s*\{", src):
        body = _block(src, m.start(src.find("fn", m.start())) if False else m.start())
        blk = _block(src, m.end() - 1)
        if blk and len(blk) < 500:
            tests.append(blk)
    return tests


def main():
    repos = sys.argv[1:] or ["../callsieve", "../vecstore"]
    cand = []
    for repo in repos:
        for root, _, files in os.walk(os.path.join(repo, "src")):
            for fn in files:
                if not fn.endswith(".rs"):
                    continue
                src = open(os.path.join(root, fn), errors="ignore").read()
                fns = extract_fns(src)
                for test in extract_tests(src):
                    used = [n for n in fns if re.search(rf"\b{n}\s*\(", test)]
                    if len(used) == 1:               # test exercises exactly one mined fn
                        code = fns[used[0]]
                        # self-contained: fn body calls only itself + std-ish (no other repo fns)
                        harness = f"#[cfg(test)] mod tests {{ use super::*; #[test] fn t() {test} }}"
                        cand.append((used[0], code, harness))
    print(f"  candidates: {len(cand)} (fn+test pairs across {len(repos)} repos)")
    kept, out = 0, open("rust_samples.jsonl", "w")
    for name, code, harness in cand:
        if cargo_test(code, harness):                # keep only standalone-compilable+passing
            out.write(json.dumps({"fn": name, "code": code, "test": harness}) + "\n")
            kept += 1
            if kept % 10 == 0:
                print(f"  ...{kept} verified", flush=True)
        if kept >= 200:
            break
    print(f"  ✅ {kept} VERIFIED real-world Rust fn+test pairs -> rust_samples.jsonl (flywheel seed)")


if __name__ == "__main__":
    main()
