# I shrank a 743-billion-parameter AI down to run on a laptop 🧨

Frontier language models are enormous — **GLM-5.2 is 743B parameters** and normally needs a server rack.
I spent a stretch *demolishing* it down to **~98 GB so it runs entirely on one MacBook (M5 Max, 128 GB)** —
then proved it still writes real code: **69% on HumanEval-164** (a standard coding benchmark), single-shot,
scored by actual compilers/tests.

It's all open-source and — the part I care about most — **honest about what works *and* what doesn't.**

### The model + data + pipeline
- 🤗 **Model** (download & run it yourself, MIT): https://huggingface.co/philipjohnbasile/GLM-5.2-Demolition-q4a4-soul-MLX
- 🤗 **Dataset** (272K verifier-checked code examples): https://huggingface.co/datasets/philipjohnbasile/glm52-demolition-data
- 🐙 **Full pipeline + the honest write-up** (incl. a "what *didn't* work" map so you don't waste the weeks I did): https://github.com/PhilipJohnBasile/glm52-demolition

### The tools I built along the way — all MIT, all work with *any* model
- 🐶 **merle** — a verifier-first coding agent (CLI) that checks its own work (compiles/tests) before trusting it: https://github.com/PhilipJohnBasile/merle
- 🔎 **callsieve** — local codebase retrieval for AI agents; finds the right files *before* you grep. 60% first-correct-file@5 on SWE-bench Lite (10× naive grep): https://github.com/PhilipJohnBasile/callsieve
- 🗃️ **vecstore** — embeddable vector DB for Rust & Python; HNSW + hybrid search. "The SQLite of vector search": https://github.com/PhilipJohnBasile/vecstore

### The honest takeaway
A demolished giant **can't** beat a clean, right-sized model — I measured it. But the *methods*
(saliency-guided pruning, LoRA healing, swappable "soul" adapters, and verify-first agents) all **transfer**.
The fun result: a 744B model, quartered, still writing usable code on a laptop — and every number is real,
nothing faked.
