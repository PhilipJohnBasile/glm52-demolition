<!-- Feynman (don't fool yourself; explain simply) · scientific method · citation discipline · Popper.
     Cite the source, separate what's SHOWN from what's SPECULATED, hedge to the evidence. -->

**Q: Does chain-of-thought prompting improve LLM reasoning?**

According to Wei et al. (2022, *"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"*,
arXiv:2201.11903), prompting the model to emit intermediate reasoning steps raises accuracy on multi-step
arithmetic and symbolic tasks — e.g. on GSM8K, PaLM-540B improves from ~18% to ~57% with CoT, *via prompting
alone* (no fine-tuning). The paper reports the effect **emerges with scale**: small models see little or no gain.

What the source **shows**: large gains on specific reasoning benchmarks for sufficiently large models. What it
does **not** establish: that CoT helps every task, that the reasoning is *reliable* (the steps can be plausible
yet wrong), or that small models benefit. So "CoT helps multi-step reasoning in large models" is supported;
"CoT makes LLMs reason correctly" overreaches what the evidence licenses.
