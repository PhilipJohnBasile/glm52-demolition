"""Serve supervisor — the self-healing layer the ecosystem was missing.

serve_stable.py just launches mlx_lm.server with a memory guard; it does NOT come back after a crash. The
serve died ~4× in one session (disk-full, a bad env flag, concurrent OOM) and each needed a MANUAL restart
— so an overnight flywheel/re-heal would silently die. This supervisor wraps serve_stable: it health-checks
the endpoint, and on a crash (process gone) OR a hang (alive but unresponsive) it kills + relaunches with
exponential backoff, logging every event. Forward ALL serve_stable args through.

  HF_HUB_OFFLINE=1 MLX_MEM_GB=112 nohup python scripts/serve_supervisor.py \
      --model models/GLM-5.2-q3a4-v2 --adapter-path heal/adapters-recover --port 8080 \
      --temp 0.6 --top-p 0.95 --prompt-cache-size 4 > /tmp/SUPERVISOR.log 2>&1 &
"""
import subprocess
import sys
import time
import urllib.request


def healthy(port, timeout=20):
    try:
        urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=timeout)
        return True
    except Exception:
        return False


def log(msg):
    print(f"[supervisor] {msg}", flush=True)


def main():
    argv = sys.argv[1:]
    port = argv[argv.index("--port") + 1] if "--port" in argv else "8080"
    backoff = 5
    proc = None
    restarts = 0
    while True:
        # (re)launch if not running
        if proc is None or proc.poll() is not None:
            if proc is not None:
                log(f"serve exited (rc={proc.returncode}) — restart #{restarts + 1} in {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 120)
                restarts += 1
            log(f"launching serve_stable ({' '.join(argv)})")
            proc = subprocess.Popen([sys.executable, "scripts/serve_stable.py"] + argv)
            up = False
            for _ in range(72):                       # up to ~6 min for the 99GB load
                time.sleep(5)
                if proc.poll() is not None:            # died during load
                    break
                if healthy(port):
                    log("serve healthy ✅")
                    backoff = 5
                    up = True
                    break
            if not up and proc.poll() is None:
                log("serve never became healthy after load window — killing to retry")
                proc.terminate(); time.sleep(5)
                if proc.poll() is None:
                    proc.kill()
                proc = None
                continue
        # NOTE: restart-on-DEATH only. We deliberately do NOT health-check a live process: mlx_lm.server
        # is single-threaded, so during a long generation it can't answer /v1/models — a health check
        # would false-positive "hung" and kill the serve mid-request (caused RemoteDisconnected). Process
        # death (OOM, disk-full, crash) is what we actually recover from, and poll() catches that reliably.
        time.sleep(15)


if __name__ == "__main__":
    main()
