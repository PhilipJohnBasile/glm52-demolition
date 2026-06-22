# Beating Suno / Udio — Sound Generation SOTA, 10 Rounds

*Research base for executing music + SFX generation **better than Suno/Udio** by attacking the axes they're
structurally weak on. Companion to `research/elite_sound.md` (the masters' canon). The thesis in one line:
**they generate audio; we compose music — and prove it.** We do not try to out-fidelity a cloud diffusion
model trained on the whole internet; we out-**control, out-structure, out-verify, out-taste**, run it
**local on MLX**, and keep it **editable** — the composer's craft they skip.*

---

## Round 1 — How Suno / Udio actually work, and where they genuinely win

Both are **end-to-end neural audio** systems: a latent-diffusion / autoregressive transformer over neural
**codec tokens** (EnCodec/DAC-style), trained on enormous catalogs of real recordings. Text (+ lyrics) →
waveform, one shot. Suno **v5.5** (Mar 2026) is the strongest all-rounder — clean lyrics, hooks that land,
arrangements that "feel like songs not loops," studio-quality audio, natural vocals, stem export, a full
workstation. Udio edges it on fidelity in hip-hop/R&B/pop and on long-form coherence.

**Implication:** their moat is raw audio realism + vocals, bought with data + scale. **Do not fight them
there — we lose.** Everything below is about the craft layer they skipped to get there.

## Round 2 — The five structural gaps (our openings — quoted from 2026 reviews)

1. **No production-fundamental control.** *"doesn't reliably take direction on bar count, key, form, tempo… doesn't reliably recognise prompts around bars, key, form and tempo."* The composer's grammar is missing.
2. **No verification / repair.** *"vocals… holds notes too long, suddenly jumps pitch, over-energies a line, and without a reliable way to fix these issues."* One-shot, no correction loop.
3. **Median taste.** Trained on the average of the catalog → competent, genre-safe, but no named-master spine; *"complex jazz scatting or operatic passages reveal the model's limitations."*
4. **Cloud + licensing taint.** RIAA sued both (Jun 2024); Warner settled with Suno (Nov 2025) but **Universal + Sony still suing Suno** (Jun 2026); Udio locked downloads/sharing during its UMG transition. Output provenance is contested; you're in their ecosystem.
5. **Basic editing.** Stems exist but it's not symbolic — you can't open the score, fix bar 12's voice-leading, swap a chord, or re-time a hit.

**Each gap is a feature we can own:** explicit structure · a verify→repair loop · masters-grounded taste · local + clean-data · symbolic/MIDI editability.

## Round 3 — The open SOTA we stand on (adopt the render, run it on MLX)

- **Stable Audio Open 1.5** — continuous-latent diffusion, trained on **Freesound CC0/CC-BY** → **commercial-clean** (Stability community license under a revenue threshold). **Our primary render engine** — the licensing story Suno can't offer.
- **MusicGen (Meta)** — single-stage transformer over EnCodec tokens; great, but **CC-BY-NC → output not commercial.** Use for R&D / melody-conditioning experiments only.
- **SongGeneration-v2**, **YuE 7B**, **ACE-Step 3.5B** — full song / vocal models, open weights.
- **The codecs** — EnCodec / DAC / the Stable-Audio VAE: the shared audio representation 2026 models reuse.

**MLX reality (confirmed Feb 2026):** MusicGen, Stable Audio Open, **SongGeneration**, and `mlx-audio` all have **Apple-Silicon MLX ports running on-device via Metal** (the MusicGen port even solved the complex-RoPE issue with paired sin/cos). So the neural render layer is **local, today** — exactly the MLX-first doctrine: adopt their method + weights, run the compute on the M5.

## Round 4 — The control research = the academic edge Suno ignores

The symbolic-control literature is precisely the "bar/key/form/tempo" grammar Suno lacks:
- **MusiConGen** — finetunes MusicGen for **rhythm + chord control** from symbolic *or* reference-audio conditions (backing-track gen).
- **Explicit tonal-tension conditioning** (dual-level beam search over **tonal interval vectors**) — *tension & release, computationally controllable.* This is principle #2 of our canon, as an algorithm.
- **PopMNet** — a structure-net (CNN) → melody-net (RNN) conditioned on **structure + chord progression**. Form first, notes second.
- **Hierarchical structure representation**, **bar-patching control codes** (TunesFormer), **diffusion + structured-state-space (Mamba)** symbolic models.
- Measured: explicit control (attribute / bar-level / FSM) buys **13–20% adherence gains** in chord/structure accuracy over prompt-only.

**Implication:** structure + harmony + rhythm are **controllable and measurable** in the symbolic domain. That is where we plant the flag.

## Round 5 — The symbolic-first inversion (the core architecture bet)

The masters compose **structure** — leitmotif, sonata/verse-chorus form, tension curves, voice-leading. Suno
infers structure implicitly from data and **drops it under pressure** ("loops, not songs"). We **invert the
pipeline**: generate the **score first** — form → harmonic plan → melody/leitmotif → arrangement — in the
**symbolic domain** (music21 + the control methods of Round 4), where it is **controllable, verifiable, and
editable**, and only *then* render to audio. The LLM is the **composer/arranger**; the neural model is the
**session player**. This is the design-soul pattern (plan → render → critique) applied to sound.

## Round 6 — Symbolic → audio (closing the fidelity gap without their data)

How the score becomes great-sounding audio, three rungs (pick per task):
1. **DDSP / MIDI-DDSP** (Magenta) — derive **frequency + loudness + performance attributes** from MIDI → expressive monophonic/instrument audio. Captures **microtiming + dynamics** = the **Dilla feel**, the thing soundfonts kill. 2025 work extends it to polyphonic guitar, singing vocoders, **expressive drum-grid synthesis**.
2. **Melody/chord-conditioned neural render** — feed the symbolic plan as conditioning to **Stable Audio Open** (via MusiConGen-style adapters) so the diffusion model fills timbre/texture *around our structure*.
3. **High-quality sampled instruments** for the deterministic, license-clean baseline (the verifiable floor).

**Implication:** we get audio realism from open models, but **steered by our verified structure** — their fidelity, our control.

## Round 7 — Verification: the moat (already built)

`verify("sound")` (`src/sound_verify.py`, audited PASS) checks what Suno **can't fix**:
- **Harmony / voice-leading** (music21 — parallel fifths, in-key, leading-tone) → Bach-correct.
- **Structure / form** — does the piece have a recognizable form, recurring leitmotif, a tension arc? (the gap from Round 2).
- **Loudness** (LUFS / true-peak, pyloudnorm) → no clipping, broadcast-safe.
- **The feel** (microtiming variance — the **Dilla check**) → reward the human wobble, fail the dead grid.
- **Vocal-pitch stability** — detect the held-too-long / sudden-jump artifacts reviewers flag in Suno, and **regenerate the bar**.

Wrapped in the **render → hear → critique → regenerate** loop + **best-of-N** (#82): generate K, verify all,
keep the best, repair the rest. **They ship the first take; we ship the verified one.**

## Round 8 — The MLX / M5 execution (private, clean, on-device)

All six blocks, the MLX-first way: **GPU** renders (Stable-Audio-Open-MLX / MIDI-DDSP / SongGeneration-MLX +
the agent composing the score) · **18 CPU cores** verify in parallel (music21 / LUFS / feel via `verify_many`)
· **ANE** for perceptual checks (audio-classify #91, embedding similarity to a reference) · **Media Engine**
muxes the final stems. No cloud, no per-track fee, **no licensing taint** (Stable-Audio-Open's CC0 lineage +
our own data). Fully editable: MIDI + stems out.

## Round 9 — Taste via heritage-activation (what median data can't buy)

Suno's taste is the **mean of the catalog**. Ours is **named masters**, internalized: Bach's voice-leading,
Wagner→Williams leitmotif logic, Herrmann's restraint, Burtt's *sound-as-character*, Eno's ambient/earcon,
**Dilla's humanized grid**. The path is the design-soul recipe — **canon (`elite_sound.md`) → validated gold →
heal** — compounded by the **sound-flywheel** (`gen → verify("sound") → keep`, harness PASS, wired into the
night). The model doesn't imitate a genre average; it composes *from principle* and can say *why*.

## Round 10 — The execution plan + the honest verdict

**The hybrid pipeline (the thing to build):**
```
brief ─► COMPOSE (LLM, masters-souled): form → harmony → melody/leitmotif → arrangement   [symbolic, music21]
      ─► VERIFY  (CPU): harmony · structure · tension-arc  ──fail──► critique → recompose
      ─► RENDER  (GPU/MLX): MIDI-DDSP (expressive) OR Stable-Audio-Open (chord/melody-conditioned)
      ─► VERIFY  (CPU/ANE): LUFS · feel/microtiming · vocal-pitch  ──fail──► repair the bar
      ─► best-of-N keep  ─►  OUT: wav + stems + editable MIDI + the "why" (which master, which principle)
```
**Where we beat them (own it):** control (bar/key/form/tempo) · verification + repair · taste (masters) ·
local + clean-licensed · editable (symbolic/stems) · explainable.
**Where we won't (be honest):** raw vocal realism and one-prompt "instant radio song" on arbitrary genres —
their data+scale wins. So we **don't sell "type a sentence, get a hit"**; we sell **"compose a *correct,
controllable, yours* piece, on your Mac."** A different, defensible product.

**Build order:** ✅ canon · ✅ `verify("sound")` · ✅ seed gold + sound-flywheel (wired) → **next:** (1) the
COMPOSE stage (LLM writes a structured music21 score, verified) — GPU-free to prototype; (2) wire a render
rung (MIDI-DDSP first, then Stable-Audio-Open-MLX); (3) the structure/tension + vocal-pitch verifiers; (4)
heal the sound soul on masters-grounded *compositional* gold, not just earcons. Each gated by a measured
adherence number (Round 4's 13–20%), the verify-everything way.

---

### Sources
- [Suno review 2026 (v5.5, Warner, lawsuits) — eesel AI](https://www.eesel.ai/blog/suno-review) · [Suno vs Udio 2026 — TLDL](https://www.tldl.io/resources/ai-music-generators-suno-udio-2026) · [Suno vs Udio — AIViewer](https://aiviewer.ai/guides/best-ai-music-generators-compared/) · [Suno legal risks — aisongcreator](https://aisongcreator.pro/blog/suno-ai-review)
- [Open-source music-gen guide 2026 — Spheron](https://www.spheron.network/blog/deploy-open-source-ai-music-generation-gpu-cloud-2026/) · [Best open music models — SiliconFlow](https://www.siliconflow.com/articles/en/best-open-source-music-generation-models) · [ACE-Step 1.5 (arXiv)](https://arxiv.org/pdf/2602.00744)
- [MusiConGen — rhythm/chord control (arXiv)](https://arxiv.org/pdf/2407.15060) · [Tonal-tension conditioning (arXiv)](https://arxiv.org/pdf/2511.19342) · [Controlled symbolic music gen — EmergentMind](https://www.emergentmind.com/topics/controlled-symbolic-music-generation) · [Diffusion+SSM symbolic (arXiv)](https://arxiv.org/pdf/2507.20128)
- [mlx-audio (Blaizzy/GitHub)](https://github.com/Blaizzy/mlx-audio) · [SongGeneration-v2-large MLX (HF)](https://huggingface.co/mlx-community/SongGeneration-v2-large) · [MusicGen on Apple Silicon MLX (Medium)](https://medium.com/@andradeolivier/i-ported-musicgen-to-apple-silicon-generate-music-from-text-on-your-macbook-9eaf95992053)
- [DDSP framework — EmergentMind](https://www.emergentmind.com/topics/ddsp-framework) · [Annotation-free MIDI-to-audio (arXiv)](https://arxiv.org/pdf/2410.16785) · [MIDI→waveform high-quality (Nature 2025)](https://www.nature.com/articles/s41598-025-17410-6) · [Expressive drum-grid synthesis (arXiv)](https://arxiv.org/html/2605.10281v1)
