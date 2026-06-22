"""Math + science verifiers/tools — verify-don't-guess, extended to STEM.
- sympy_eval : symbolic compute/simplify/solve, and `a == b` identity VERIFICATION
               (catches hallucinated algebra/calculus instantly).
- units_check: dimensional analysis via pint (physical equations must be consistent).
- arxiv_search: live papers from arXiv (science beyond the training cutoff).
Back the agent's `sympy`, `units`, `arxiv` tools.
"""
import re
import urllib.parse
import urllib.request


def sympy_eval(expr):
    """Verify an identity (`lhs == rhs`) or compute/simplify/solve a SymPy expression."""
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr
    except Exception as e:  # noqa: BLE001
        return f"sympy unavailable: {e}"
    try:
        if "==" in expr:
            lhs, rhs = expr.split("==", 1)
            diff = sympy.simplify(parse_expr(lhs) - parse_expr(rhs))
            return f"{'TRUE ✓' if diff == 0 else 'FALSE'}  (simplified lhs-rhs = {diff})"
        return str(sympy.simplify(parse_expr(expr)))
    except Exception as e:  # noqa: BLE001
        return f"sympy error: {str(e)[:150]}"


def units_check(expr):
    """Evaluate a quantity with units, e.g. '9.8 meter/second**2 * 2 second' -> velocity."""
    try:
        import pint
    except Exception:  # noqa: BLE001
        return "pint not installed (uv pip install pint) — dimensional analysis unavailable"
    try:
        return str(pint.UnitRegistry()(expr))
    except Exception as e:  # noqa: BLE001
        return f"units error: {str(e)[:150]}"


def arxiv_search(query, k=5):
    """Top-k live arXiv papers (title + abstract link) — beat the training cutoff."""
    url = ("http://export.arxiv.org/api/query?search_query=all:"
           + urllib.parse.quote(query) + f"&start=0&max_results={k}&sortBy=relevance")
    try:
        xml = urllib.request.urlopen(url, timeout=20).read().decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        return f"arxiv unavailable: {str(e)[:80]}"
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
    out = []
    for e in entries[:k]:
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        i = re.search(r"<id>(.*?)</id>", e, re.S)
        s = re.search(r"<summary>(.*?)</summary>", e, re.S)
        out.append(f"- {(t.group(1).strip()[:130]) if t else ''}\n  {i.group(1).strip() if i else ''}"
                   f"\n  {(s.group(1).strip()[:160]) if s else ''}")
    return "\n".join(out) or "(no results)"


def selftest():
    a = sympy_eval("sin(x)**2 + cos(x)**2 == 1")            # a true identity
    b = sympy_eval("(x+1)**2 == x**2 + 2*x + 2")            # FALSE (off by 1)
    c = sympy_eval("integrate(2*x, x)")                     # -> x**2
    ok = "TRUE" in a and "FALSE" in b and "x**2" in c
    print(f"  sympy: identity={a.split('(')[0].strip()}, false-caught={'FALSE' in b}, "
          f"integral={c.strip()}  {'PASS ✅' if ok else 'FAIL'}")
    ax = arxiv_search("speculative decoding transformers", k=2)
    print(f"  arxiv: {'OK' if ('arxiv.org' in ax) else 'no-network'} "
          f"-> {ax.splitlines()[0][:60] if ax else ''}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
