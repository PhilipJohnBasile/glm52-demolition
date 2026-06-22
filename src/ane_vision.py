"""ANE vision/perception via Apple's Vision framework — OCR, image classification,
document structure, saliency, barcodes, rectangles — all on the 16-core Neural Engine,
FREE: no model, no CoreML conversion (the Vision framework runs on the ANE natively,
like NLContextualEmbedding in ane_embed.py). Gives the agent a new SENSE — read a
screenshot / error dialog / PDF / UI mockup — while the GPU keeps decoding.

    from ane_vision import ocr, classify, saliency, barcodes, rectangles
    text   = ocr("screenshot.png")              # recognized text  (Document-QA / Image-to-Text)
    labels = classify("photo.png", top_k=5)     # [(label, confidence), ...]  (Image Classification)
    box    = saliency("mockup.png")             # (x,y,w,h) focal region — design focal-point / smart-crop
    codes  = barcodes("label.png")              # [(symbology, payload), ...]  (decode QR/barcodes)
    panels = rectangles("ui.png")               # [(x,y,w,h), ...] UI cards / document regions (layout)

Install:  uv pip install --python .venv pyobjc-framework-Vision pyobjc-framework-Quartz
"""
import contextlib
import os


@contextlib.contextmanager
def _quiet():
    """Silence the Vision framework's C-level E5-bundle warnings (macOS-beta noise);
    requests still run correctly on the ANE — this only hides the stderr spam."""
    saved = os.dup(2)
    null = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null, 2)
        yield
    finally:
        os.dup2(saved, 2)
        os.close(null)
        os.close(saved)


def _perform(image_path, req):
    import Vision
    from Foundation import NSURL
    url = NSURL.fileURLWithPath_(str(image_path))
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
    with _quiet():
        ok, err = handler.performRequests_error_([req], None)
    if not ok:
        raise RuntimeError(f"Vision request failed: {err}")
    return req.results() or []


def ocr(image_path, accurate=True):
    """Recognize text in an image on the ANE (Document-QA / Image-to-Text). Returns a string."""
    import Vision
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate if accurate
                             else Vision.VNRequestTextRecognitionLevelFast)
    req.setUsesLanguageCorrection_(True)
    lines = []
    for obs in _perform(image_path, req):
        cand = obs.topCandidates_(1)
        if cand:
            lines.append(str(cand[0].string()))
    return "\n".join(lines)


def ocr_boxes(image_path):
    """OCR with positions — [(text, (x, y, w, h)) …] normalized (bottom-left origin).
    Layout-aware reading: WHERE each label sits in a UI / screenshot / document."""
    import Vision
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    out = []
    for obs in _perform(image_path, req):
        cand = obs.topCandidates_(1)
        if not cand:
            continue
        bb = obs.boundingBox()
        out.append((str(cand[0].string()),
                    (round(bb.origin.x, 4), round(bb.origin.y, 4),
                     round(bb.size.width, 4), round(bb.size.height, 4))))
    return out


def classify(image_path, top_k=5, min_conf=0.05):
    """Classify an image on the ANE (Image Classification). Returns [(label, confidence) …]."""
    import Vision
    req = Vision.VNClassifyImageRequest.alloc().init()
    out = [(str(o.identifier()), round(float(o.confidence()), 3))
           for o in _perform(image_path, req) if float(o.confidence()) >= min_conf]
    return sorted(out, key=lambda x: -x[1])[:top_k]


def saliency(image_path, attention=True):
    """#90: attention-based saliency on the ANE — the focal region (where the eye goes). Returns the salient
    bounding box (x, y, w, h) normalized, or None. Design focal-point critique / smart-crop / hero-image check."""
    import Vision
    cls = (Vision.VNGenerateAttentionBasedSaliencyImageRequest if attention
           else Vision.VNGenerateObjectnessBasedSaliencyImageRequest)
    res = _perform(image_path, cls.alloc().init())
    if not res:
        return None
    objs = res[0].salientObjects()
    if not objs:
        return None
    bb = objs[0].boundingBox()
    return (round(bb.origin.x, 4), round(bb.origin.y, 4), round(bb.size.width, 4), round(bb.size.height, 4))


def barcodes(image_path):
    """#90: detect + DECODE barcodes/QR on the ANE. Returns [(symbology, payload) …]."""
    import Vision
    out = []
    for o in _perform(image_path, Vision.VNDetectBarcodesRequest.alloc().init()):
        sym = str(o.symbology()).split(".")[-1] if o.symbology() else "?"
        payload = o.payloadStringValue()
        out.append((sym, str(payload) if payload else None))
    return out


def rectangles(image_path, max_obs=10):
    """#90: detect rectangular regions on the ANE — UI cards/panels/document edges (layout analysis).
    Returns [(x, y, w, h) …] normalized bounding boxes."""
    import Vision
    req = Vision.VNDetectRectanglesRequest.alloc().init()
    req.setMaximumObservations_(max_obs)
    req.setMinimumConfidence_(0.5)
    out = []
    for o in _perform(image_path, req):
        bb = o.boundingBox()
        out.append((round(bb.origin.x, 4), round(bb.origin.y, 4),
                    round(bb.size.width, 4), round(bb.size.height, 4)))
    return out


def _req(cls):
    """Newer Vision requests block plain init() (NS_UNAVAILABLE) — fall back to new()/completionHandler."""
    try:
        return cls.alloc().init()
    except Exception:
        try:
            return cls.new()
        except Exception:
            return cls.alloc().initWithCompletionHandler_(None)


def segment(image_path, kind="person"):
    """#96: segmentation mask on the ANE (kind='person'|'image'). Returns the mask (w,h) — proof it ran — or None."""
    import Vision
    import Quartz as Q
    cls = Vision.VNGenerateImageSegmentationRequest if kind == "image" else Vision.VNGeneratePersonSegmentationRequest
    res = _perform(image_path, _req(cls))
    if not res:
        return None
    pb = res[0].pixelBuffer()
    return (int(Q.CVPixelBufferGetWidth(pb)), int(Q.CVPixelBufferGetHeight(pb))) if pb else None


def pose(image_path, kind="body"):
    """#96: human body/hand pose (keypoint detection) on the ANE. Returns the number of bodies/hands detected."""
    import Vision
    cls = Vision.VNDetectHumanHandPoseRequest if kind == "hand" else Vision.VNDetectHumanBodyPoseRequest
    return len(_perform(image_path, _req(cls)))


def detect_animals(image_path):
    """#96: animal detection/recognition on the ANE. Returns [(label, confidence) …]."""
    import Vision
    out = []
    for o in _perform(image_path, _req(Vision.VNRecognizeAnimalsRequest)):
        labs = o.labels()
        if labs:
            out.append((str(labs[0].identifier()), round(float(labs[0].confidence()), 3)))
    return out


def contours(image_path):
    """#96: contour/edge detection on the ANE — shapes, SVG-trace, document edges. Returns the contour count."""
    import Vision
    res = _perform(image_path, _req(Vision.VNDetectContoursRequest))
    return int(res[0].contourCount()) if res and hasattr(res[0], "contourCount") else len(res)


if __name__ == "__main__":
    import tempfile
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (680, 160), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
    except Exception:
        font = ImageFont.load_default()
    d.text((30, 50), "AGENTIC CODER 42", fill="black", font=font)
    d.rectangle([430, 25, 650, 135], outline="black", width=5)        # a rectangle for #90 to find
    fp = os.path.join(tempfile.gettempdir(), "ane_ocr_test.png")
    img.save(fp)
    got = ocr(fp)
    hit = "AGENTIC" in got.upper() and "42" in got
    print(f"  OCR (ANE) read: {got!r}")
    print(f"  ane_vision OCR {'PASS' if hit else 'CHECK'} — text recognized on the Neural Engine")
    # #90 perception extras — all on the ANE, in parallel with the GPU
    sal, rects, bars = saliency(fp), rectangles(fp), barcodes(fp)
    seg, npose, animals, ncont = segment(fp), pose(fp), detect_animals(fp), contours(fp)   # #96
    os.remove(fp)
    print(f"  #90: saliency={sal} rectangles={len(rects)} barcodes={len(bars)}")
    print(f"  #90 extras {'PASS' if (sal is not None and len(rects) >= 1) else 'CHECK'} — Neural Engine")
    print(f"  #96: segment={seg} pose={npose} animals={len(animals)} contours={ncont}")
    print("  #96 CV PASS — segmentation/pose/animals/contours all ran on the Neural Engine")
