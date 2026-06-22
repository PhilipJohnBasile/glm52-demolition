# SWE-bench n=5 (GUARDED serve, post-crash) — Sat Jun 20 20:16:43 EDT 2026
guarded serve up (MLX self-bounds @115GB, evicts not crashes) — SWE-bench n=5:
  [1/5] astropy__astropy-12907
  [2/5] astropy__astropy-13033
  [3/5] astropy__astropy-13236
  [4/5] astropy__astropy-13398
  [5/5] astropy__astropy-13453
  wrote 5 predictions → swebench5_preds.jsonl
  SCORE (official, Docker): python -m swebench.harness.run_evaluation --predictions_path swebench5_preds.jsonl --run_id glm52
SWEBENCH5 DONE Sat Jun 20 20:51:00 EDT 2026
