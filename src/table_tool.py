"""Table / data tool — load CSV/Parquet/JSON, expose the schema, and EXECUTE a pandas
query the agent writes (verify-everything: the agent writes it, we run it on the REAL data
and return the REAL result or the REAL error). CPU-native (pandas on the 18 cores). Covers
HF: Table Question Answering, Tabular Classification/Regression, Time Series Forecasting.

    from table_tool import load, schema, query
    df = load("sales.csv")
    print(schema(df))                                    # shape, columns+dtypes, a sample
    query(df, "df.groupby('region')['rev'].mean().to_dict()")   # runs it -> real result
"""


def load(path):
    import pandas as pd
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    if path.endswith(".json"):
        return pd.read_json(path)
    return pd.read_csv(path)


def schema(df):
    """Compact schema the agent reads BEFORE writing a query: shape, columns+dtypes, a sample."""
    cols = ", ".join(f"{c}:{t}" for c, t in zip(df.columns, df.dtypes.astype(str)))
    return f"shape={df.shape}  columns=[{cols}]  sample={df.head(2).to_dict('records')}"


def query(df, expr):
    """Run a pandas EXPRESSION (the agent writes it) against `df`; return the real result or
    the real error (which the agent repairs from). `df`/`pd` in scope; builtins stripped (guard)."""
    import pandas as pd
    safe = {"df": df, "pd": pd, "len": len, "sum": sum, "min": min, "max": max, "sorted": sorted}
    try:
        return {"ok": True, "result": str(eval(expr, {"__builtins__": {}}, safe))[:2000]}
    except Exception as e:  # noqa: BLE001 — the REAL error feeds the repair loop
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


if __name__ == "__main__":
    import pandas as pd
    df = pd.DataFrame({"region": ["W", "E", "W", "E"], "rev": [10, 20, 30, 40]})
    print("  schema:", schema(df))
    good = query(df, "df.groupby('region')['rev'].sum().to_dict()")
    print("  query ->", good)
    bad = query(df, "df.nonexistent_method()")
    ok = good["ok"] and good["result"] == "{'E': 60, 'W': 40}" and not bad["ok"]
    print(f"  table_tool selftest {'PASS' if ok else 'CHECK'} — real result returned, real error caught")
