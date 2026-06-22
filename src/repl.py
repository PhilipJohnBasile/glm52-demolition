"""Stateful Python REPL — for data science + AI engineering. Unlike a one-shot `run`,
this keeps a PERSISTENT namespace across calls: load a dataframe once, explore it, fit a
model, evaluate — variables/imports/models stay alive, the way real analysis works. Pairs
with plot->SEE: the agent saves a matplotlib figure, then the VLM (vision.py) looks at it
and reasons. Backs the agent's `repl` tool.

  k = PyREPL(); k.run("import pandas as pd; df = pd.read_csv('x.csv')"); k.run("df.describe()")
"""
import contextlib
import io
import traceback


class PyREPL:
    """A persistent in-process Python namespace with captured stdout/stderr + last value."""

    def __init__(self):
        self.ns = {"__name__": "__repl__"}

    def run(self, code, timeout=15):
        import ast
        import signal
        buf = io.StringIO()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return traceback.format_exc(limit=1)[-1200:]

        def _timeout(*_a):                              # guard agent-generated infinite loops
            raise TimeoutError(f"code exceeded {timeout}s")
        has_alarm = hasattr(signal, "SIGALRM")
        if has_alarm:
            old = signal.signal(signal.SIGALRM, _timeout)
            signal.alarm(timeout)
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                if tree.body and isinstance(tree.body[-1], ast.Expr):   # REPL-echo the last value
                    exec(compile(ast.Module(tree.body[:-1], []), "<repl>", "exec"), self.ns)
                    val = eval(compile(ast.Expression(tree.body[-1].value), "<repl>", "eval"), self.ns)
                    if val is not None:
                        print(repr(val)[:1500])
                else:
                    exec(compile(tree, "<repl>", "exec"), self.ns)      # state persists in self.ns
            out = buf.getvalue()
            return out[-3000:] if out.strip() else "(ok, no output)"
        except Exception:  # noqa: BLE001  (incl. TimeoutError from the alarm)
            return (buf.getvalue() + "\n" + traceback.format_exc())[-2500:]
        finally:
            if has_alarm:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)


def selftest():
    k = PyREPL()
    k.run("xs = [1,2,3,4]")                                  # state...
    r1 = k.run("s = sum(xs); s")                             # ...persists + echoes value
    r2 = k.run("import statistics as st; st.mean(xs)")
    bad = k.run("1/0")                                       # real traceback captured
    ok = "10" in r1 and "2.5" in r2 and "ZeroDivisionError" in bad
    print(f"  repl selftest: state persists ({r1.strip()}), mean={r2.strip()}, "
          f"errors captured={'ZeroDivisionError' in bad}  {'PASS ✅' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
