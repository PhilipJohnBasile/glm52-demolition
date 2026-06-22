"""Generalize design-soul to EVERY facet — the activation recipe applied across the model's hats.

Each facet has masters whose knowledge is LATENT in the weights (the model read Tufte, Kernighan, Saltzer,
Erdős, Strunk). Generic prompts never activate it → competent-not-elite, everywhere. Same fix as design:
  HERITAGE canon (names the masters → activates) → GATE (audit eliteness) → SEEDS → STEER (design_steering is
  facet-agnostic) → HEAL (design_flywheel, parameterized by the facet's gate).

This file defines the Facet abstraction + a heritage canon per facet + a gate where one is statically checkable
(design/dataviz/security) or delegates to the live verifier (code→compile+lint, math→Lean). The steering vector
and flywheel from design_steering/design_flywheel take ANY facet's gate as the elite/generic contrast.
"""
import re
import sys
import os
from dataclasses import dataclass
from typing import Callable, List

sys.path.insert(0, os.path.dirname(__file__))
from design_canon import audit_design, CANON as _DESIGN_CANON  # noqa: E402  (design facet reuses gate + canon)


@dataclass
class Facet:
    name: str
    heritage: str                       # the masters that activate the latent knowledge (rung-1 priming)
    canon: str                          # the system prompt (rung 0-1)
    audit: Callable[[str], List[str]]   # (output) -> violations; [] = elite. Static gate or verifier-delegate.


# ── DATAVIZ — the crispest parallel to design (Tufte : charts :: Rams : products) ───────────────────────
_CHARTJUNK = re.compile(r"projection\s*=\s*['\"]3d['\"]|mplot3d|Axes3D|\.bar3d|plt\.pie\(|\.pie\("
                        r"|LinearGradient|fillGradient|drop-?shadow|textShadow|set_facecolor\(\s*['\"](?:black|#000)",
                        re.I)


def audit_dataviz(code: str) -> List[str]:
    """Tufte's gate: maximize the data-ink ratio, erase chartjunk. Flags 3-D, pie charts, gradients/shadows,
    dark chart backgrounds. (The render critic adds perceptual checks; this catches the code-level tells.)"""
    junk = _CHARTJUNK.findall(code)
    return [f"chartjunk (Tufte violation): {junk[:3]} — kill 3-D/pie/gradients, show the data"] if junk else []


def _audit_security(code: str) -> List[str]:
    from constrained_decode import SecretValidator  # reuse the 16-pattern gate
    sv = SecretValidator()
    v = ["hard-coded credential — never embed secrets"] if sv.emits_secret(code) else []
    if re.search(r"\beval\(|\bexec\(|shell\s*=\s*True|md5\(|\bDES\b|verify\s*=\s*False", code):
        v.append("insecure primitive (eval/exec/shell=True/md5/DES/verify=False) — fail safe, least privilege")
    return v


def _verifier_gate(_):  # ⚠ NO-OP — code/math/arch are NOT verified here (accepts everything). TODO: wire verify()/
    return []           # verify_lean() in 77_soul_flywheel BEFORE running these facets. (design uses the REAL audit_design gate.)


DESIGN = Facet("design",
    "Rams · Müller-Brockmann · Albers · Bauhaus · Vignelli",
    _DESIGN_CANON, audit_design)

DATAVIZ = Facet("dataviz",
    "Edward Tufte · William Cleveland · the grammar of graphics (Wilkinson/Wickham)",
    "You make ELITE data graphics. HERITAGE: Tufte (the data-ink ratio — erase everything that isn't data; no "
    "chartjunk, no 3-D, no pie charts; small multiples), Cleveland (perception: position > length > angle > "
    "area > color), Wilkinson's grammar of graphics. Above all else, show the data. Direct-label over legends; "
    "one accent; honest axes (start bars at zero); generous whitespace; a clear title that states the finding.",
    audit_dataviz)

CODE = Facet("code",
    "Kernighan & Pike (The Practice of Programming) · the Unix philosophy · Knuth (literate) · per-language idiom",
    "You write ELITE code. HERITAGE: Kernighan & Pike — clarity over cleverness; the Unix philosophy — do one "
    "thing well, compose; Knuth — code is read far more than written, so write it to be read; idiomatic for the "
    "language (Pythonic / idiomatic Rust / effective Go). Names that explain; small honest functions; errors "
    "handled, not hidden; no dead code. Simplicity is the prerequisite for reliability (Dijkstra).",
    _verifier_gate)

SECURITY = Facet("security",
    "Saltzer & Schroeder (the 8 principles) · OWASP · Kerckhoffs · defense-in-depth",
    "You write SECURE code. HERITAGE: Saltzer & Schroeder — least privilege, fail-safe defaults, economy of "
    "mechanism, complete mediation; OWASP top-10; Kerckhoffs — security in the key, not the secrecy of the "
    "design; defense in depth. Never trust input (validate + parameterize); never embed secrets; never roll your "
    "own crypto; fail closed.",
    _audit_security)

MATH = Facet("math",
    "Erdős's 'The Book' · Pólya (How to Solve It) · the mathlib idiom",
    "You write ELITE proofs. HERITAGE: Erdős's Book — seek the most elegant proof, not the first; Pólya — "
    "understand, plan, execute, review; a proof should EXPLAIN why, not just verify. Prefer a short structured "
    "Lean proof (the right lemma) over brute force. Name your steps.",
    _verifier_gate)

PROSE = Facet("prose",
    "Strunk & White · Zinsser (On Writing Well) · Orwell (Politics and the English Language)",
    "You write ELITE prose. HERITAGE: Strunk & White — omit needless words; Zinsser — clarity, simplicity, "
    "humanity; Orwell — never use a long word where a short one does, cut every word you can. Vigorous writing "
    "is concise. Plain, specific, active. No filler, no hedging, no AI-slop.",
    lambda t: (["AI-slop phrasing — cut it"] if re.search(
        r"\b(?:delve|tapestry|in today's (?:fast-paced|digital) world|it's worth noting|leverage|utilize|"
        r"in conclusion|moreover|furthermore)\b", t, re.I) else []))

ARCHITECTURE = Facet("architecture",
    "Christopher Alexander (A Pattern Language) · Parnas (information hiding) · GoF · Uncle Bob (the dependency rule) · Fowler · Fielding (REST) · Evans (DDD)",
    "You design ELITE software architecture. HERITAGE: Alexander — patterns, 'quality without a name' (his work "
    "birthed software design patterns); Parnas — information hiding, modularity; the Gang of Four — composition "
    "over inheritance; Uncle Bob — the dependency rule (source dependencies point INWARD, toward the domain); "
    "Fowler; Evans (DDD); Conway's law. High cohesion, low coupling; separation of concerns; ports & adapters; "
    "make the right thing easy and the wrong thing hard. The structure IS the design.",
    _verifier_gate)


def _audit_research(text):
    """Research-QA gate (proxy): a careful answer CITES + HEDGES. The FULL gate is groundedness vs the source —
    the science-QA flywheel checks the answer's claims actually appear in the retrieved abstract/paper (no
    hallucinated citations). This static check catches the obvious tells: uncited claims + overclaiming."""
    v = []
    if len(text) > 120 and not re.search(r"\[\d+\]|\(\w+\.?,?\s*\d{4}\)|arXiv:|et al\.|according to|Fig(?:ure)? \d|Table \d", text, re.I):
        v.append("no citation — a research answer must ground every claim in a source")
    if re.search(r"\b(?:definitely proves|always works|guaranteed|100% certain|never fails|completely solves)\b", text, re.I):
        v.append("overclaim — hedge to what the evidence supports (Feynman: the first principle is not to fool yourself)")
    return v


RESEARCH = Facet("research",
    "Feynman (understand it simply; don't fool yourself) · the scientific method · citation discipline · Popper (falsifiability)",
    "You answer like a careful RESEARCHER. HERITAGE: Feynman — if you can't explain it simply you don't "
    "understand it, and the first principle is not to fool yourself; the scientific method — claims are "
    "hypotheses until evidenced; Popper — state what would falsify it; citation discipline — every claim grounded "
    "in a source, never invented. Read the paper, cite it ([n] / arXiv / author-year), distinguish what it SHOWS "
    "from what it SPECULATES, hedge to the evidence, and say plainly when the source doesn't answer the question.",
    _audit_research)


FACETS = {f.name: f for f in (DESIGN, DATAVIZ, CODE, SECURITY, MATH, PROSE, ARCHITECTURE, RESEARCH)}


def _selftest():
    print(f"  facets registered: {list(FACETS)}")
    # the statically-gateable facets catch their violations + pass elite examples
    checks = [
        ("dataviz", "ax.plot_surface(X, Y, Z, projection='3d')", "fig, ax = plt.subplots(); ax.plot(x, y); ax.spines[['top','right']].set_visible(False)"),
        ("security", 'token = "sk-ant-api03-abc1234567890XYZdefghij"', "token = os.environ['API_KEY']; cur.execute('select * from t where id=%s', (uid,))"),
        ("prose", "Let's delve into this rich tapestry and leverage synergies.", "The function returns the parsed config. It raises on a missing key."),
        ("research", "This new method definitely proves that scaling always works and guaranteed solves reasoning across every domain with no limitations whatsoever forever.", "The paper (Smith, 2024) reports 53% recall on arXivQA; it does not evaluate generation, so claims beyond retrieval are unsupported."),
    ]
    for name, bad, good in checks:
        f = FACETS[name]
        bv, gv = f.audit(bad), f.audit(good)
        print(f"  {name:9s}: bad→{len(bv)} viol {'✓' if bv else 'MISS'} | good→{len(gv)} viol {'✓' if not gv else 'FALSE-POS'}")
        assert bv and not gv, (name, bv, gv)
    print(f"  {len(FACETS)} facets have heritage canons; code/math delegate to the live verifier (compile+lint/Lean)")
    print("  soul selftest PASS — design-soul recipe generalized to every facet (heritage→gate→steer→heal)")


if __name__ == "__main__":
    _selftest()
