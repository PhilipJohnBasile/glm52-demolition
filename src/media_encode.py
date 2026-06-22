"""Hardware video ENCODE via the M5 MEDIA ENGINE (AVAssetWriter / VideoToolbox) — write numpy frames to an
H.264/HEVC mp4 on the dedicated video-codec silicon, off GPU+CPU. The encode half of #88 (which decodes).
Gives #44 video-gen + screen-recording a hardware output path.

    from media_encode import encode_frames
    encode_frames(frames_rgb, "out.mp4", fps=24)   # frames_rgb: list of HxWx3 uint8 RGB numpy arrays

#88b. Built parallel with the GPU heal.
"""
import numpy as np


def encode_frames(frames, out_mp4, fps=24, codec="h264"):
    """Encode HxWx3 uint8 RGB frames to mp4 on the Media Engine. Returns the number of frames written."""
    import os
    import AVFoundation as AV
    import CoreMedia as CM
    import Quartz as Q
    from Foundation import NSURL, NSRunLoop, NSDate
    if os.path.exists(out_mp4):
        os.remove(out_mp4)
    h, w = frames[0].shape[:2]
    writer, err = AV.AVAssetWriter.alloc().initWithURL_fileType_error_(
        NSURL.fileURLWithPath_(str(out_mp4)), AV.AVFileTypeMPEG4, None)
    if writer is None:
        raise RuntimeError(f"writer init failed: {err}")
    vcodec = AV.AVVideoCodecTypeHEVC if codec == "hevc" else AV.AVVideoCodecTypeH264
    settings = {AV.AVVideoCodecKey: vcodec, AV.AVVideoWidthKey: w, AV.AVVideoHeightKey: h}
    inp = AV.AVAssetWriterInput.alloc().initWithMediaType_outputSettings_(AV.AVMediaTypeVideo, settings)
    inp.setExpectsMediaDataInRealTime_(False)
    adaptor = AV.AVAssetWriterInputPixelBufferAdaptor.alloc()\
        .initWithAssetWriterInput_sourcePixelBufferAttributes_(inp, None)
    writer.addInput_(inp)
    writer.startWriting()
    writer.startSessionAtSourceTime_(CM.CMTimeMake(0, fps))
    rl = NSRunLoop.currentRunLoop()
    n = 0
    for i, fr in enumerate(frames):
        rc, pb = Q.CVPixelBufferCreate(None, w, h, Q.kCVPixelFormatType_32BGRA, None, None)
        if rc != 0:
            continue
        Q.CVPixelBufferLockBaseAddress(pb, 0)
        base = Q.CVPixelBufferGetBaseAddress(pb)
        bpr = Q.CVPixelBufferGetBytesPerRow(pb)
        bgra = np.empty((h, w, 4), np.uint8)                       # RGB -> BGRA (the pixel format)
        bgra[..., 0], bgra[..., 1], bgra[..., 2], bgra[..., 3] = fr[..., 2], fr[..., 1], fr[..., 0], 255
        mv = memoryview(base.as_buffer(h * bpr))
        for row in range(h):                                       # row-by-row (bpr may be padded > w*4)
            mv[row * bpr:row * bpr + w * 4] = bgra[row].tobytes()
        Q.CVPixelBufferUnlockBaseAddress(pb, 0)
        while not inp.isReadyForMoreMediaData():
            rl.runMode_beforeDate_("kCFRunLoopDefaultMode", NSDate.dateWithTimeIntervalSinceNow_(0.01))
        adaptor.appendPixelBuffer_withPresentationTime_(pb, CM.CMTimeMake(i, fps))
        n += 1
    inp.markAsFinished()
    done = [False]
    writer.finishWritingWithCompletionHandler_(lambda: done.__setitem__(0, True))
    for _ in range(250):
        if done[0]:
            break
        rl.runMode_beforeDate_("kCFRunLoopDefaultMode", NSDate.dateWithTimeIntervalSinceNow_(0.02))
    return n


if __name__ == "__main__":
    import os
    import sys
    import tempfile
    h, w = 240, 320
    frames = []
    for i in range(30):
        fr = np.zeros((h, w, 3), np.uint8)
        fr[..., 0] = ((np.linspace(0, 255, w).astype(int)[None, :] + i * 8) % 256).astype(np.uint8)
        fr[..., 1] = np.linspace(0, 255, h).astype(np.uint8)[:, None]
        frames.append(fr)
    fp = os.path.join(tempfile.gettempdir(), "media_enc_test.mp4")
    n = encode_frames(frames, fp, fps=24)
    size = os.path.getsize(fp) if os.path.exists(fp) else 0
    sys.path.insert(0, os.path.dirname(__file__))
    from media_decode import video_info
    info = video_info(fp) if size else {}
    if os.path.exists(fp):
        os.remove(fp)
    print(f"  encoded {n} frames -> {size} bytes mp4 (Media Engine)")
    print(f"  round-trip decode: {info}")
    ok = n == 30 and size > 1000 and info.get("width") == w
    print(f"  media_encode selftest {'PASS' if ok else 'CHECK'} — video ENCODED on the Media Engine (off-GPU)")
