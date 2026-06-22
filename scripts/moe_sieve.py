#!/usr/bin/env python3
"""#110 MoE-Sieve scenarios (CPU). Rank LoRA modules by ‖A‖·‖B‖; project size for keeping top-X% experts
with/without also sieving attn LoRA. Answers: can we reach ~500MB? (routing-saliency = GPU calib, TODO)."""
import sys, numpy as np
from safetensors import safe_open
path = sys.argv[1] if len(sys.argv) > 1 else "heal/adapters-soul/adapters.safetensors"
mods = {}
with safe_open(path, framework="numpy") as f:
    for k in f.keys():
        kl = k.lower(); side = "a" if "lora_a" in kl else ("b" if "lora_b" in kl else None)
        if side is None: continue
        base = k.replace(".lora_a","").replace(".lora_A","").replace(".lora_b","").replace(".lora_B","")
        t = f.get_tensor(k); mods.setdefault(base, {})[side] = (t.size*t.itemsize, float(np.linalg.norm(t.astype(np.float32))))
exp, att = [], []
for b,d in mods.items():
    if "a" in d and "b" in d:
        row=(b, d["a"][1]*d["b"][1], d["a"][0]+d["b"][0])
        (exp if ("expert" in b.lower() or ".mlp." in b.lower()) else att).append(row)
exp.sort(key=lambda r:r[1], reverse=True); att.sort(key=lambda r:r[1], reverse=True)
tot=sum(r[2] for r in exp+att)/1e6
print(f"  current: {tot:.0f} MB ({len(exp)} expert, {len(att)} attn modules)")
for ep in (25,10):
    ek=max(1,len(exp)*ep//100); eb=sum(r[2] for r in exp[:ek])/1e6
    for ap,al in ((100,"keep all attn"),(50,"sieve attn→top50%")):
        ak=max(1,len(att)*ap//100); ab=sum(r[2] for r in att[:ak])/1e6
        proj=eb+ab
        print(f"  top-{ep}% experts + {al}: {proj:.0f} MB ({100*proj/tot:.0f}%, −{100*(1-proj/tot):.0f}%)")
