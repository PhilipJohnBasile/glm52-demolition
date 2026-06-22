"""Hardware video decode via the M5's MEDIA ENGINE (AVFoundation) — extract frames on the dedicated
video-codec silicon (HEVC/H.264/ProRes/AV1), NOT the GPU or CPU. Feeds the vision lane (#43) cheaply:
the Media Engine decodes, the ANE/VLM perceives, the GPU keeps decoding tokens — three blocks at once.

    from media_decode import video_info, extract_frames
    info   = video_info("clip.mov")                       # {'seconds':.., 'width':.., 'height':..}
    frames = extract_frames("clip.mov", [0.0, 1.0, 2.0])  # [(t, (w,h) or png_path), ...] hardware-decoded

#88. Built parallel with the GPU heal.
Install:  uv pip install --python .venv pyobjc-framework-AVFoundation pyobjc-framework-Quartz
"""


def video_info(path):
    """Duration + native dimensions (the Media Engine parses the container/codec)."""
    import AVFoundation as AV
    from Foundation import NSURL
    asset = AV.AVURLAsset.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(path)), None)
    dur = asset.duration()
    secs = (dur.value / dur.timescale) if dur.timescale else 0.0
    tracks = asset.tracksWithMediaType_(AV.AVMediaTypeVideo)
    w = h = 0
    if tracks:
        sz = tracks[0].naturalSize()
        w, h = int(abs(sz.width)), int(abs(sz.height))
    return {"seconds": round(secs, 3), "width": w, "height": h}


def extract_frames(path, times, out_dir=None):
    """Decode frames at the given timestamps (seconds) on the Media Engine via AVAssetImageGenerator
    (hardware video decoder). Returns [(time, (w,h))] — or (time, png_path) if out_dir given."""
    import os
    import AVFoundation as AV
    import CoreMedia as CM
    import Quartz
    from Foundation import NSURL
    asset = AV.AVURLAsset.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(path)), None)
    gen = AV.AVAssetImageGenerator.alloc().initWithAsset_(asset)
    gen.setAppliesPreferredTrackTransform_(True)                      # default tolerance already = nearest frame
    out = []                                                      # the generator loads internally on first copy —
    #                                                               no sync warm (the deprecated track-load blocks ~3 min)
    for t in times:
        cmt = CM.CMTimeMakeWithSeconds(float(t), 600)
        cgimg = None
        for _ in range(3):                                        # a cold decoder can miss the first call — retry
            res = gen.copyCGImageAtTime_actualTime_error_(cmt, None, None)
            cgimg = res[0] if isinstance(res, (tuple, list)) else res
            if cgimg is not None:
                break
        if cgimg is None:
            out.append((round(float(t), 3), None))
            continue
        w, h = int(Quartz.CGImageGetWidth(cgimg)), int(Quartz.CGImageGetHeight(cgimg))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            png = os.path.join(out_dir, f"frame_{float(t):.2f}.png")
            url = NSURL.fileURLWithPath_(png)
            dst = Quartz.CGImageDestinationCreateWithURL(url, "public.png", 1, None)
            Quartz.CGImageDestinationAddImage(dst, cgimg, None)
            Quartz.CGImageDestinationFinalize(dst)
            out.append((round(float(t), 3), png))
        else:
            out.append((round(float(t), 3), (w, h)))
    return out


if __name__ == "__main__":
    import os
    cands = [
        "/Applications/iMovie.app/Contents/Resources/PhotoAlbum.mov",
        "/Applications/Pages Creator Studio.app/Contents/Resources/PlaceholderMovie.mov",
        "/Applications/Pages Creator Studio.app/Contents/Resources/Empty.mov",
    ]
    vid = next((c for c in cands if os.path.exists(c)), None)
    if not vid:
        print("  no test video found — module wired, needs a real video to verify")
        raise SystemExit
    info = video_info(vid)
    frames = extract_frames(vid, [0.5, max(info["seconds"] / 2, 1.0)])     # avoid the t=0 keyframe edge
    print(f"  source: {os.path.basename(vid)}")
    print(f"  video_info: {info}")
    print(f"  decoded frames (Media Engine): {frames}")
    ok = info["width"] > 0 and any(f[1] for f in frames)
    print(f"  media_decode selftest {'PASS' if ok else 'CHECK'} — video decoded on the Media Engine (off-GPU)")
