#!/usr/bin/env python3
"""GRPO / RLVR on MLX — RL with VERIFIABLE rewards. The winner-maker: the reward
is our REAL verifier (toolchain tests/types via scripts/30; design findings via
scripts/25), so the model learns to be CORRECT, not to imitate a teacher. This is
the only lever whose ceiling EXCEEDS our base — the way the niche is genuinely won.

Group Relative Policy Optimization (the DeepSeek-R1 method): for each prompt sample
a GROUP of G completions, reward each, use the group's mean reward as the baseline
(no critic, no teacher), and update a LoRA policy by the group-normalized advantage.

128GB-fit: LoRA policy only (base frozen), grad-checkpoint, NO separate teacher or
critic — the verifier IS the reward, so only one model is resident (~88GB). There is
no MLX/TRL GRPO trainer, so this is from scratch. RUN AFTER the SFT heal + baseline
eval; validate on a few iters first.

  python scripts/39_grpo.py --model models/GLM-5.2-q3a4-v2 --resume heal/adapters \
      --group 8 --iters 300 --lr 1e-6 --temp 0.8
"""
import argparse
import importlib.util as iu
import json
import os
import sys

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from exec_check import extract_code  # noqa: E402


def _load(path):
    spec = iu.spec_from_file_location(os.path.basename(path)[:-3], path)
    m = iu.module_from_spec(spec)
    sys.argv = [path]
    spec.loader.exec_module(m)
    return m


def reward(task, text, vr, dc):
    """Verifiable reward in [0,1]. Code: real toolchain pass. Design: fewer
    measured findings. The signal that makes the model correct, not imitative."""
    lang = task.get("lang", "")
    if task.get("kind") == "design" or lang in ("html", "css"):
        try:
            html = dc.extract_html(text)
            issues = dc.critique(html, dc.measure(html, "/tmp/grpo_design.png"))
            return 1.0 / (1.0 + len(issues))
        except Exception:  # noqa: BLE001
            return 0.0
    verify = vr.VERIFIERS.get(lang)
    code = extract_code(text)
    if not verify:
        return 0.3 if code else 0.0
    ok, diag = verify(code or text, task.get("harness", ""))
    if ok is True:
        return 1.0                                   # compiles / typechecks / passes
    if ok is None:
        return 0.3                                   # no toolchain to judge
    if not code:
        return 0.0                                   # produced no code block
    # GRADED: real code that failed -> partial, scaled by how FEW errors remain, so
    # completions differ (variance) even when none fully compile. Format bonus for a
    # clean single fenced block. This is what gives GRPO a usable gradient.
    import re as _re
    nerr = len(_re.findall(r"error", diag, _re.I)) or 1
    return max(0.2, 0.6 - 0.08 * min(nerr, 5)) + (0.05 if text.count("```") == 2 else 0)


def gen(model, tok, prompt_ids, max_tokens, temp):
    """Sample one completion with a KV cache (fast — our make_cache fix makes this
    work for GLM-5.2's DSA cache). Returns the completion token ids."""
    from mlx_lm.models.cache import make_prompt_cache
    cache = make_prompt_cache(model)
    logits = model(mx.array([prompt_ids]), cache=cache)[0, -1]
    out = []
    for _ in range(max_tokens):
        tok_id = (int(mx.random.categorical(logits / temp).item()) if temp > 0
                  else int(mx.argmax(logits).item()))
        if tok_id == tok.eos_token_id:
            break
        out.append(tok_id)
        logits = model(mx.array([[tok_id]]), cache=cache)[0, -1]
    return out


def seq_logp(model, ids, start):
    """Sum log-prob of ids[start:] under the policy (teacher-forced), differentiable
    w.r.t. the LoRA params. The GRPO policy-gradient term."""
    logits = model(mx.array([ids]))[0].astype(mx.float32)      # [T, V]
    logp = nn.log_softmax(logits[start - 1:-1], axis=-1)        # predict ids[start:]
    tgt = mx.array(ids[start:])
    return mx.take_along_axis(logp, tgt[:, None], axis=-1).sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v2")
    ap.add_argument("--resume", default="heal/adapters", help="LoRA to continue from")
    ap.add_argument("--num-layers", type=int, default=6,
                    help="LoRA layers — MUST match the resumed SFT adapter (heal used 6)")
    ap.add_argument("--tasks", default=os.path.join(HERE, "..", "eval", "tasks.jsonl"))
    ap.add_argument("--group", type=int, default=8)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--lr", type=float, default=1e-6)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--out", default="heal/adapters-grpo")
    args = ap.parse_args()

    from mlx_lm import load
    from mlx_lm.tuner.utils import linear_to_lora_layers
    model, tok = load(args.model)
    model.freeze()
    # Match the WORKING SFT heal exactly: default LoRA + gradient checkpointing.
    # grad_checkpoint wraps each layer so its backward recomputes the forward and
    # takes the VJP ONLY w.r.t. the trainable params -> the non-differentiable MoE
    # expert-gather indices (GatherQMM/GatherMM) are treated as constants, so the
    # 'cannot compute gradient wrt indices' crash never happens.
    linear_to_lora_layers(model, args.num_layers, {"rank": 16, "scale": 20.0, "dropout": 0.0})
    from mlx_lm.tuner.trainer import grad_checkpoint
    layers = getattr(model, "layers", None) or model.model.layers
    grad_checkpoint(layers[0])                 # patches the layer class -> all layers
    print("  default LoRA + grad-checkpoint (matches the working SFT path)", flush=True)
    if args.resume and os.path.exists(os.path.join(args.resume, "adapters.safetensors")):
        model.load_weights(os.path.join(args.resume, "adapters.safetensors"), strict=False)
        print(f"  resumed LoRA from {args.resume}")
    vr = _load(os.path.join(HERE, "30_verify_repair.py"))
    dc = _load(os.path.join(HERE, "25_design_critique.py"))
    tasks = [json.loads(l) for l in open(args.tasks)]
    opt = optim.AdamW(learning_rate=args.lr)

    def group_loss(model, prompt_ids, comps, advs):
        # GRPO: maximize sum_i adv_i * logp(comp_i)  -> minimize the negative.
        # Takes `model` positionally so nn.value_and_grad can differentiate the
        # LoRA params (the correct MLX training pattern).
        total = mx.array(0.0)
        for comp, a in zip(comps, advs):
            if not comp:
                continue
            full = prompt_ids + comp
            total = total + a * seq_logp(model, full, len(prompt_ids))
        return -total / max(1, len(comps))

    import random
    from mlx.utils import tree_flatten
    random.seed(0)

    def _save(tag=""):
        os.makedirs(args.out, exist_ok=True)
        mx.save_safetensors(os.path.join(args.out, "adapters.safetensors"),
                            {k: v for k, v in tree_flatten(model.trainable_parameters())})
        json.dump({"fine_tune_type": "lora", "num_layers": args.num_layers,
                   "lora_parameters": {"rank": 16, "scale": 20.0, "dropout": 0.0}},
                  open(os.path.join(args.out, "adapter_config.json"), "w"))  # mlx_lm needs this to LOAD

    for it in range(args.iters):
        if it and it % 15 == 0:                      # checkpoint (overnight-crash-safe)
            _save()
            print(f"  [checkpoint @ iter {it}] -> {args.out}", flush=True)
        task = random.choice(tasks)
        prompt_ids = tok.apply_chat_template(
            [{"role": "user", "content": task["prompt"]}],
            add_generation_prompt=True, tokenize=True)
        comps, rewards = [], []
        for _ in range(args.group):                         # sample the group
            c = gen(model, tok, prompt_ids, args.max_tokens, args.temp)
            comps.append(c)
            rewards.append(reward(task, tok.decode(c), vr, dc))
        r = mx.array(rewards)
        mr = float(r.mean().item())
        npass = sum(x >= 1.0 for x in rewards)
        adv = (r - r.mean()) / (r.std() + 1e-4)             # group-normalized advantage
        if float(r.std().item()) < 1e-6:                    # no variance -> no signal
            print(f"  iter {it}: reward={mr:.2f} pass={npass}/{args.group} "
                  f"[{task.get('lang','?')}] no-variance skip", flush=True)
            continue
        lg = nn.value_and_grad(model, group_loss)
        loss, grad = lg(model, prompt_ids, comps, [float(x) for x in adv])
        opt.update(model, grad)
        mx.eval(model.parameters(), opt.state)
        print(f"  iter {it}: reward={mr:.2f} pass={npass}/{args.group} "
              f"[{task.get('lang','?')}] loss={float(loss.item()):.3f}  <-- UPDATE", flush=True)

    _save()                              # adapters.safetensors + adapter_config.json (loadable)
    print(f"\n  GRPO LoRA -> {args.out}  (verifier-trained; eval vs Fable to confirm the gain)")


if __name__ == "__main__":
    main()
