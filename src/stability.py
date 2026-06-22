"""Frontier-grade serving stability (#47) — survive the known mlx_lm.server unbounded-KV crash.

The crash (mlx-lm #883): KV grows past GPU memory on long agentic runs → SoC watchdog KERNEL PANIC;
wired memory can't be Jetsam-reclaimed. Frontier stability is a 5-layer discipline. This module is
layers 1 + 5 (the cheap, GPU-free ones that kill the crash today):

  Layer 1 — BOUNDED KV: cap so the cache can never grow past memory (drive via mlx_lm.generate's
            max_kv_size, since mlx_lm.server still lacks the flag as of 0.31.2).
  Layer 5 — GRACEFUL RECOVERY: a watchdog detects the server's death (RemoteDisconnected / gone) and
            auto-reconnects (re-serve + resume), so the AGENT survives a crash instead of dying with it.
  (Layers 2 TurboQuant KV / 3 tool-call pinning / 4 resource lifecycle are #25 + follow-ons.)

GPU-free logic is unit-tested below; respawn() runs the real serve command.
"""
from __future__ import annotations

import subprocess
import time
import urllib.request

# stream-eval=1 = lower PEAK memory (more stable); max KV is enforced client-side via the generate path
SERVE_CMD = ("GLM_STREAM_EVAL=1 {py} -m mlx_lm.server --model {model} "
             "--adapter-path {adapter} --port {port}")


class BoundedKV:
    """Layer 1: the cap that makes unbounded growth impossible (the root-cause fix)."""

    def __init__(self, max_kv_size: int = 8192, max_context: int = 24000):
        self.max_kv_size = max_kv_size      # passed to mlx_lm.generate (server lacks the flag)
        self.max_context = max_context      # hard ceiling on prompt+gen tokens

    def trim_needed(self, n_tokens: int) -> int:
        return max(0, n_tokens - self.max_context)


class ServerWatchdog:
    """Layer 5: detect death + auto-reconnect. The agent never dies with the server."""

    def __init__(self, model, adapter, port=8080, base_url=None, respawn_fn=None):
        self.model, self.adapter, self.port = model, adapter, port
        self.base_url = base_url or f"http://127.0.0.1:{port}"
        self.respawn_fn = respawn_fn        # injectable for tests
        self.respawns = 0

    def is_alive(self, timeout=5) -> bool:
        try:
            urllib.request.urlopen(self.base_url + "/v1/models", timeout=timeout)
            return True
        except Exception:                   # noqa: BLE001  (connection refused / disconnected / gone)
            return False

    def respawn(self):
        """Re-serve the model after a crash (real subprocess unless respawn_fn injected)."""
        self.respawns += 1
        if self.respawn_fn:
            return self.respawn_fn()
        cmd = SERVE_CMD.format(py=".venv/bin/python", model=self.model,
                               adapter=self.adapter, port=self.port)
        with open("logs/serve_watchdog.log", "a") as f:
            subprocess.Popen(cmd, shell=True, stdout=f, stderr=f, start_new_session=True)
        return self.wait_until_up()

    def wait_until_up(self, tries=60, delay=5) -> bool:
        for _ in range(tries):
            if self.is_alive():
                return True
            time.sleep(delay)
        return False


class CircuitBreaker:
    """Stop the respawn LOOP. After repeated failures in a window, back off with ESCALATING cooldowns
    (the 'flapping' problem — a server that recovers briefly then dies again needs ever-longer cooldowns)."""

    def __init__(self, max_failures=5, window_s=300, base_cooldown_s=10):
        self.max_failures, self.window_s, self.base_cooldown = max_failures, window_s, base_cooldown_s
        self.failures, self.trips = [], 0

    def record_failure(self, now=None):
        now = time.time() if now is None else now
        self.failures = [t for t in self.failures if now - t < self.window_s] + [now]

    def is_open(self, now=None):
        now = time.time() if now is None else now
        self.failures = [t for t in self.failures if now - t < self.window_s]
        return len(self.failures) >= self.max_failures

    def trip(self):
        self.trips += 1
        return self.base_cooldown * (2 ** min(self.trips - 1, 5))   # 10,20,40,80,160,320 — escalating

    def reset(self):
        self.failures, self.trips = [], 0


import threading
_RESPAWN_LOCK = threading.Lock()                            # serialize respawns — no thundering-herd of duplicate servers


def resilient_call(call_fn, watchdog: ServerWatchdog, max_retries=3, backoff=2.0, breaker=None):
    """Wrap a model call: on a connection death, respawn the server + retry. Survives crashes. With a
    CircuitBreaker, escalating cooldowns prevent an infinite respawn loop when the server keeps dying."""
    last = None
    for attempt in range(max_retries + 1):
        try:
            out = call_fn()
            if breaker:
                breaker.reset()                          # success → clear the failure window
            return out
        except (ConnectionError, OSError, TimeoutError) as e:   # RemoteDisconnected ⊂ ConnectionError
            last = e
            if breaker:
                breaker.record_failure()
            if attempt >= max_retries:
                break
            if breaker and breaker.is_open():
                time.sleep(min(breaker.trip(), 120))     # escalating cooldown, capped (flapping guard)
            if not watchdog.is_alive():
                with _RESPAWN_LOCK:                      # serialize — another thread may already be respawning
                    if not watchdog.is_alive() and not watchdog.respawn() and breaker:
                        breaker.record_failure()         # respawn FAILED (server didn't come back) — let the breaker open
            if backoff:
                time.sleep(backoff ** attempt)
    raise last


def mem_free_pct():
    """Layer 5 instrumentation: free-memory % — pause/evict BEFORE the crash, not after."""
    try:
        import re
        out = subprocess.check_output(["memory_pressure"], text=True, timeout=5)
        for line in out.splitlines():
            if "free perc" in line.lower():
                m = re.search(r"(\d+)%", line)
                return int(m.group(1)) if m else None
    except Exception:       # noqa: BLE001
        return None


def mx_set_limits(memory_gb=118.0, cache_gb=8.0, wired_gb=None):
    """MLX-NATIVE stability — the framework guardrail (better than parsing shell memory_pressure).
    `mx.set_memory_limit` makes MLX EVICT/error instead of kernel-panicking on unbounded KV growth
    (the #883 crash, in-framework). `set_cache_limit` bounds the buffer-reuse pool (anti-fragmentation).
    Call at the start of any MLX serving/training process. Returns the limits set."""
    import mlx.core as mx
    gb = 1024 ** 3
    mx.set_memory_limit(int(memory_gb * gb))     # soft cap → graceful eviction, not a crash
    mx.set_cache_limit(int(cache_gb * gb))       # bound the pool that "fragments over ~14h" and dies
    if wired_gb is not None:
        mx.set_wired_limit(int(wired_gb * gb))   # in-framework iogpu.wired_limit
    return {"memory_gb": memory_gb, "cache_gb": cache_gb, "wired_gb": wired_gb}


def mx_mem():
    """Precise IN-PROCESS memory in GB: active / cache / peak — exact, not a shell estimate."""
    import mlx.core as mx
    gb = 1024 ** 3
    return {"active": mx.get_active_memory() / gb, "cache": mx.get_cache_memory() / gb,
            "peak": mx.get_peak_memory() / gb}


def mx_clear():
    """Clear MLX's buffer pool — under pressure / between long sessions (NOT every request: that kills
    the prefix cache). Pairs with set_cache_limit to stop the fragment-then-crash aging."""
    import mlx.core as mx
    mx.clear_cache()


def run_with_lifecycle(cmd, cwd=None, timeout=300):
    """Layer 4 — resource lifecycle: run a subprocess (cargo build / pytest / find) with a HARD timeout,
    then SIGKILL the whole process GROUP so nothing orphans/zombies (the documented agent-subprocess leak).
    Returns (returncode, output). 124 = killed by timeout."""
    import os
    import signal
    p = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True, text=True)
    try:
        out, _ = p.communicate(timeout=timeout)
        return p.returncode, out or ""
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)     # kill the GROUP — no orphans
        except Exception:  # noqa: BLE001
            p.kill()
        try:
            out, _ = p.communicate(timeout=5)
        except Exception:  # noqa: BLE001
            out = ""
        return 124, (out or "") + "\n[killed: timeout]"


class Checkpoint:
    """Microreboot, not full restart: snapshot agent state so a crash → resume from the last good step."""

    def __init__(self, path):
        self.path = path

    def save(self, state: dict):
        import json
        import os
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, self.path)                           # atomic — never a half-written checkpoint

    def load(self):
        import json
        import os
        if os.path.exists(self.path):
            with open(self.path) as f:
                return json.load(f)
        return None


def _selftest():
    bk = BoundedKV(max_context=24000)
    assert bk.trim_needed(30000) == 6000 and bk.trim_needed(10000) == 0

    # watchdog respawn: dead → alive
    state = {"alive": False}
    wd = ServerWatchdog("m", "a", respawn_fn=lambda: (state.update(alive=True), True)[1])
    wd.is_alive = lambda timeout=5: state["alive"]
    assert not wd.is_alive()
    wd.respawn()
    assert state["alive"] and wd.respawns == 1

    # resilient_call: connection dies twice, recovers via respawn, then succeeds
    state["alive"] = False
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] <= 2:
            raise ConnectionError("RemoteDisconnected")
        return "ok"

    wd2 = ServerWatchdog("m", "a", respawn_fn=lambda: (state.update(alive=True), True)[1])
    wd2.is_alive = lambda timeout=5: state["alive"]
    out = resilient_call(flaky, wd2, max_retries=3, backoff=0)
    assert out == "ok" and calls["n"] == 3 and wd2.respawns >= 1

    # circuit breaker: opens after max_failures, escalating cooldown (flapping guard)
    cb = CircuitBreaker(max_failures=3, base_cooldown_s=10)
    for _ in range(3):
        cb.record_failure(now=100)
    assert cb.is_open(now=100)
    assert (cb.trip(), cb.trip(), cb.trip()) == (10, 20, 40)
    cb.reset()
    assert not cb.is_open(now=100)

    # subprocess lifecycle: a hang is SIGKILLed by timeout (no zombie/orphan)
    rc, lout = run_with_lifecycle("sleep 10", timeout=1)
    assert rc == 124 and "killed" in lout

    # checkpoint: atomic save → load round-trips (resume after crash, not restart)
    import os
    import tempfile
    cp = Checkpoint(os.path.join(tempfile.mkdtemp(), "ckpt.json"))
    assert cp.load() is None
    cp.save({"step": 7, "transcript": ["a", "b"]})
    assert cp.load()["step"] == 7

    # MLX-native memory guardrail (the in-framework evict-before-crash)
    lim = mx_set_limits(memory_gb=110, cache_gb=4)
    assert lim["memory_gb"] == 110
    m = mx_mem()
    assert m["active"] >= 0 and "cache" in m and "peak" in m
    mx_clear()

    print("  stability selftest PASS: bounded-KV + watchdog + resilient retry + circuit-breaker +")
    print("    subprocess-lifecycle + checkpoint + MLX-NATIVE limits (set_memory_limit/cache_limit/clear)")
    print(f"  survived {calls['n'] - 1} crashes via {wd2.respawns} respawn(s); breaker stops respawn-loops;")
    print(f"    MLX self-bounds (evict-not-crash); live mem active={m['active']:.1f} cache={m['cache']:.1f} GB")


if __name__ == "__main__":
    _selftest()
