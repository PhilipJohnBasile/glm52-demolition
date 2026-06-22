#!/usr/bin/env python3
"""The MODEL designs — the harness only operates. Give GLM-5.2-v4 a design brief, take ITS HTML,
then RENDER + MEASURE it with our critic (25_design_critique). If the critic flags issues, feed
them back and the MODEL revises. Author = the model; verifier = the harness. No human (or Claude)
writes a line of the design. Output: showcase/model_design.html + .png + the critique.

  python scripts/69_model_designs.py --rounds 3
"""
import argparse
import importlib.util
import json
import os
import re
import time
import urllib.request

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "showcase")
_spec = importlib.util.spec_from_file_location("dc", os.path.join(HERE, "25_design_critique.py"))
dc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dc)

BRIEF = (
    "You are a world-class product designer in the Swiss / International tradition (Müller-Brockmann, "
    "Dieter Rams, Massimo Vignelli). Design a single-page DARK landing page for 'GLM-5.2 Demolished' — "
    "a 743-billion-parameter AI model pruned to run on a single MacBook.\n\n"
    "Hard requirements: OKLCH colors with ONE accent; a modular type scale; an 8px spacing grid; "
    "generous whitespace; clear hierarchy; AA contrast (>=4.5:1 body). Tell the story (743B -> 99GB, "
    "runs fully local, every output verified) with: a hero, a 4-stat scorecard (HumanEval 95%, GSM8K "
    "66%, 99 GB on-device, 47 verified tools), and a short 'it cannot lie to you' section. Dark theme "
    "done right (no pure #000/#fff). Output ONE complete, self-contained HTML file with inline <style>. "
    "Output ONLY a single ```html code block."
)


def chat(base_url, model, prompt, max_tokens=3500):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.6, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(base_url + "/chat/completions", body, {"Content-Type": "application/json"})
    m = json.loads(urllib.request.urlopen(req, timeout=600).read())["choices"][0]["message"]
    return m.get("content") or m.get("reasoning") or ""


def extract_html(text):
    m = re.search(r"```html\s*\n(.*?)```", text, re.S) or re.search(r"(<!doctype html.*?</html>)",
                                                                     text, re.S | re.I)
    return (m.group(1) if m else text).strip()


def run(base_url, model, rounds):
    os.makedirs(OUT, exist_ok=True)
    fb, best = "", None
    for r in range(rounds):
        prompt = BRIEF + (f"\n\nThe automated design critic found these issues in your last version — "
                          f"FIX every one and output the FULL revised HTML:\n{fb}" if fb else "")
        print(f"  [round {r+1}] the MODEL is designing…", flush=True)
        html = extract_html(chat(base_url, model, prompt))
        path = os.path.join(OUT, "model_design.html")
        open(path, "w").write(html)
        png = os.path.join(OUT, "model_design.png")
        try:
            findings = dc.critique(html, dc.measure(html, png))
        except Exception as e:  # noqa: BLE001
            findings = [f"render/measure error: {str(e)[:140]}"]
        print(f"  [round {r+1}] model wrote {len(html)} bytes; critic: "
              f"{findings if findings else 'CLEAN ✅ (passed WCAG/type/OKLCH/grid)'}", flush=True)
        best = (len(findings), path)
        if not findings:
            print(f"  ✅ THE MODEL's design PASSED the critic in {r+1} round(s) -> {path}")
            return
        fb = "; ".join(map(str, findings[:6]))
    print(f"  best of {rounds} -> {best[1]} ({best[0]} issues left: {fb})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="models/GLM-5.2-q3a4-v4")
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()
    print("  waiting for the model to be served…", flush=True)
    for _ in range(80):
        try:
            urllib.request.urlopen(args.base_url.replace("/v1", "") + "/v1/models", timeout=5)
            break
        except Exception:  # noqa: BLE001
            time.sleep(8)
    run(args.base_url, args.model, args.rounds)


if __name__ == "__main__":
    main()
