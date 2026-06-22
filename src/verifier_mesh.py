"""#26 — verifier-mesh self-training: ONE generic RFT/self-heal loop plugged into EVERY domain verifier
(Lean, Python, SQL, JSON-tools, design, secrets), so the flywheel that lifted Lean pass@1 2/5→4/5 extends
to all of them uniformly. Each domain pairs with a verify_fn; src/self_heal.SelfHealLoop runs the same
generate→verify→keep-verified→SFT loop over each. GPU-free here (the verifiers + registry + selftest);
the generate/SFT steps run on the model (GPU).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from constrained_decode import (DesignValidator, SchemaSQLValidator,  # noqa: E402
                                 SecretValidator, ToolJSONValidator)


def verify_python(code, test=None):
    """Candidate Python compiles + (optional) passes a test snippet — the pytest/exec verifier."""
    try:
        compile(code, "<cand>", "exec")
    except SyntaxError:
        return False
    if test:
        ns = {}
        try:
            exec(code + "\n" + test, ns)  # noqa: S102  (verifier sandbox context)
        except Exception:  # noqa: BLE001
            return False
    return True


def verify_json(text):
    return ToolJSONValidator.balanced(text)


def verify_sql(sql, columns):
    """SELECT grammar + at least one REAL column from the schema (catches hallucinated/destructive SQL)."""
    if not re.match(r"(?is)\s*select\b", sql):
        return False
    sv = SchemaSQLValidator(columns)
    kw = {"select", "from", "where", "and", "or", "join", "on", "group", "by", "order", "limit",
          "as", "in", "not", "null", "is", "count", "sum", "avg", "min", "max", "distinct"}
    cols = [t for t in re.findall(r"\b([a-z_][a-z0-9_]*)\b", sql.lower()) if t not in kw]
    return any(sv.column_ok(c) for c in cols)


def verify_design(sizes_px, spacing_px):
    dv = DesignValidator()
    return all(dv.size_ok(s) for s in sizes_px) and all(dv.grid_ok(s) for s in spacing_px)


def verify_no_secret(text):
    return not SecretValidator().emits_secret(text)


# the mesh: domain -> callable(candidate, **ctx) -> bool. The flywheel runs the SAME loop over each.
VERIFIERS = {
    "python": verify_python,
    "json": verify_json,
    "sql": verify_sql,
    "design": verify_design,
    "secret": verify_no_secret,
    # "lean": wired lazily (needs the elan toolchain) — see lean_verifier()
}


def lean_verifier():
    """Lazily wire the Lean verifier (imports 66_prove, needs elan on PATH). Kept out of VERIFIERS so the
    GPU-free selftest never requires a Lean toolchain."""
    import importlib.util
    here = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("p66", os.path.join(here, "..", "scripts", "66_prove.py"))
    p66 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p66)
    return lambda proof: p66.verify_lean(proof).passed


def heal_loop_for(domain, gen_fn, sft_fn, **ctx):
    """Build a self_heal.SelfHealLoop for `domain` using its mesh verifier. gen_fn/sft_fn are the model-side
    callables (GPU). This is the single mechanism that turns ANY verifier into a self-improving flywheel."""
    from self_heal import SelfHealLoop
    verify = VERIFIERS[domain]
    return SelfHealLoop(gen_fn=gen_fn, verify_fn=lambda c: verify(c, **ctx) if ctx else verify(c), sft_fn=sft_fn)


def _selftest():
    assert verify_python("def f(x): return x + 1", "assert f(1) == 2") and not verify_python("def f(:", None)
    assert verify_json('{"tool":"x"}') and not verify_json('{"a":}}')
    assert verify_sql("select id from users", {"id", "name"}) and not verify_sql("drop table x", {"id"})
    assert verify_design([16, 28], [8, 16]) and not verify_design([17], [13])
    assert verify_no_secret("hello") and not verify_no_secret("AKIA" + "B" * 16)
    assert set(VERIFIERS) >= {"python", "json", "sql", "design", "secret"}
    print(f"  verifier_mesh selftest PASS (#26): {len(VERIFIERS)} domain verifiers + lean(lazy) → "
          "self_heal.SelfHealLoop runs the SAME generate→verify→keep→SFT loop over each domain")


if __name__ == "__main__":
    _selftest()
