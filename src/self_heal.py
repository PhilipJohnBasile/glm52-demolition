"""Self-healing flywheel — the model improves from its OWN verified runs, forever, locally (MLX-native).

Unifies verifier-mesh self-training (#26) + the hard-negative flywheel (#16) + expert-iteration (#28) +
Continual Harness into one autonomous engine:

    generate (mlx_lm.server) → verify (the mesh) → verified ⇒ train pool, failed ⇒ hard-neg pool
    → when the train pool is big enough, SFT (06_heal_lora QLoRA) → reload → repeat, compounding.

No human labels, no cloud — the verifier IS the supervision. GPU-free orchestration logic is unit-tested
here; `run()` drives the live loop (needs the model + the verifier mesh + the SFT hook).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HealStats:
    verified: int = 0           # correct → training data
    hard_neg: int = 0           # failed → targeted harder training
    sfts: int = 0               # heal cycles completed
    history: list = field(default_factory=list)   # verified-rate per heal cycle (should trend UP)

    def verified_rate(self) -> float:
        tot = self.verified + self.hard_neg
        return self.verified / tot if tot else 0.0


@dataclass
class SelfHealLoop:
    gen_fn: object = None        # task -> output            (mlx_lm.server)
    verify_fn: object = None     # output -> bool            (the verifier mesh, in unified memory)
    sft_fn: object = None        # train_pool -> new adapter (06_heal_lora QLoRA)
    sft_threshold: int = 200     # verified examples before a heal cycle
    stats: HealStats = field(default_factory=HealStats)
    train_pool: list = field(default_factory=list)
    hard_neg: list = field(default_factory=list)

    def step(self, task) -> bool:
        """One task → generate, verify, bucket. The atom of self-healing."""
        out = self.gen_fn(task)
        if self.verify_fn(out):
            self.train_pool.append((task, out))
            self.stats.verified += 1
            return True
        self.hard_neg.append((task, out))
        self.stats.hard_neg += 1
        return False

    def ready_to_heal(self) -> bool:
        return len(self.train_pool) >= self.sft_threshold

    def heal(self):
        """SFT on the verified pool — the compounding step. Then the pool resets and the model reloads."""
        adapter = self.sft_fn(self.train_pool) if self.sft_fn else None
        self.stats.sfts += 1
        self.stats.history.append(round(self.stats.verified_rate(), 3))
        self.train_pool = []                 # consumed into the model's weights
        return adapter

    def run(self, tasks):
        """Live compounding loop: step every task, heal whenever the verified pool fills."""
        for t in tasks:
            self.step(t)
            if self.ready_to_heal():
                self.heal()                  # (reload the served model with the new adapter here)
        return self.stats


def _selftest():
    # a fake model that gets BETTER after each heal (verified-rate should climb) — the flywheel working
    state = {"skill": 0.5}

    def gen(task):
        return {"task": task, "skill": state["skill"]}

    def verify(out):                          # correct with prob = current skill (deterministic by task id)
        return (out["task"] * 7919) % 100 < out["skill"] * 100

    def sft(pool):
        state["skill"] = min(1.0, state["skill"] + 0.2)   # healing raises skill
        return f"adapter-{state['skill']:.1f}"

    loop = SelfHealLoop(gen_fn=gen, verify_fn=verify, sft_fn=sft, sft_threshold=30)
    loop.run(range(300))
    s = loop.stats
    assert s.verified + s.hard_neg == 300
    assert s.sfts >= 1, "should have healed at least once"
    # the verified-rate history should be non-empty and trend upward as the model self-heals
    assert s.history and s.history[-1] >= s.history[0], s.history
    print(f"  self_heal selftest PASS (GPU-free): 300 tasks → {s.verified} verified / {s.hard_neg} hard-neg")
    print(f"  {s.sfts} heal cycles; verified-rate trend {s.history} (compounding upward = the flywheel works)")
    print("  wire gen_fn=mlx_lm.server, verify_fn=the mesh, sft_fn=06_heal_lora → live autonomous self-healing")


if __name__ == "__main__":
    _selftest()
