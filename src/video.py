"""Video understanding — local, by composition (no cloud video model):
extract keyframes (opencv) -> the VLM (Qwen2.5-VL) describes each -> optional Whisper on the
audio track. Turns "see an image" into "understand a clip" with what we already have.
"""
import os


def _frames(video_path, n_frames=6, outdir="/tmp"):
    import cv2
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    if total <= 0:
        cap.release()
        return []
    step = max(1, total // max(1, n_frames))
    paths = []
    for i in range(n_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(i * step, total - 1))
        ok, frame = cap.read()
        if not ok:
            break
        p = os.path.join(outdir, f"_vframe_{i}.jpg")
        cv2.imwrite(p, frame)
        paths.append(p)
    cap.release()
    return paths


def watch(video_path, prompt="Describe what happens in this clip.", n_frames=6, audio=False):
    """Understand a video: sample keyframes, have the VLM describe each, stitch a summary."""
    if not os.path.exists(video_path):
        return f"no such video: {video_path}"
    frames = _frames(video_path, n_frames)
    if not frames:
        return "could not read frames (need opencv + a readable video)"
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from vision import see
    parts = [f"[frame {i} @ ~{i}/{len(frames)}] {see(f, prompt)}" for i, f in enumerate(frames)]
    if audio:                                               # best-effort audio track
        parts.append("[audio] " + transcribe_video(video_path))
    return f"video '{os.path.basename(video_path)}' ({len(frames)} keyframes):\n" + "\n".join(parts)


def transcribe_video(video_path, model="mlx-community/whisper-large-v3-turbo"):
    """Transcribe a video's AUDIO track: extract via the bundled ffmpeg -> Whisper (MLX). Local."""
    if not os.path.exists(video_path):
        return f"no such video: {video_path}"
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # noqa: BLE001
        return f"ffmpeg unavailable (uv pip install imageio-ffmpeg): {str(e)[:80]}"
    import subprocess
    import tempfile
    wav = tempfile.mktemp(suffix=".wav")
    r = subprocess.run([ff, "-y", "-i", video_path, "-ac", "1", "-ar", "16000", wav],
                       capture_output=True, timeout=300)
    if not os.path.exists(wav):
        return f"audio extract failed: {r.stderr.decode()[:200]}"
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from audio import transcribe
    return transcribe(wav, model)


def selftest():
    """GPU-free: synthesize a tiny clip + confirm frame extraction (VLM tested live)."""
    try:
        import cv2
        import numpy as np
        p = "/tmp/_test_clip.mp4"
        vw = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*"mp4v"), 5, (64, 64))
        for k in range(10):
            vw.write((np.ones((64, 64, 3), np.uint8) * (k * 25)))
        vw.release()
        n = len(_frames(p, 4))
        ok = n >= 1
    except Exception as e:  # noqa: BLE001
        print(f"  video selftest: FAIL ({str(e)[:80]})")
        return False
    print(f"  video selftest: extracted {n} keyframes  {'PASS ✅' if ok else 'FAIL'}  "
          "(VLM describes them live)")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
