# Multimodal lane smoke-test (2026-06-22 02:03) — light lanes (ANE/CPU)

v3 era, HF_HUB_OFFLINE (missing model = needs download, not pulled). Heavy lanes (imagegen/whisper/VLM) deferred to GPU-idle.
```
✅ WORKS            embeddings (ANE)   [[ 6.04021177e-02 -4.19780910e-02 -5.65959550e-02 
✅ WORKS            rerank (ANE)       [('a cat', 0.5411593317985535), ('a dog', 0.520904
✅ WORKS            NLP/NER (ANE)      [('Steve', 'PersonalName'), ('Jobs', 'PersonalName
✅ WORKS            tabular/data       shape=(2, 2)  columns=[a:int64, b:int64]  sample=[
✅ WORKS            RAG tokenize       ['def', 'def', 'foo', 'foo', 'return', 'return', '
✅ WORKS            web search         - Apple silicon
  https://en.wikipedia.org/wiki/Ap
✅ WORKS            TTS (ANE)          15800
```
