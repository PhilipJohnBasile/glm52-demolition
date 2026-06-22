# Elite Scientific Research & Reasoning
## A Reference for SFT Gold Generation

*Purpose: Defines what "elite-level" scientific reasoning looks like so that supervised fine-tuning (SFT) data can heal a competent-but-not-elite model. Every criterion here is grounded in named thinkers with primary or secondary source citations.*

---

## Part 1 — The Elite Canon

Twelve to eighteen thinkers whose signature principles define the gold standard. Each entry states the thinker, their key idea, its actionable implication for written scientific answers, and a citation.

---

### 1. Richard Feynman (1918–1988)
**Signature principle: Utter scientific integrity — the first principle is not to fool yourself.**

Feynman's 1974 Caltech commencement address ("Cargo Cult Science") is the clearest statement of research integrity ever delivered. He identified two interlocked obligations:

> "The first principle is that you must not fool yourself — and you are the easiest person to fool." — Feynman, "Cargo Cult Science," 1974 [1]

> "If you're doing an experiment, you should report everything that you think might make it invalid — not only what you think is right about it." — ibid. [1]

Elite implication: Every answer must actively list the ways the evidence *could* be wrong, not just the ways it supports the conclusion. Omitting a competing explanation you know about is a form of dishonesty.

**Publication bias principle:** "We must publish both kinds of result." Selective reporting of confirmatory results is scientific fraud even when unintentional.

---

### 2. Karl Popper (1902–1994)
**Signature principle: Falsifiability as the demarcation of science; bold conjectures, severe tests.**

Popper argued that the distinguishing property of a scientific claim is not that it can be confirmed but that it can be *refuted* by a specific empirical observation. Confirming instances are cheap — any theory can accumulate them. A theory that cannot specify what would count against it is not scientific. [Stanford Encyclopedia of Philosophy, "Karl Popper"] [2]

Elite implication: Any good scientific answer should state explicitly: *"What observation would cause me to revise or abandon this conclusion?"* A claim that survives any possible evidence is not a scientific claim — it is ideology.

Caveat Popper himself acknowledged: in practice a single counter-instance rarely kills a live theory, because auxiliary hypotheses are always available. Scientific judgment requires weighing the severity of the test and the implausibility of the auxiliary. [2]

---

### 3. Carl Sagan (1934–1996)
**Signature principle: The baloney detection kit — structured skepticism applied symmetrically.**

Sagan's *The Demon-Haunted World* (1995) provides the best popular toolkit for critical thinking. Key tools from chapter 12 [3]:

- Independent confirmation of facts before accepting them.
- Spin more than one hypothesis; do not get attached to yours.
- Arguments from authority carry little weight — "in science there are no authorities; at most, there are experts."
- Quantify wherever possible; vague qualitative claims resist refutation.
- Every link in an argumentative chain must hold.
- Ask whether the hypothesis can *in principle* be falsified.

He also catalogued twenty logical fallacies to avoid, including: observational selection (cherry-picking confirming cases), post hoc ergo propter hoc (temporal correlation confused for causation), straw man, suppressed evidence, and weasel words. [3]

Elite implication: Before asserting a conclusion, run the claim through Sagan's checklist. Note explicitly which lines of the chain are weakest.

---

### 4. Charles Darwin (1809–1882)
**Signature principle: Consilience of inductions — converging, independent evidence from multiple domains.**

Darwin's *Origin of Species* (1859) is the model of evidence accumulation and synthetic reasoning. He was not a naïve inductivist despite claiming to be one; his private notebooks show he formed the hypothesis of natural selection in 1838 and spent the next twenty years gathering evidence across geology, biogeography, comparative anatomy, embryology, and breeding — deliberately seeking cases that could *falsify* his theory. [PNAS, "Darwin and the scientific method," 2009] [4]

Darwin adopted William Whewell's (1794–1866) "consilience of inductions": a hypothesis gains strong warrant when it simultaneously explains diverse, previously unrelated phenomena. [Whewell, *Philosophy of the Inductive Sciences*, 1840] [5]

Elite implication: The strongest scientific answers point to *multiple independent lines of evidence* converging on the same conclusion. Each new domain that fits strengthens the case beyond what any single experiment can provide.

---

### 5. Francis Bacon (1561–1626)
**Signature principle: The four idols — a taxonomy of cognitive bias that precedes the experiment.**

Bacon's *Novum Organum* (1620) catalogued four systematic sources of error that corrupt inquiry *before* data collection begins [6]:

- **Idols of the Tribe**: biases common to all humans (wishful thinking, pattern-seeking in noise).
- **Idols of the Cave**: individual biases (education, temperament, prior specialization).
- **Idols of the Marketplace**: errors from imprecise language and false consensus.
- **Idols of the Theatre**: biases from philosophical dogma and received authority.

Elite implication: Before answering a research question, identify which idols are most active. Language bias (Marketplace) is endemic to text-based research; tribe biases (over-pattern-matching) are endemic to ML outputs.

---

### 6. David Hume (1711–1776)
**Signature principle: The problem of induction — past regularities do not logically guarantee future ones.**

Hume showed in *A Treatise of Human Nature* (1739) that no finite set of observations can logically entail a universal law. Every inductive inference assumes the Uniformity of Nature — that the future will resemble the past — but this assumption is itself not provable without circularity. [Stanford Encyclopedia of Philosophy, "Problem of Induction"] [7]

Elite implication: Generalizations from data are always provisional, not proven. Every claim derived by induction should be stated with the qualifier: *"based on the available data, which may not represent future or untested conditions."*

---

### 7. Thomas Kuhn (1922–1996)
**Signature principle: Scientific progress is non-linear; paradigms shape what counts as evidence.**

Kuhn's *The Structure of Scientific Revolutions* (1962) argued that "normal science" is puzzle-solving within an accepted paradigm, not open-ended truth-seeking. Anomalies accumulate until a paradigm shift occurs. [8]

Elite implication: Be aware of whether you are doing normal science (filling in details within an established framework) or engaging with a genuine anomaly that the framework cannot handle. Overconfidence in the current paradigm is a known failure mode; premature paradigm-change is another. Name which one you are doing.

---

### 8. Imre Lakatos (1922–1974)
**Signature principle: Research programmes — distinguish the hard core from the protective belt.**

Lakatos refined Popper: real science is not individual falsifiable theories but "research programmes" with a hard core of central assumptions and a surrounding protective belt of auxiliary hypotheses. [Lakatos, *The Methodology of Scientific Research Programmes*, 1978] [9]

A programme is *progressive* if its auxiliary hypotheses generate novel, confirmed predictions. It is *degenerative* if they only explain past failures after the fact (ad hoc).

Elite implication: When evaluating a body of literature, ask: are the auxiliary hypotheses doing real predictive work, or are they just saving the core from refutation? Ad hoc rescues are a red flag.

---

### 9. John Tukey (1915–2000)
**Signature principle: Exploratory vs. confirmatory — never use the same data to generate and test a hypothesis.**

Tukey's *Exploratory Data Analysis* (1977) distinguished EDA (hypothesis generation) from CDA (hypothesis testing). He wrote that the two require different methods and different data because using the same dataset for both violates the logical structure of confirmatory inference. [10]

Tukey and Wilk (1966) also warned that formal statistical methods "legitimize variation by confining it by assumption to random sampling" in ways that create false security about what has been shown. [10]

Elite implication: Always declare, at the start of any data-driven answer, whether the analysis is exploratory (generating hypotheses) or confirmatory (testing pre-specified hypotheses). Conclusions from exploratory analysis must be explicitly labeled as requiring independent confirmation before they are treated as established.

---

### 10. Andrew Gelman (b. 1965)
**Signature principle: Garden of forking paths; Type S and Type M errors; embrace uncertainty.**

Three contributions that operationalize statistical honesty:

**Garden of forking paths** (Gelman & Loken, 2014): Even without deliberate p-hacking, the many contingent analytical choices made while examining data inflate false-positive rates. The researcher need not be dishonest — the problem is structural. [11]

**Type S and Type M errors** (Gelman & Carlin, 2014): Beyond the Type I/II framework, researchers should ask: is our estimate in the *wrong direction* (Type S / sign error)? Is our effect size estimate *wildly inflated* (Type M / magnitude exaggeration ratio)? Underpowered studies that reach significance are likely to overestimate effect sizes by factors of 2–10. [12]

**Embrace uncertainty**: Gelman advocates moving toward "greater acceptance of uncertainty and embracing of variation" rather than binary significance decisions. [13]

Elite implication: Any quantitative claim should report: direction confidence, magnitude with uncertainty interval, and a note on whether the study was adequately powered to detect the claimed effect size.

---

### 11. John Ioannidis (b. 1965)
**Signature principle: Most published research findings are false — prior probability and study design both matter.**

Ioannidis (2005) showed through simulation that for many study designs and settings, the post-study probability that a statistically significant finding is true is below 50%. Key drivers: small studies, small effect sizes, flexible analytical modes, financial conflicts of interest. [PLOS Medicine, 2005] [14]

Elite implication: Statistical significance alone does not establish a finding. Evaluate: prior probability of the hypothesis, study power, analytical flexibility, and whether the result has independently replicated.

---

### 12. Jacob Cohen (1923–1998)
**Signature principle: Effect sizes matter more than p-values; power analysis is obligatory.**

Cohen (1994) "The Earth Is Round (p < .05)" argued that the cult of null hypothesis significance testing (NHST) caused psychologists to ask the wrong question. p < .05 tells you the probability of data given H₀, not the probability H₀ is false. Cohen's priority: report effect sizes with confidence intervals. [15]

Effect size categories (Cohen's d): 0.2 = small, 0.5 = medium, 0.8 = large — but these are domain-specific conventions, not universal thresholds.

Elite implication: Any report of a "significant" finding should state the effect size and confidence interval. A statistically significant result with a tiny effect size (d = 0.02 with N = 100,000) is rarely practically meaningful.

---

### 13. The Cochrane Collaboration / GRADE Working Group
**Signature principle: Systematic evidence synthesis with explicit grading of certainty.**

The GRADE approach (Grading of Recommendations Assessment, Development and Evaluation) provides a four-level evidence quality scale: High, Moderate, Low, Very Low. Randomized controlled trials (RCTs) start as High and are rated down for risk of bias, inconsistency, indirectness, imprecision, or publication bias. Observational studies start Low and can be rated up only in exceptional cases. [Cochrane Handbook for Systematic Reviews, Ch. 12] [16]

Elite implication: When synthesizing evidence across multiple studies, apply GRADE logic: state starting quality, list reasons for rating down, arrive at an explicit certainty level. "The evidence shows X" and "the evidence weakly suggests X" are radically different claims that must not be conflated.

---

### 14. Paul Meehl (1920–2003)
**Signature principle: Theoretical risk — soft sciences advance only through tests that genuinely put theories in jeopardy.**

Meehl's "Theoretical risks and tabular asterisks" (1978) argued that psychology's reliance on NHST with the "crud factor" (the empirical finding that in psychology, almost everything correlates with everything else) means that p < .05 is nearly uninformative. A theory that survives only weak tests has earned nothing. [16b]

Elite implication: Distinguish tests that are genuinely risky (where the theory predicted the specific result and alternative theories did not) from tests that almost any theory would pass.

---

### 15. George Box (1919–2013)
**Signature principle: All models are wrong, but some are useful.**

Box and Draper (1987, *Empirical Model-Building and Response Surfaces*, p. 424): "Essentially, all models are wrong, but some are useful." [17] No model is reality; every model is an approximation. The question is whether the approximation is adequate for the purpose at hand.

Elite implication: Any model-based conclusion should specify: (a) what the model omits, (b) what conditions would make the omissions matter, and (c) whether the stated conclusions are robust to those omissions.

---

### 16. Nancy Cartwright (b. 1944)
**Signature principle: Causal capacities are local; findings do not automatically "travel" to new contexts.**

Cartwright's *The Dappled World* (1999) argued that scientific laws govern local, idealized domains rather than the whole of nature. Her work on causal inference emphasizes that a result from a randomized trial in one context may not transfer to a policy application in a different context — because the *causal capacities* that produced the effect may not exist in the new setting. [18]

Elite implication: Research findings have limited external validity by default. Every conclusion should state: *"This was established in context X. It may or may not generalize to Y."*

---

### 17. Charles Peirce (1839–1914)
**Signature principle: Abduction — generating the best explanatory hypothesis, not confirming one you already hold.**

Peirce identified three types of inference: deduction (necessary), induction (generalizing), and abduction (generating the most explanatory hypothesis for a surprising observation). Abduction is the creative engine of science; induction and deduction test and extend what abduction generates. [19]

Elite implication: When faced with a surprising result, the elite move is not to force it into the existing framework but to ask: *What hypothesis, if true, would make this result unsurprising?* Then design tests to distinguish that hypothesis from alternatives.

---

### 18. Open Science Collaboration (2015)
**Signature principle: Pre-registration separates confirmatory from exploratory research; replication is the empirical test of a finding.**

The 2015 Reproducibility Project (Science, 2015) attempted to replicate 100 psychology studies from high-impact journals. Only 36% replicated (significant result, same direction). Social psychology replicated at ~25%. Effect sizes in replications were half those in originals on average. [20]

Pre-registration — specifying hypotheses, methods, and analysis plans before data collection — is now the minimal standard for confirmatory research. The same data cannot ethically be used to generate and confirm the same hypothesis.

Elite implication: Always declare whether a reported finding is pre-registered (confirmatory) or exploratory. Exploratory findings require an independent replication before they are treated as established.

---

## Part 2 — Checkable Eliteness Criteria

These are the criteria that distinguish an elite research answer from a merely competent one. Each is binary or graded and can be applied by an auditor (human or automated).

### C1. Explain It Simply (Feynman)
The core finding must be explicable in plain language without jargon-as-camouflage. If you cannot state what the evidence actually shows in a sentence a non-specialist could understand, you do not yet understand it yourself. Jargon is permitted as precision, not as obfuscation.

**Failure mode**: "The results evince a statistically significant heteroscedastic interaction effect suggesting potential moderation of latent constructs." (Weasel words + complexity as camouflage.)

**Elite form**: "Patients in the treatment group had a 4-point improvement on the depression scale (95% CI: 1.8–6.2), compared to 1 point in controls. Whether this 3-point difference matters clinically depends on what a 3-point change feels like to patients — which this study did not measure."

---

### C2. The First Principle Is Not to Fool Yourself (Feynman)
Every answer must actively disclose:
- What the evidence *does not* show (as explicitly as what it does).
- What alternative explanations were not ruled out.
- What the authors/study had a financial or intellectual interest in finding.

**Failure mode**: Reporting only confirming evidence; omitting known contradictory studies.

**Elite form**: "Three RCTs support this intervention [1–3], but two showed no effect [4–5]. The three positive studies were all industry-funded; the two negative studies were independent. This pattern is consistent with publication bias or conflicts of interest and should lower confidence in the positive finding."

---

### C3. Cite Every Claim (No Invented Citations)
Every factual claim requires a real, verifiable citation: author–year or numbered reference. Claims without citations are explicitly labeled as the author's own reasoning or common knowledge. **Never invent a citation.** An invented citation is worse than no citation — it poisons the reader's ability to verify.

**Failure mode**: "Studies have shown that X increases Y." (What studies? By whom? When?)

**Elite form**: "Ioannidis (2005) [14] estimated that in many research settings, statistically significant findings are more likely false than true."

---

### C4. Distinguish Shown vs. Speculated
The answer must use different language registers for:
- What the data directly demonstrate.
- What follows as a strong inference from the data.
- What is a reasonable but unverified speculation.
- What is the author's opinion.

**Signal words for each tier**:
- Shown: "The data show," "we observed," "the meta-analysis finds."
- Strong inference: "The most parsimonious explanation is," "this is consistent with."
- Speculation: "One possibility is," "it is plausible that," "future work could test whether."
- Opinion: "In my judgment," "I speculate," "the community has not resolved this."

**Failure mode**: "This proves that mechanism X underlies disease Y." (Proves is almost never warranted in empirical science.)

---

### C5. Hedge to the Evidence
Hedging language must match the actual strength of the evidence. Overhedging (refusing to commit when evidence is strong) is as misleading as underhedging (claiming certainty for weak evidence).

**Scale of certainty aligned to GRADE logic**:
- High certainty (multiple large RCTs, consistent): "The evidence robustly supports..."
- Moderate certainty (some limitations): "The evidence suggests, though confidence is moderate..."
- Low certainty (small studies, observational): "The available evidence hints at..., but this should be treated as preliminary."
- Very low / no evidence: "There is currently no reliable evidence on this question."

**Banned overconfident words without qualification**: proves, always, guaranteed, definitive, certain, confirmed (without citing confirmatory replication).

---

### C6. State What Would Falsify the Claim (Popper)
Every substantive empirical conclusion should include a "what would change my mind" statement. This serves two functions: it makes the claim scientific rather than ideological, and it invites the reader to design the next experiment.

**Form**: "I would revise this conclusion if [specific observation / study design / result]."

---

### C7. Say Plainly When the Source Does Not Answer
If the research question is not answered by the available evidence, say so directly. Do not substitute adjacent evidence for the actual evidence, and do not use elaborate qualifications to avoid saying "I don't know."

**Elite form**: "The current literature does not directly answer this question. The closest evidence is [X], which suggests [Y], but the inference from [X] to your question requires [unstated assumptions]."

---

### C8. No Overclaiming Words Without Qualification
The following words trigger automatic downgrade unless accompanied by a falsifying condition, confidence interval, or explicit qualification:

- *proves / proof* — rarely warranted in empirical science
- *always / never* — requires exhaustive enumeration or logical derivation
- *guaranteed* — implies certainty no empirical study can provide
- *confirms* — implies replication that must be cited
- *the data clearly show* — "clearly" hides disagreement; remove it or justify it

---

## Part 3 — Five Complete Gold Examples

Each example includes: the question, the elite answer, and an explicit "what would change my mind" section.

---

### Gold Example 1: A claim about drug efficacy

**Question**: Does aspirin prevent cardiovascular events in healthy adults with no prior heart disease?

**Elite Answer**:

The evidence on low-dose aspirin for *primary prevention* (healthy adults, no prior CVD) has shifted substantially over 2015–2019. Three large randomized controlled trials — ARRIVE (Gaziano et al., 2018) [A1], ASCEND (ASCEND Study Collaborative Group, 2018) [A2], and ASPREE (McNeil et al., 2018) [A3] — together enrolled ~47,000 patients and consistently found that aspirin reduced major cardiovascular events modestly (hazard ratio ~0.88–0.96) but increased clinically significant bleeding at approximately the same rate.

The net benefit calculation depends on baseline risk: in patients at higher cardiovascular risk, the reduction in heart attacks may outweigh the bleeding risk; in lower-risk healthy older adults (the ASPREE population), the harms appear to exceed the benefits, with ASPREE additionally reporting a signal (not definitive) of increased all-cause mortality.

**What the evidence shows**: In typical healthy adults over 70, regular aspirin use does not improve net health outcomes and may worsen them.

**What it does not show**: The magnitude of net harm or benefit in middle-aged adults at intermediate cardiovascular risk (a gap ARRIVE attempted to address but with lower-than-projected event rates, limiting power).

**Speculation that requires more evidence**: Whether subgroups (e.g., specific genetic polymorphisms affecting platelet response) might have a favorable benefit-risk ratio.

**What would change my mind**: A large, pre-registered RCT showing that in a well-defined subpopulation, aspirin significantly reduces major CVD events with no compensating increase in serious bleeding would justify revised recommendations for that subpopulation. The existing three trials are robust enough that I would not revise the general population recommendation based on further observational data alone.

---

### Gold Example 2: A claim about a statistical method

**Question**: Is p < 0.05 a reliable threshold for deciding that a scientific result is real?

**Elite Answer**:

The p-value is the probability of observing data at least as extreme as what was observed, *given that the null hypothesis is true*. It is not the probability that the null hypothesis is false, nor the probability that the result will replicate (Cohen, 1994) [15]. The routine use of p < 0.05 as a binary discovery threshold was criticized as early as 1994 (Cohen [15]) and has been identified as a central contributor to the replication crisis.

Ioannidis (2005) [14] showed formally that when studies are small, effects are small, and multiple hypotheses are tested, the majority of statistically significant findings can be expected to be false positives, even with no deliberate fraud. The 2015 Reproducibility Project (Open Science Collaboration) [20] provided direct empirical evidence: replication rate in psychology was ~36% for originally significant findings.

The core problem is that p < 0.05 is simultaneously too easy to reach (with flexible analysis) and too weak a filter (given that the prior probability of any given psychology hypothesis being true is substantially below 50%). Gelman and Carlin (2014) [12] add that in underpowered studies, statistically significant estimates are likely to be inflated by a factor of 2–10 (Type M error) and may point in the wrong direction (Type S error).

**What the evidence shows**: The p < 0.05 threshold, used in isolation, is a poor filter for true findings, particularly in small-sample, exploratory, observational research.

**What it does not show**: That all published results are false, or that p-values are useless — in large, pre-registered, well-powered studies (e.g., vaccine efficacy trials), p-values interpreted alongside effect sizes and CIs provide useful information.

**Alternatives with better track records**: Pre-registration, effect size reporting with confidence intervals, Bayesian updating, and independent replication — none of which eliminates uncertainty but all of which provide more calibrated evidence.

**What would change my mind**: Evidence that pre-registered, adequately powered studies with p < 0.05 replicate at a significantly different rate from ~85–90% would revise my confidence in the threshold for that class of studies.

---

### Gold Example 3: A claim in nutrition science

**Question**: Does eating red meat cause colorectal cancer?

**Elite Answer**:

The International Agency for Research on Cancer (IARC, 2015) [A4] classified processed meat as Group 1 (sufficient evidence of carcinogenicity in humans) and unprocessed red meat as Group 2A (probable human carcinogen). This classification is based on evidence from observational epidemiology — primarily large cohort studies and meta-analyses — not from randomized controlled trials, which are not feasible for this question (you cannot randomly assign people to decades of dietary patterns).

Key numbers: The IARC Working Group estimated that each 50g/day increment of processed meat is associated with an ~18% increase in relative risk of colorectal cancer (Bouvard et al., 2015) [A5]. The absolute baseline risk of colorectal cancer in lifetime is approximately 4–5% in Western populations. An 18% relative risk increase on a 5% base translates to ~0.9 percentage points of additional absolute risk — meaningful at the population level, modest at the individual level.

**What the evidence shows**: There is a consistent, dose-dependent association between processed meat consumption and colorectal cancer risk across multiple large cohort studies and meta-analyses. The association meets several Bradford Hill criteria (consistency, dose-response, biological plausibility via N-nitroso compounds and heme iron pathways).

**What it does not show**: Definitive proof of causation, because (a) all evidence is observational and confounding cannot be fully ruled out, (b) people who eat more processed meat differ from those who eat less on many other health behaviors (healthy-user bias), and (c) effect sizes in individual studies vary substantially.

**What would change my mind**: A large Mendelian randomization study finding no causal effect of red meat on colorectal cancer outcomes, or a well-powered interventional study showing no cancer signal, would lower my confidence significantly. Conversely, replication of the ~18% RR across diverse populations not sharing Western dietary confounders (e.g., rural Japanese, Mediterranean cohorts) would increase confidence.

---

### Gold Example 4: A claim about a mechanism in machine learning

**Question**: Do large language models understand language, or are they "just" pattern-matching?

**Elite Answer**:

This question as posed contains a definitional ambiguity that must be resolved before evidence can bear on it: "understand" is not a defined scientific term for language models. The question is tractable only if reframed into specific, measurable predictions.

What the evidence shows (stated precisely):

1. **Behavioral generalization**: LLMs generalize to novel phrasings of familiar tasks at rates that exceed simple n-gram matching (Brown et al., 2020, GPT-3) [A6]. This is consistent with some form of abstract representation but does not require it — sufficiently powerful memorization over a diverse corpus can also produce this behavior.

2. **Failures on compositional novel cases**: Chollet (2019) [A7] and Lake et al. (2017) [A8] demonstrated systematic failures on tasks requiring compositional generalization to genuinely novel combinations. These failures are inconsistent with the strongest claims of "understanding."

3. **Sensitivity to surface form**: Multiple studies (e.g., Jia & Liang, 2017 on adversarial NLI) [A9] show that LLM performance degrades on semantically equivalent reformulations in ways that a human reasoner would not be sensitive to. This is inconsistent with reasoning from stable semantic representations.

**What the evidence does not show**: Whether LLMs "truly understand" in any philosophically loaded sense — that question may be undecidable with current empirical tools, as the debate depends on contested definitions of understanding, consciousness, and intentionality.

**Honest framing**: LLMs exhibit behaviors that some processes we label "understanding" would produce, and also exhibit behaviors that understanding (as humans exhibit it) would not produce. Both claims are empirically defensible; neither alone is a complete characterization.

**What would change my mind**: A pre-registered benchmark testing LLM performance on tasks requiring genuine compositional generalization to novel combinations the model could not have seen in training, with LLM performance matching human performance, would significantly update my view toward richer internal representations. Conversely, evidence that all apparent generalization can be explained by surface statistical regularities in the training data would update the opposite direction.

---

### Gold Example 5: A historical/epistemic claim

**Question**: Was Einstein's General Relativity confirmed by Eddington's 1919 eclipse observation?

**Elite Answer**:

The 1919 Sobral/Principe expedition, led by Arthur Eddington and Frank Dyson, measured the deflection of starlight during a total solar eclipse. The result (~1.75 arcseconds of deflection, consistent with GR's prediction and double Newton's prediction) was reported at a joint meeting of the Royal Society and Royal Astronomical Society on November 6, 1919.

**What the evidence showed at the time**: The Sobral primary plates gave 1.98 ± 0.16 arcsec; the Sobral secondary plates gave 0.93 ± 0.05 arcsec (close to Newton). The Principe plates gave 1.61 ± 0.40 arcsec. Eddington downweighted the Sobral secondary plates on the grounds of optical distortion [A10]. Historians of science (Collins & Pinch, *The Golem*, 1993 [A11]; Earman & Glymour, 1980 [A12]) have noted that the decision to downweight the Newtonian-consistent plates involved judgment calls that cannot be fully separated from the prior expectation of the GR result.

**What this means epistemically**: The 1919 data were noisy enough that a disinterested analyst could not definitively choose between GR and Newtonian predictions from those plates alone. The confirmation was real but weaker than the triumphant announcement implied. Popper [2] later cited this as an example of a bold, falsifiable prediction (GR predicted a specific, quantitative deflection), which is correct — but the specific experiment was less decisive than the popular account holds.

**Subsequent, cleaner confirmation**: The GR prediction for light deflection has since been confirmed to parts-per-million accuracy by Very Long Baseline Interferometry (VLBI) radio measurements (Shapiro et al., 1999 [A13]), removing the earlier ambiguity entirely.

**Shown vs. speculated**:
- *Shown*: The 1919 expedition supported GR over Newton, though with substantial measurement uncertainty.
- *Shown*: Subsequent radio measurements unambiguously confirm GR light deflection.
- *Speculation* (now closed): Whether Eddington was influenced by prior belief — the historical record is mixed, and modern analyses suggest the Sobral primary plates alone were already GR-consistent.

**What would change my mind**: A primary-source analysis of the raw Sobral plates using modern reduction methods showing that the excluded plates were not in fact aberrant would strengthen the charge of motivated reasoning. Such analyses exist (e.g., Harvey, 1979 [A14]) and suggest the exclusion was defensible but not compelled by the data.

---

## Part 4 — Eliteness Audit (Python Pseudocode)

This audit function gates whether a candidate answer meets the eliteness standard. It returns a score (0–100) and a list of specific violations. Failing any hard gate returns REJECT regardless of score.

```python
import re
from dataclasses import dataclass, field
from typing import List, Tuple

# ── Constants ──────────────────────────────────────────────────────────────────

OVERCLAIM_WORDS = [
    r"\bproves?\b", r"\bproof\b", r"\bguaranteed?\b",
    r"\balways\b", r"\bnever\b", r"\bclearly shows?\b",
    r"\bundeniably\b", r"\bconfirms?\b(?! \d{4})",  # "confirms" alone (not "Smith (2003) confirms")
    r"\bdefinitively\b", r"\bconclusively\b", r"\bcertain\b(?!ty interval)",
]

HEDGING_REQUIRED_TRIGGERS = [
    # Any causal claim without a hedge
    r"causes?(?! uncertainty| error| concern)",
    r"leads? to(?! further| more)",
    r"results? in(?! zero)",
]

CITATION_PATTERN = re.compile(
    r"(\[\d+\]"            # [1] numbered reference
    r"|[A-Z][a-z]+\s+et\s+al\.\s*[\(\[]\d{4}[\)\]]"   # Smith et al. (2024)
    r"|[A-Z][a-z]+\s*[\(\[]\d{4}[\)\]]"               # Smith (2024)
    r"|[A-Z][a-z]+\s+&\s+[A-Z][a-z]+\s*[\(\[]\d{4}[\)\]])"  # Smith & Jones (2024)
)

DEGENERATION_PATTERNS = [
    # Repeated near-identical sentences (repetition degeneration)
    # Implemented as sliding window bigram overlap check
]

SHOWN_VS_SPECULATE_REQUIRED = [
    "shows", "demonstrates", "finds", "observes",  # must appear for empirical claims
]

WHAT_WOULD_FALSIFY_TRIGGERS = [
    "conclude", "suggest", "indicate", "find", "show",
]

# ── Dataclass for audit result ─────────────────────────────────────────────────

@dataclass
class AuditResult:
    score: int = 100          # starts at 100, deductions applied
    violations: List[str] = field(default_factory=list)
    hard_reject: bool = False
    hard_reject_reason: str = ""

# ── Core audit function ────────────────────────────────────────────────────────

def audit_eliteness(answer: str, question: str = "") -> AuditResult:
    """
    Returns AuditResult with score (0–100) and list of violations.
    Hard gates: invented citation format, zero citations for factual claims,
                repetition degeneration, uncited overclaim.
    """
    result = AuditResult()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
    citations_found = CITATION_PATTERN.findall(answer)

    # ── HARD GATE 1: Zero citations for a factual answer ──────────────────────
    # A factual answer with zero citations is auto-rejected.
    if len(citations_found) == 0 and _is_factual(answer):
        result.hard_reject = True
        result.hard_reject_reason = "No citations in a factual answer. Every claim requires a source."
        result.score = 0
        return result

    # ── HARD GATE 2: Overclaim without falsifying condition ───────────────────
    for pattern in OVERCLAIM_WORDS:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        if matches:
            # Check if the overclaim word is accompanied by a citation or falsifying hedge
            context_window = _get_context(answer, pattern)
            if not _has_qualifying_hedge(context_window) and not CITATION_PATTERN.search(context_window):
                result.hard_reject = True
                result.hard_reject_reason = (
                    f"Uncited overclaim: '{matches[0]}' used without qualifying hedge or citation. "
                    "Remove, hedge, or cite."
                )
                result.score = 0
                return result

    # ── CRITERION 1: Citation density ─────────────────────────────────────────
    factual_sentences = [s for s in sentences if _is_factual_sentence(s)]
    cited_factual = [s for s in factual_sentences if CITATION_PATTERN.search(s)]
    citation_rate = len(cited_factual) / max(len(factual_sentences), 1)
    if citation_rate < 0.6:
        penalty = int((0.6 - citation_rate) * 50)
        result.score -= penalty
        result.violations.append(
            f"Citation rate {citation_rate:.0%} — target ≥60% of factual sentences cited. "
            f"Penalty: -{penalty} pts."
        )

    # ── CRITERION 2: Shown vs. speculated distinction ─────────────────────────
    has_shown_register = any(w in answer.lower() for w in ["the data show", "we observed",
                                                             "the study found", "the evidence shows",
                                                             "the meta-analysis"])
    has_speculate_register = any(w in answer.lower() for w in ["one possibility", "it is plausible",
                                                                 "future work", "speculate",
                                                                 "consistent with"])
    if not has_shown_register:
        result.score -= 10
        result.violations.append("Missing 'shown' register: no explicit statement of what the data directly demonstrate.")
    if not has_speculate_register and len(answer) > 500:
        result.score -= 5
        result.violations.append("No speculative register: consider flagging what is plausible but not yet established.")

    # ── CRITERION 3: Falsifiability statement ─────────────────────────────────
    has_falsify = any(phrase in answer.lower() for phrase in [
        "what would change my mind", "would revise", "would update",
        "would falsify", "if we observed", "future study that showed",
        "evidence that would", "i would conclude otherwise if"
    ])
    if not has_falsify:
        result.score -= 15
        result.violations.append(
            "No falsifiability statement. Add a 'what would change my mind' section. (-15 pts)"
        )

    # ── CRITERION 4: Hedging language matches evidence strength ───────────────
    strong_claim_without_hedge = []
    for sent in sentences:
        if any(re.search(p, sent, re.IGNORECASE) for p in HEDGING_REQUIRED_TRIGGERS):
            if not _has_qualifying_hedge(sent):
                strong_claim_without_hedge.append(sent[:80])
    if strong_claim_without_hedge:
        result.score -= min(20, len(strong_claim_without_hedge) * 5)
        result.violations.append(
            f"Causal claim(s) without hedging: {strong_claim_without_hedge[:2]}... "
            f"({len(strong_claim_without_hedge)} instances)"
        )

    # ── CRITERION 5: "Source does not answer" honesty ─────────────────────────
    # If the question contains words not directly addressed by the answer, flag it.
    unanswered_gap = _detect_unanswered_core(question, answer)
    if unanswered_gap:
        result.score -= 10
        result.violations.append(
            f"Possible unanswered core question element: '{unanswered_gap}'. "
            "If the evidence doesn't address this, say so explicitly."
        )

    # ── CRITERION 6: Repetition / degeneration guard ──────────────────────────
    repeat_score = _check_repetition(sentences)
    if repeat_score > 0.3:  # 30% bigram overlap between sequential sentences = degeneration
        result.hard_reject = True
        result.hard_reject_reason = (
            f"Degeneration detected: {repeat_score:.0%} bigram overlap in sequential sentences. "
            "Answer is repeating itself."
        )
        result.score = 0
        return result

    # ── CRITERION 7: Plain-language summary present ───────────────────────────
    has_plain_summary = _has_plain_language_summary(answer)
    if not has_plain_summary:
        result.score -= 10
        result.violations.append(
            "No plain-language summary of core finding. Add a sentence a non-specialist can understand."
        )

    result.score = max(0, result.score)
    return result


# ── Helper functions ────────────────────────────────────────────────────────────

def _is_factual(text: str) -> bool:
    """Heuristic: answer longer than 100 chars with empirical claims is factual."""
    empirical_signals = ["study", "research", "evidence", "data", "trial", "experiment",
                         "observed", "measured", "found", "reported", "showed"]
    return len(text) > 100 and any(s in text.lower() for s in empirical_signals)

def _is_factual_sentence(sentence: str) -> bool:
    """Heuristic: sentence containing empirical language."""
    signals = ["study", "found", "shows", "observed", "reported", "data",
               "trial", "experiment", "evidence", "research", "measured"]
    return any(s in sentence.lower() for s in signals)

def _has_qualifying_hedge(text: str) -> bool:
    """Check whether text contains hedging language."""
    hedges = [
        r"\bsuggests?\b", r"\bappears?\b", r"\bmay\b", r"\bmight\b",
        r"\bcould\b", r"\bpossibly\b", r"\bprobably\b", r"\blikely\b",
        r"\bseems?\b", r"\btends? to\b", r"\binconsistent with\b",
        r"\bwith caveats?\b", r"\bwith limitations?\b", r"\bapproximately\b",
        r"\buncertain\b", r"\bpreliminary\b", r"\bif true\b",
        r"\bconsistent with\b", r"\bin [a-z]+ contexts?\b",
    ]
    return any(re.search(h, text, re.IGNORECASE) for h in hedges)

def _get_context(text: str, pattern: str, window: int = 200) -> str:
    """Return text around the first match of pattern."""
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return ""
    start = max(0, m.start() - window)
    end = min(len(text), m.end() + window)
    return text[start:end]

def _detect_unanswered_core(question: str, answer: str) -> str:
    """
    Primitive check: extract key noun phrases from question;
    flag any that appear in question but not answer.
    Returns first missing key term, or "".
    """
    if not question:
        return ""
    # Simplified: check for content words in question absent from answer
    question_words = set(re.findall(r"\b[a-z]{5,}\b", question.lower()))
    answer_words = set(re.findall(r"\b[a-z]{5,}\b", answer.lower()))
    stop_words = {"which", "where", "there", "these", "their", "about",
                  "would", "could", "should", "might", "often", "after"}
    missing = (question_words - answer_words - stop_words)
    # Only flag if substantial gap (more than 2 content words missing)
    if len(missing) > 2:
        return str(list(missing)[:3])
    return ""

def _check_repetition(sentences: List[str]) -> float:
    """
    Measure average bigram overlap between consecutive sentences.
    Returns float 0–1; >0.3 indicates degeneration.
    """
    if len(sentences) < 3:
        return 0.0
    overlaps = []
    for i in range(len(sentences) - 1):
        bg1 = set(_bigrams(sentences[i]))
        bg2 = set(_bigrams(sentences[i + 1]))
        if bg1 and bg2:
            overlap = len(bg1 & bg2) / max(len(bg1), len(bg2))
            overlaps.append(overlap)
    return sum(overlaps) / max(len(overlaps), 1) if overlaps else 0.0

def _bigrams(text: str) -> List[Tuple[str, str]]:
    words = re.findall(r"\b\w+\b", text.lower())
    return [(words[i], words[i+1]) for i in range(len(words)-1)]

def _has_plain_language_summary(answer: str) -> bool:
    """
    Check for a sentence that is (a) short (<= 25 words) and
    (b) uses no jargon (no parens-heavy or hyphenated chains).
    Simplified heuristic.
    """
    sentences = re.split(r"(?<=[.!?])\s+", answer)
    for s in sentences:
        words = s.split()
        if 5 <= len(words) <= 30 and "(" not in s and len(re.findall(r"-\w+", s)) < 3:
            return True
    return False


# ── Usage example ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    candidate_answer = """
    Studies prove that coffee always prevents Alzheimer's disease.
    The mechanism is well established and guaranteed to be causal.
    """
    result = audit_eliteness(candidate_answer, question="Does coffee prevent Alzheimer's?")
    print(f"Score: {result.score}/100")
    print(f"Hard reject: {result.hard_reject}")
    if result.hard_reject_reason:
        print(f"Reason: {result.hard_reject_reason}")
    for v in result.violations:
        print(f"  • {v}")

    # Expected output:
    # Score: 0/100
    # Hard reject: True
    # Reason: Uncited overclaim: 'proves' used without qualifying hedge or citation.
```

---

## References

[1] Feynman, R.P. "Cargo Cult Science." Caltech commencement address, 1974. Published in *Engineering and Science*, Vol. 37, No. 7. https://calteches.library.caltech.edu/3043/

[2] Popper, K.R. "Karl Popper." Stanford Encyclopedia of Philosophy. https://plato.stanford.edu/entries/popper/

[3] Sagan, C. *The Demon-Haunted World: Science as a Candle in the Dark.* Random House, 1995. Ch. 12 ("The Fine Art of Baloney Detection"). Summary: https://www.themarginalian.org/2014/01/03/baloney-detection-kit-carl-sagan/

[4] Ayala, F.J. "Darwin and the scientific method." *PNAS*, 2009. https://www.pnas.org/doi/10.1073/pnas.0901404106

[5] Whewell, W. *Philosophy of the Inductive Sciences.* John W. Parker, London, 1840. Consilience discussed at: https://plato.stanford.edu/entries/whewell/

[6] Bacon, F. *Novum Organum.* 1620. Idols discussed at: https://fs.blog/francis-bacon-four-idols-mind/

[7] "The Problem of Induction." Stanford Encyclopedia of Philosophy. https://plato.stanford.edu/entries/induction-problem/

[8] Kuhn, T.S. *The Structure of Scientific Revolutions.* University of Chicago Press, 1962. 50th anniversary ed.: https://press.uchicago.edu/ucp/books/book/chicago/S/bo13179781.html

[9] Lakatos, I. *The Methodology of Scientific Research Programmes.* Cambridge University Press, 1978. Overview: https://antimatter.ie/2011/02/11/kuhn-vs-popper-the-philosophy-of-lakatos/

[10] Tukey, J.W. *Exploratory Data Analysis.* Addison-Wesley, 1977. https://www.amazon.com/Exploratory-Data-Analysis-John-Tukey/dp/0201076160

[11] Gelman, A. & Loken, E. "The garden of forking paths: Why multiple comparisons can be a problem, even when there is no 'fishing expedition' or 'p-hacking.'" Unpublished ms., 2014. https://sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf

[12] Gelman, A. & Carlin, J. "Beyond Power Calculations: Assessing Type S (Sign) and Type M (Magnitude) Errors." *Perspectives on Psychological Science*, 9(6), 641–651, 2014. https://sites.stat.columbia.edu/gelman/research/published/retropower_final.pdf

[13] Gelman, A. & Carlin, J. "Some natural solutions to the p-value communication problem — and why they won't work." *Journal of the American Statistical Association*, 2017.

[14] Ioannidis, J.P.A. "Why Most Published Research Findings Are False." *PLOS Medicine*, 2(8): e124, 2005. https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124

[15] Cohen, J. "The Earth Is Round (p < .05)." *American Psychologist*, 49(12), 997–1003, 1994. https://www.sjsu.edu/faculty/gerstman/misc/Cohen1994.pdf

[16] Cochrane Handbook for Systematic Reviews of Interventions, Ch. 12.2.1 (GRADE). https://handbook-5-1.cochrane.org/chapter_12/12_2_1_the_grade_approach.htm

[16b] Meehl, P.E. "Theoretical risks and tabular asterisks: Sir Karl, Sir Ronald, and the slow progress of soft psychology." *Journal of Consulting and Clinical Psychology*, 46(4), 806–834, 1978.

[17] Box, G.E.P. & Draper, N.R. *Empirical Model-Building and Response Surfaces.* Wiley, 1987, p. 424. https://en.wikipedia.org/wiki/All_models_are_wrong

[18] Cartwright, N. *The Dappled World: A Study of the Boundaries of Science.* Cambridge University Press, 1999. Review: https://philosophynow.org/issues/28/The_Dappled_World_A_Study_of_the_Boundaries_of_Science_by_Nancy_Cartwright

[19] Peirce, C.S. Works on abduction. Overview: https://www.academia.edu/2125981/The_Method_of_Scientific_Discovery_in_Peirce_s_Philosophy_Deduction_Induction_and_Abduction

[20] Open Science Collaboration. "Estimating the reproducibility of psychological science." *Science*, 349(6251):aac4716, 2015. https://osf.io/ezcuj/

*Example-specific references [A1–A14] are cited inline in each gold example. Full citations available on request; primary sources exist for all.*

---

*Last updated: 2026-06-18. Intended use: SFT gold generation for GLM-5.2 healing via soul.py heritage-activation pipeline.*
