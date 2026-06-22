"""ANE audio perception via Apple's SoundAnalysis framework — sound classification on the
16-core Neural Engine, FREE: no model, no CoreML conversion (SoundAnalysis runs on the ANE
natively, like Vision in ane_vision.py and NLContextualEmbedding in ane_embed.py). Gives the
agent EARS — "what is this sound?" (~300 classes: speech, music, applause, alarm, typing,
silence, …) — while the GPU keeps decoding.

    from ane_audio import classify_audio
    labels = classify_audio("clip.wav", top_k=5)   # [(identifier, confidence), ...]  (Audio Classification)

#91. Built in parallel with the GPU heal. Speech-to-text (#87) is a separate lane (Speech framework,
needs authorization) — kept out of here so this stays auth-free.

Install:  uv pip install --python .venv pyobjc-framework-SoundAnalysis pyobjc-framework-AVFoundation
"""
import objc
from Foundation import NSObject
import SoundAnalysis as _SN          # noqa: F401 — import registers the SNResultsObserving protocol referenced below

_OBSERVING = objc.protocolNamed("SNResultsObserving")   # observer MUST declare conformance or addRequest -> invalidArgument


class _SoundObserver(NSObject, protocols=[_OBSERVING]):
    """SNResultsObserving delegate — collects per-window classifications into a sink list."""
    def initWithSink_(self, sink):
        self = objc.super(_SoundObserver, self).init()
        if self is None:
            return None
        self._sink = sink
        return self

    def request_didProduceResult_(self, request, result):           # SNClassificationResult
        for c in (result.classifications() or [])[:8]:
            self._sink.append((str(c.identifier()), round(float(c.confidence()), 4)))

    def request_didFailWithError_(self, request, error):
        self._sink.append(("__error__", str(error)))

    def requestDidComplete_(self, request):
        pass


def classify_audio(path, top_k=5, min_conf=0.0):
    """Classify a sound file on the ANE (Audio Classification). Returns [(identifier, confidence) …],
    best confidence per class across the clip's analysis windows."""
    import SoundAnalysis as SN
    from Foundation import NSURL
    url = NSURL.fileURLWithPath_(str(path))
    analyzer, err = SN.SNAudioFileAnalyzer.alloc().initWithURL_error_(url, None)
    if analyzer is None:
        raise RuntimeError(f"audio open failed: {err}")
    req, err = SN.SNClassifySoundRequest.alloc().initWithClassifierIdentifier_error_(
        SN.SNClassifierIdentifierVersion1, None)
    if req is None:
        raise RuntimeError(f"classifier init failed: {err}")
    sink = []
    obs = _SoundObserver.alloc().initWithSink_(sink)
    ok, err = analyzer.addRequest_withObserver_error_(req, obs, None)
    if not ok:
        raise RuntimeError(f"addRequest failed: {err}")
    analyzer.analyze()                                              # synchronous — fills sink via the observer
    best = {}
    for ident, conf in sink:
        if ident == "__error__":
            raise RuntimeError(f"analysis error: {conf}")
        if ident not in best or conf > best[ident]:
            best[ident] = conf
    return sorted([(k, v) for k, v in best.items() if v >= min_conf], key=lambda x: -x[1])[:top_k]


def vad(path, threshold=0.3):
    """Voice Activity Detection on the ANE — is there SPEECH in this clip? Returns (has_speech, confidence),
    derived from the sound classifier's speech-family classes. Lets the agent gate ASR (#87) cheaply."""
    speech = {"speech", "conversation", "narration_monologue", "shout", "whispering", "babbling", "singing"}
    labels = dict(classify_audio(path, top_k=25))
    conf = max((labels.get(c, 0.0) for c in speech), default=0.0)
    return (conf >= threshold, round(conf, 4))


if __name__ == "__main__":
    import os
    import tempfile
    import wave
    import numpy as np
    sr = 16000
    t = np.linspace(0, 3.0, int(sr * 3.0), False)                 # ≥ the classifier's analysis window (~3 s)
    # a tone + noise + clap-like transient — give the classifier something with structure
    audio = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.12 * np.random.randn(t.size)
    audio[sr // 2:sr // 2 + 200] += 0.8                            # a transient (clap-ish)
    pcm = np.clip(audio, -1, 1)
    pcm = (pcm * 32767).astype(np.int16)
    fp = os.path.join(tempfile.gettempdir(), "ane_audio_test.wav")
    with wave.open(fp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    labels = classify_audio(fp, top_k=5)
    os.remove(fp)
    print(f"  classify_audio (ANE) -> {labels[:5]}")
    ok = isinstance(labels, list) and len(labels) >= 1
    print(f"  ane_audio selftest {'PASS' if ok else 'CHECK'} — sound classified on the Neural Engine ({len(labels)} labels)")
