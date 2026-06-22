"""Media-Engine flywheel — keeps the M5 MEDIA ENGINE (VideoToolbox H.264 encode) lit for a time budget,
alongside the GPU heal chain + the CPU/ANE flywheel. Each round: generate frames -> hardware-encode to mp4
(#88b). Encode-only (the decode path is memory-contended under a heal — measured 189s); the encoder is its
own Media-Engine block and stays fast. Self-contained; never converges.

  python src/media_flywheel.py --hours 12
"""
import argparse
import os
import sys
import tempfile
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--report", type=int, default=200)
    a = ap.parse_args()
    from media_encode import encode_frames
    fp = os.path.join(tempfile.gettempdir(), "media_flyw.mp4")
    h, w = 240, 320
    ygrad = np.linspace(0, 255, h).astype(np.uint8)[:, None]
    xgrad = np.linspace(0, 255, w).astype(int)[None, :]
    deadline = time.time() + a.hours * 3600
    rounds = enc = 0
    while time.time() < deadline:
        rounds += 1
        frames = []
        for i in range(24):
            f = np.zeros((h, w, 3), np.uint8)
            f[..., 0] = ((xgrad + i * 10) % 256).astype(np.uint8)
            f[..., 1] = ygrad
            frames.append(f)
        enc += encode_frames(frames, fp, fps=24)                    # Media Engine H.264 encode
        if rounds % a.report == 0:
            print(f"  round {rounds}: {enc} frames encoded on the Media Engine, "
                  f"{(deadline - time.time()) / 3600:.2f}h left", flush=True)
    if os.path.exists(fp):
        os.remove(fp)
    print(f"  media-flywheel done: {enc} frames encoded, {rounds} rounds")


if __name__ == "__main__":
    main()
