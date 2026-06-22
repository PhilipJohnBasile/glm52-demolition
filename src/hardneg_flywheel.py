"""Hard-negative mining flywheel (#16) — keeps the 18 CPU cores (verify_many) + the ANE (embed) busy for a
time budget, alongside the GPU heal chain. RICH procedural generation (infinite, no model, no contamination):
  pick a REAL algorithm template (binary-search, gcd, Kadane, two-sum, bubble-sort, RLE, ...) parameterized
  with random inputs and a python-COMPUTED assert -> inject a realistic bug (off-by-one / wrong-bound /
  wrong-comparison / wrong-init) -> verify_many BOTH on the 18 cores (runs the asserts) -> keep pairs where
  good PASSES & mutant FAILS = a verified hard negative (real algorithmic bug) -> embed the good code on the
  ANE. GPU-free; never converges.

  python src/hardneg_flywheel.py --hours 12
"""
import argparse
import itertools
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

# realistic algorithmic bugs (not arithmetic noise): off-by-one, wrong bound, wrong comparison, wrong init
_MUTS = [(" == ", " != "), (" < ", " <= "), (" <= ", " < "), (" > ", " >= "), (" >= ", " > "),
         ("+1", "-1"), ("-1", "+1"), ("[0]", "[-1]"), ("len(a)-1", "len(a)"), ("range(2,", "range(1,"),
         (" and ", " or "), ("max(", "min("), ("[::-1]", "[::1]"), ("//2", "//3"), ("i+1", "i"),
         ("lo=m+1", "lo=m"), ("hi=m-1", "hi=m"), ("n<2", "n<1"), ("%15", "%5"), ("a%b", "b%a")]


def _t_binary_search():
    a = sorted(random.sample(range(1, 60), 7)); t = random.choice(a)
    return ("def f(a,t):\n    lo,hi=0,len(a)-1\n    while lo<=hi:\n        m=(lo+hi)//2\n"
            "        if a[m]==t: return m\n        if a[m]<t: lo=m+1\n        else: hi=m-1\n    return -1\n"
            f"assert f({a},{t})=={a.index(t)}")


def _t_gcd():
    x, y = random.randint(6, 90), random.randint(6, 90)
    return f"def f(a,b):\n    while b: a,b=b,a%b\n    return a\nassert f({x},{y})=={math.gcd(x,y)}"


def _t_fib():
    n = random.randint(5, 16); a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return f"def f(n):\n    a,b=0,1\n    for _ in range(n): a,b=b,a+b\n    return a\nassert f({n})=={a}"


def _t_is_prime():
    n = random.randint(2, 60); p = n > 1 and all(n % i for i in range(2, int(n ** 0.5) + 1))
    return ("def f(n):\n    if n<2: return False\n    for i in range(2,int(n**0.5)+1):\n"
            f"        if n%i==0: return False\n    return True\nassert f({n})=={p}")


def _t_dedup():
    lst = [random.randint(1, 5) for _ in range(7)]; seen = []
    for x in lst:
        if x not in seen:
            seen.append(x)
    return ("def f(lst):\n    seen=[]\n    for x in lst:\n        if x not in seen: seen.append(x)\n"
            f"    return seen\nassert f({lst})=={seen}")


def _t_two_sum():
    a = random.sample(range(1, 30), 6); i, j = sorted(random.sample(range(6), 2)); t = a[i] + a[j]
    res = None
    for ii in range(len(a)):
        for jj in range(ii + 1, len(a)):
            if a[ii] + a[jj] == t:
                res = [ii, jj]; break
        if res:
            break
    return ("def f(a,t):\n    for i in range(len(a)):\n        for j in range(i+1,len(a)):\n"
            f"            if a[i]+a[j]==t: return [i,j]\n    return None\nassert f({a},{t})=={res}")


def _t_max_subarray():
    a = [random.randint(-5, 9) for _ in range(7)]; best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x); best = max(best, cur)
    return ("def f(a):\n    best=cur=a[0]\n    for x in a[1:]:\n        cur=max(x,cur+x); best=max(best,cur)\n"
            f"    return best\nassert f({a})=={best}")


def _t_bubble_sort():
    a = random.sample(range(1, 40), 6)
    return ("def f(a):\n    a=a[:]\n    for i in range(len(a)):\n        for j in range(len(a)-1-i):\n"
            f"            if a[j]>a[j+1]: a[j],a[j+1]=a[j+1],a[j]\n    return a\nassert f({a})=={sorted(a)}")


def _t_palindrome():
    s = random.choice(["racecar", "hello", "noon", "python", "level", "world"])
    return f"def f(s):\n    return s==s[::-1]\nassert f({s!r})=={s == s[::-1]}"


def _t_flatten():
    nested = [[random.randint(1, 9) for _ in range(2)] for _ in range(3)]
    flat = [x for sub in nested for x in sub]
    return ("def f(n):\n    out=[]\n    for sub in n: out.extend(sub)\n    return out\n"
            f"assert f({nested})=={flat}")


def _t_factorial():
    n = random.randint(2, 8)
    return f"def f(n):\n    r=1\n    for i in range(2,n+1): r*=i\n    return r\nassert f({n})=={math.factorial(n)}"


def _t_count_vowels():
    s = "".join(random.choices("aeiobcd", k=8)); c = sum(1 for ch in s if ch in "aeiou")
    return f"def f(s):\n    return sum(1 for c in s if c in 'aeiou')\nassert f({s!r})=={c}"


def _t_run_length():
    s = "".join(random.choices("aab", k=6))
    out = [(ch, len(list(g))) for ch, g in itertools.groupby(s)]
    return ("def f(s):\n    import itertools\n    return [(c,len(list(g))) for c,g in itertools.groupby(s)]\n"
            f"assert f({s!r})=={out}")


def _t_fizzbuzz():
    n = random.randint(1, 30)
    v = "FizzBuzz" if n % 15 == 0 else "Fizz" if n % 3 == 0 else "Buzz" if n % 5 == 0 else str(n)
    return ("def f(n):\n    if n%15==0: return 'FizzBuzz'\n    if n%3==0: return 'Fizz'\n"
            f"    if n%5==0: return 'Buzz'\n    return str(n)\nassert f({n})=={v!r}")


def _t_reverse_words():
    words = random.sample(["the", "cat", "sat", "on", "a", "mat"], 4); s = " ".join(words)
    return ("def f(s):\n    return ' '.join(s.split()[::-1])\n"
            f"assert f({s!r})=={' '.join(words[::-1])!r}")


_TEMPLATES = [_t_binary_search, _t_gcd, _t_fib, _t_is_prime, _t_dedup, _t_two_sum, _t_max_subarray,
              _t_bubble_sort, _t_palindrome, _t_flatten, _t_factorial, _t_count_vowels, _t_run_length,
              _t_fizzbuzz, _t_reverse_words]


def _mutate(code):
    random.shuffle(_MUTS)
    for x, y in _MUTS:
        if x in code:
            return code.replace(x, y, 1)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=12.0)
    ap.add_argument("--report", type=int, default=50)
    ap.add_argument("--out", default="heal/hardnegs_rich.jsonl")
    a = ap.parse_args()
    from verifiers import verify, verify_many
    try:
        from ane_embed import ANEEmbedder
        emb = ANEEmbedder()
    except Exception:
        emb = None
    print(f"  flywheel: RICH algo templates ({len(_TEMPLATES)}), {a.hours}h, ANE={'on' if emb else 'off'} "
          f"-> {a.out}", flush=True)
    deadline = time.time() + a.hours * 3600
    found = rounds = idx = 0
    out = open(a.out, "a")
    while time.time() < deadline:
        rounds += 1
        pairs = []
        for _ in range(24):
            g = random.choice(_TEMPLATES)()
            b = _mutate(g)
            if b and b != g:
                pairs.append((g, b))
        items = []
        for g, b in pairs:
            items += [(g,), (b,)]
        res = verify_many(items, fn=lambda code: verify("python", code, ""))     # 18-core CPU fan-out
        ok = []
        for i, (g, b) in enumerate(pairs):
            rg, rb = res[2 * i], res[2 * i + 1]
            if rg and rg.passed and rb and not rb.passed:                          # good runs, mutant breaks
                out.write(json.dumps({"good": g, "bad": b, "stage": rb.stage}) + "\n")
                found += 1
                ok.append(g)
        out.flush()
        if emb and ok:
            try:
                emb.embed(ok)
                idx += len(ok)
            except Exception:
                pass
        if rounds % a.report == 0:
            print(f"  round {rounds}: {found} rich hard-negs, {idx} ANE-embeds, "
                  f"{(deadline - time.time()) / 3600:.2f}h left", flush=True)
    print(f"  flywheel done: {found} rich hard-negs, {idx} embeds, {rounds} rounds")


if __name__ == "__main__":
    main()
