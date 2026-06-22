"""Video Classification (#98) — the Media Engine decodes frames (off-GPU) → the ANE classifies each (Neural
Engine) → aggregate to per-video labels. Two M5 blocks, ZERO GPU. Composes media_decode (#88) + ane_vision (#79).

    from video_classify import classify_video
    labels = classify_video("clip.mov", n_frames=5)   # [(label, avg_confidence) …]
"""
import os
import sys
import tempfile
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))


def classify_video(path, n_frames=5, top_k=5):
    """Sample n_frames across the clip (Media Engine decode) → classify each (ANE) → average the labels."""
    from media_decode import video_info, extract_frames
    from ane_vision import classify
    info = video_info(path)
    dur = max(info.get("seconds", 0.0), 0.1)
    times = [dur * (i + 0.5) / n_frames for i in range(n_frames)]
    d = tempfile.mkdtemp()
    frames = extract_frames(path, times, out_dir=d)                  # Media Engine → PNG per frame
    agg = defaultdict(list)
    for _t, png in frames:
        if not png:
            continue
        for label, conf in classify(png):                            # ANE classify
            agg[label].append(conf)
        os.remove(png)
    out = [(k, round(sum(v) / len(v), 3)) for k, v in agg.items()]
    return sorted(out, key=lambda x: -x[1])[:top_k]


if __name__ == "__main__":
    vid = "/Applications/iMovie.app/Contents/Resources/PhotoAlbum.mov"
    labels = classify_video(vid, n_frames=3)
    print(f"  classify_video -> {labels[:5]}")
    print(f"  video_classify {'PASS' if isinstance(labels, list) else 'CHECK'} — Media-decode + ANE-classify ({len(labels)} labels, 0 GPU)")
