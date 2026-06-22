# 20-Agent Audit — findings triage (2026-06-18)

20 read-only sub-agents, one per area. ~60 raw findings → triaged below. Status: ✅fixed · 🔧verify-then-fix · ❌false-alarm.
Each agent's claim was/should-be VERIFIED against the actual code before fixing (agents are capable but misread control flow — see the `gate` false alarm).

## ✅ FIXED this session (verified real)
- **83_build_soul_corpus.py** — train/valid LEAKAGE (valid was a subset of train). → train=rows[nval:]. *(affects design heal)*
- **33_live_docs_rag.py** — dedup keyed on per-run temp path → index grows unbounded every run. → key on basename. *(affects docs-index)*
- **docs_manifest.json** — cppreference C++23 URL 404. → compiler_support/23.
- **86_scoreboard.py + 57 track** — jsonl crash on corrupt line (earlier hunt). → tolerant read.
- **57_tool_agent _safe + dev_tools apply_patch** — sandbox escape via sibling-prefix (earlier hunt). → trailing-sep check.

## ❌ FALSE ALARMS (verified — do NOT "fix")
- **04_quantize.py "gate" substring** — claimed expert gate_proj left unquantized. CONFIG PROVES gate_proj IS 3-bit quantized (predicate sees the `switch_mlp` module path, not the `.gate_proj` sub-path). NOT a bug.
- **73_minif2f enumerate_fallback** — confirmed CLEAN (never on in eval — honest).
- **88_verifier_distill, open().write leaks** — CLEAN (skip!=pass logic correct; CPython refcount-closes).

## 🔧 CONFIRMED-REAL, HIGH VALUE — fix next (verify each first)
### Crashes / robustness (agent loop is hot path)
- **57_tool_agent L416** — tool dispatch has NO try/except → any tool exception kills agent_loop. Wrap it.
- **57_tool_agent run()** — `TimeoutExpired` unhandled → crash; + shell=True no process-group → orphan grandchildren. Popen+start_new_session+killpg.
- **57_tool_agent task_t** — no recursion-depth limit → infinite sub-agent nesting. Add depth guard.
- **dev_tools.py profile()** — uses `sys.executable` but `sys` not imported → NameError crash. Add import.
- **84_kl_eval / 04b_sensitivity_plan** — div-by-zero & nan-on-empty (mean([]), all-masked logits). Guard.

### Correctness (silently wrong numbers)
- **verifiers skip-not-checked** — 53_arena:98, 54_search:41/53 read `.passed` without `stage!="skip"` → false-PASS counts skips as solved. Add the guard (88 already does it right).
- **verify_lean "sorry"** — substring matches identifiers (not_sorry) → false-FAIL. `\bsorry\b`.
- **58_bench.py** — pass@1 divides by args.n not min(n,len(ds)) → deflated %. 
- **59_stem_diag.py** — GSM8K gold with `$` → float() fails → false-negative. Strip non-numeric.
- **86_scoreboard guard** — compound study_set ("a+b") bypasses the substring check; split not lowercased. Tokenize+lower.
- **87_lean_study selftest** — returns green when verify_disjoint()==None (offline) → false confidence. sys.exit(1).

### Design-heal relevant (auto-runs tonight — VERIFY before trusting its output)
- **77_soul_flywheel** — code/math/arch facets use stub gate `lambda _:[]` (always pass, no real verify); + no dedup (n/len(prompts) near-dupes); + truncate-on-interrupt. CONFIRM the *design* facet uses the real render-critic gate before relying on the heal.

### Security / leaks (long-run)
- **trust.py** — secret gaps: `github_pat_`, JWT (`eyJ…`), AWS STS (`ASIA`); "you are now" false-positive; zero-width/fullwidth unicode injection bypass (NFKC normalize).
- **reliability.py** — `shell=True` on caller string (injection); `exit=1` substring matches exit=10/12.
- **ptr_store._STORE / sys.path.insert ×18 / prompt_cache._cached_ids** — unbounded growth over a long agent run. Cap/evict.
- **stability.py** — respawn race (no lock → thundering-herd); failed-respawn return value ignored → fires into dead server.

### Build / pipeline
- **79_demolition_family** — `int(float("2.5"))==2` → 36gb silently builds as 2-bit (==20gb); GGUF skip checks for `convert_hf_to_gguf.py` on PATH which Homebrew never installs → dead branch.
- **install_glm_dsa_patch** — DSV32_OLD string stale → patch silently inert on current mlx_lm; non-atomic write.
- **rag.py** — hybrid merge adds raw cosine [-1,1] to normalized BM25 (scale mismatch); `_HTML` regex strips prose containing bare `<` (C++/TS!).
- **27/06 heal** — no dedup; 27 double-parses + crashes on one bad jsonl line.

### Docs
- **MODEL_CARD/README** — headline "99 GB" vs family-table "~106 GB" (same model); VLM (Qwen3-VL-4B-8bit) + embedding (bge-large) named in code/BACKLOG but not the card.

## Method note
The single most valuable lesson: the `gate` "HIGH" finding was the scariest and **wrong** — only the built-model config settled it. Verify every agent claim against ground truth before editing.
