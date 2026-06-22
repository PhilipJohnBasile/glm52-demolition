"""Humanize — a VERIFIER for prose, the way verifiers.py is for code. It scores AI-slop tells,
learns YOUR voice from YOUR repo (commits/comments/docs — an edge a cloud model can't have), and
emits a per-domain rewrite brief. The model then writes -> score -> rewrite until it reads human
and on-voice. Domains: code comments, commit/PR messages, docs, design/marketing copy, prose.

Intent: craft + voice (no AI-slop, sounds like you) — NOT defeating AI detectors for dishonest use.
"""
import re
import subprocess
from collections import Counter

# The 2026 AI-slop lexicon (the tells everyone recognizes) -------------------------------
_SLOP_WORDS = {
    "delve", "tapestry", "leverage", "utilize", "robust", "seamless", "realm", "landscape",
    "testament", "underscore", "pivotal", "crucial", "vital", "intricate", "multifaceted",
    "holistic", "paradigm", "synergy", "elevate", "embark", "unleash", "unlock", "foster",
    "garner", "bolster", "myriad", "plethora", "nuanced", "comprehensive", "cutting-edge",
    "game-changer", "ever-evolving", "fast-paced", "navigating", "harness", "spearhead",
    "streamline", "supercharge", "transformative", "boasts", "treasure trove",
}
_SLOP_PHRASES = [
    r"in today'?s [\w\- ]+world", r"it'?s (?:worth|important) (?:noting|to note)",
    r"that being said", r"at the end of the day", r"dive (?:in|into|deep)", r"in conclusion",
    r"first and foremost", r"last but not least", r"when it comes to", r"the world of",
    r"not only [\w ]+ but also", r"isn'?t just [\w ]+,? it'?s", r"whether you'?re a",
    r"in the ever-?\w+", r"plays a (?:crucial|key|vital|pivotal) role", r"a wide (?:range|array) of",
]
_SYCOPHANT = [r"\bcertainly!?\b", r"\babsolutely!?\b", r"great question", r"i'?d be happy to",
              r"let'?s (?:dive|explore|take a look)"]
_HEDGE = [r"\bcan\b", r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bpotentially\b", r"\bperhaps\b",
          r"\bgenerally\b", r"\btypically\b", r"\boften\b"]


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def ai_tells(text):
    """Return the AI-slop tells found: words, phrases, sycophancy, and structural markers."""
    t = (text or "")
    low = t.lower()
    tells = {}
    words = [w for w in re.findall(r"[a-z][a-z\-']+", low) if w in _SLOP_WORDS]
    if words:
        tells["slop_words"] = dict(Counter(words))
    ph = [p for p in _SLOP_PHRASES if re.search(p, low)]
    if ph:
        tells["slop_phrases"] = ph
    syc = [p for p in _SYCOPHANT if re.search(p, low)]
    if syc:
        tells["sycophancy"] = syc
    em = t.count("—") + t.count(" - ")
    if em >= 3:
        tells["em_dash_overuse"] = em
    # tricolon / rule-of-three ("x, y, and z") overuse
    tri = len(re.findall(r"\w+, \w+,? and \w+", low))
    if tri >= 3:
        tells["tricolon_overuse"] = tri
    sents = _sentences(t)
    if len(sents) >= 4:
        lens = [len(s.split()) for s in sents]
        mean = sum(lens) / len(lens)
        var = sum((x - mean) ** 2 for x in lens) / len(lens)
        if var < 9:                                          # uniform length = robotic (low burstiness)
            tells["low_burstiness"] = round(var, 1)
    hedges = sum(len(re.findall(p, low)) for p in _HEDGE)
    if sents and hedges / max(1, len(sents)) > 1.2:
        tells["hedging"] = hedges
    return tells


def humanize_score(text):
    """0-100: how human it reads (100 = human, low = AI-slop). Returns (score, tells)."""
    tells = ai_tells(text)
    penalty = (sum(sum(v.values()) for v in tells.values() if isinstance(v, dict)) * 6
               + sum(len(v) for v in tells.values() if isinstance(v, list)) * 7
               + sum(8 for k in tells if k in ("em_dash_overuse", "low_burstiness", "tricolon_overuse", "hedging")))
    return max(0, 100 - penalty), tells


def voice_profile(samples):
    """Learn a writing voice from samples (the user's commits/comments/docs)."""
    text = "\n".join(samples) if isinstance(samples, list) else (samples or "")
    sents = _sentences(text)
    lens = [len(s.split()) for s in sents] or [0]
    words = re.findall(r"[a-z']+", text.lower())
    return {
        "avg_sentence_len": round(sum(lens) / len(lens), 1),
        "burstiness": round((max(lens) - min(lens)) if lens else 0, 1),
        "contractions": round(len(re.findall(r"\b\w+'\w+", text)) / max(1, len(sents)), 2),
        "vocab_richness": round(len(set(words)) / max(1, len(words)), 2),
        "lowercase_starts": round(sum(1 for s in sents if s[:1].islower()) / max(1, len(sents)), 2),
        "exclaims": text.count("!"), "samples": len(sents),
    }


def learn_voice_from_repo(repo="."):
    """YOUR voice from YOUR repo — git commit subjects + bodies (the cloud-can't-have edge)."""
    try:
        p = subprocess.run(["git", "-C", repo, "log", "--no-merges", "-n", "120",
                            "--pretty=%s%n%b"], capture_output=True, text=True, timeout=30)
        msgs = [ln for ln in p.stdout.splitlines() if ln.strip()]
    except Exception:  # noqa: BLE001
        msgs = []
    return voice_profile(msgs) if msgs else {"note": "no git history — pass samples to voice_profile"}


_DOMAIN = {
    "code": "Terse senior-dev comments. Explain WHY, never restate WHAT the code obviously does. No "
            "'This function...'. Lowercase ok. Delete any comment a good reader wouldn't need.",
    "commit": "Imperative mood ('add', 'fix', not 'added'/'fixes'). One-line subject <60 chars + a "
              "why-focused body. No marketing words. No emoji unless the repo uses them.",
    "pr": "What changed + why + how to verify. Concrete. No 'This PR seamlessly...'. Plain.",
    "docs": "Scannable, concrete, zero fluff. Cut every intro sentence that says nothing. Examples > "
            "adjectives. No 'In this guide we will'. Short sentences mixed with long ones.",
    "design": "A designer's voice — specific and opinionated. Name the choice and the reason "
              "(contrast, rhythm, hierarchy). No buzzwords (elevate/seamless/curated/bespoke).",
    "prose": "Vary sentence length (burstiness). Concrete nouns + strong verbs. Cut hedging and "
             "filler. One idea per sentence. Sound like a person who knows the subject.",
}


def humanize_brief(text, domain="prose", voice=None):
    """The rewrite brief: the tells to kill + the domain voice + (optionally) the user's voice."""
    score, tells = humanize_score(text)
    lines = [f"HUMAN-SCORE {score}/100 (higher = more human).", _DOMAIN.get(domain, _DOMAIN["prose"])]
    if tells:
        lines.append("Kill these AI tells: " + "; ".join(
            f"{k}={v}" for k, v in tells.items()))
    if voice:
        lines.append("Match THIS voice: avg sentence ~"
                     f"{voice.get('avg_sentence_len')} words, burstiness {voice.get('burstiness')}, "
                     f"contractions {voice.get('contractions')}, exclaims {voice.get('exclaims')}.")
    lines.append("Rewrite to score >=85 without losing meaning. Don't add new claims.")
    return "\n".join(lines)


def selftest():
    sloppy = ("In today's fast-paced world, it's worth noting that we leverage robust, cutting-edge "
              "solutions. Furthermore, this seamless paradigm will elevate and unlock synergy. "
              "Whether you're a beginner or a pro, dive in.")
    human = ("The parser was slow because it re-read the file on every token. I cached the buffer. "
             "Now it's about 4x faster on the big inputs. Tests still pass.")
    s_lo, _ = humanize_score(sloppy)
    s_hi, _ = humanize_score(human)
    brief = humanize_brief(sloppy, "docs")
    vp = voice_profile([human])
    ok = s_lo < 60 and s_hi > 80 and "HUMAN-SCORE" in brief and "avg_sentence_len" in vp
    print(f"  humanize selftest: slop={s_lo} human={s_hi} brief+voice ok  {'PASS ✅' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
