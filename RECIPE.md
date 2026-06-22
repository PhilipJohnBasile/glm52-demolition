# RECIPE — run the demolished model + its lanes

A one-page operator guide. Full story: `README` · `MODEL_CARD` · `FACTORY` · `AGENTIC`.

## 1. One-time setup
```bash
sudo sysctl iogpu.wired_limit_mb=122000        # raise the GPU ceiling (else long runs OOM)
python dist/install_glm_dsa_patch.py           # patch mlx_lm (venv + LM Studio's bundled engine)
```

## 2. Serve (OpenAI-compatible)
```bash
GLM_STREAM_EVAL=0 python -m mlx_lm.server --model models/GLM-5.2-q3a4-v4 \
    --adapter-path adapters-soul2 --port 8080
```
Point any OpenAI-compatible agent at `http://localhost:8080/v1` (Cline · Aider · Cursor · OpenCode).

## 3. Swap a soul (the factory)
Stop the serve, change `--adapter-path`, restart (~3 min reload). The library:
`adapters-soul2` (core) · `gamedev` · `legacy` · `security` · `fullstack` · `science` · `factory` · `perfumery`.

## 4. The six-chip lanes (off the GPU)
```python
from omni import handle, generate
# INPUT — read any modality:
handle("fix the failing pytest")        # text  -> route -> LLM
handle(image="shot.png")                # image -> ANE OCR + classify
handle(audio="clip.wav")                # audio -> Whisper ASR (MLX)
handle(video="clip.mov")                # video -> Media decode + ANE classify
handle(table=df)                        # table -> CPU sklearn
# OUTPUT — write any modality:
generate("image",  "a dark SaaS pricing hero, OKLCH greens")   # -> Flux (GPU)
generate("speech", "build complete")                            # -> ANE TTS
generate("audio",  "calm ambient pad")                          # -> mlx_audio (GPU)
```

## 5. The autonomous flywheel
- `scripts/factory_chain.sh` — forge the 7 souls overnight (wait-for-GPU → heal → next).
- `src/hardneg_flywheel.py` — mine repair hard-negatives on CPU+ANE (real algorithmic bugs).
- `scripts/post_chain.sh` — after the souls, auto-prep the repair data, heal on it, and run the
  repair-eval gate. The compounding loop **mine → heal → measure** closes with no operator.

## 6. Speed knobs
`--dsa-block-size 32/64/128` (free, pick fastest) · throughput batching for concurrent requests (2.6× at B=8).
~11–14 tok/s single-stream is the memory trade for a local 743B-class model.
