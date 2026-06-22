#!/usr/bin/env python3
"""Design head-to-head vs Fable — proves the DESIGN half of "beat Fable in-niche".

For each brief: render OUR model's HTML and Fable's HTML, MEASURE both with the
same objective signals as 25_design_critique (WCAG contrast, type scale, OKLCH
token usage, framework-default tells), and compare findings counts (fewer =
better). This is the design analogue of 07_eval --vs-fable for code.

  # serve the local model (+ 08 think-proxy) first, then:
  ANTHROPIC_API_KEY=... python scripts/29_design_vs_fable.py \
      --base-url http://localhost:8081/v1

Wrap losers with `26_bestofn.py --mode design` (render+measure best-of-N) to recover.
"""
import argparse
import importlib.util as u
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(__file__)


def load_dc():
    spec = u.spec_from_file_location("dc", os.path.join(HERE, "25_design_critique.py"))
    dc = u.module_from_spec(spec)
    sys.argv = ["dc"]
    spec.loader.exec_module(dc)
    return dc


def local_html(base_url, brief, dc, model=os.environ.get("MODEL_ID", "models/GLM-5.2-q3a4-v2")):
    body = json.dumps({"model": model, "messages": [
        {"role": "system", "content": dc.SYS},
        {"role": "user", "content": f"Design: {brief}"}],
        "temperature": 0.4, "max_tokens": 2600,
        "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    txt = json.loads(urllib.request.urlopen(req, timeout=400).read())[
        "choices"][0]["message"]["content"]
    return dc.extract_html(txt)


def fable_html(brief, key, dc, model):
    body = json.dumps({"model": model, "max_tokens": 2600, "messages": [
        {"role": "user", "content": dc.SYS + "\n\nDesign: " + brief}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", body,
        {"content-type": "application/json", "x-api-key": key,
         "anthropic-version": "2023-06-01"})
    data = json.loads(urllib.request.urlopen(req, timeout=400).read())
    return dc.extract_html("".join(b.get("text", "") for b in data.get("content", [])))


BRIEFS = [
    "an art-directed SaaS pricing hero, OKLCH tokens, no framework defaults, expressive type scale",
    "a developer-tool landing hero with a bespoke layout (not a centered card), accessible contrast",
    "a portfolio case-study header with editorial typography and a non-generic color system",
    "a dashboard empty-state that feels designed, not a Bootstrap/Tailwind default",
]


def findings(html, png, dc):
    try:
        return len(dc.critique(html, dc.measure(html, png)))
    except Exception as e:  # noqa: BLE001
        print(f"    [warn] render/measure failed: {str(e)[:60]}")
        return 999


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8081/v1")
    ap.add_argument("--fable-model", default="claude-fable-5")
    ap.add_argument("--out", default="design_out/vs_fable")
    args = ap.parse_args()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("  [stop] needs ANTHROPIC_API_KEY")
    dc = load_dc()
    os.makedirs(os.path.join(HERE, "..", args.out), exist_ok=True)
    beat = tie = behind = 0
    for i, brief in enumerate(BRIEFS):
        base = os.path.join(HERE, "..", args.out)
        try:
            li = findings(local_html(args.base_url, brief, dc), f"{base}/local{i}.png", dc)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] local gen failed: {str(e)[:60]}"); li = 999
        try:
            fi = findings(fable_html(brief, key, dc, args.fable_model), f"{base}/fable{i}.png", dc)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] fable gen failed: {str(e)[:60]}"); fi = 999
        v = "BEAT FABLE ✅" if li < fi else ("tied" if li == fi else "behind")
        beat += li < fi
        tie += li == fi
        behind += li > fi
        print(f"  brief {i+1}: local {li} findings vs fable {fi}  -> {v}")
    print(f"\n  DESIGN vs FABLE: beat {beat}, tied {tie}, behind {behind} "
          "(fewer measured findings = better). Wrap losers with 26_bestofn --mode design.")


if __name__ == "__main__":
    main()
