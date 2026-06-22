"""Tabular ML (#102) — Classification / Regression / Time-Series Forecasting on the CPU (sklearn/statsmodels,
all 18 cores via n_jobs=-1). Extends table_tool.py (#94, Table-QA) with predictive models. ZERO GPU.

    from tabular_ml import classify, regress, forecast
    model, acc = classify(X, y)          # Tabular Classification
    model, r2  = regress(X, y)           # Tabular Regression
    next_vals  = forecast(series, 5)     # Time-Series Forecasting
"""
import numpy as np


def classify(X, y, X_new=None):
    """Tabular Classification (RandomForest, all cores). Returns (model, predictions or train-accuracy)."""
    from sklearn.ensemble import RandomForestClassifier
    m = RandomForestClassifier(n_estimators=80, n_jobs=-1, random_state=0).fit(X, y)
    return (m, m.predict(X_new)) if X_new is not None else (m, m.score(X, y))


def regress(X, y, X_new=None):
    """Tabular Regression (GradientBoosting). Returns (model, predictions or train-R²)."""
    from sklearn.ensemble import GradientBoostingRegressor
    m = GradientBoostingRegressor(n_estimators=80, random_state=0).fit(X, y)
    return (m, m.predict(X_new)) if X_new is not None else (m, m.score(X, y))


def forecast(series, steps=5):
    """Time-Series Forecasting (Holt-Winters exponential smoothing). Returns the next `steps` values."""
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    m = ExponentialSmoothing(np.asarray(series, float), trend="add").fit()
    return [round(float(v), 3) for v in m.forecast(steps)]


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(0, 1, (50, 4)), rng.normal(3, 1, (50, 4))]); y = np.array([0] * 50 + [1] * 50)
    _, acc = classify(X, y)
    Xr = rng.normal(0, 1, (120, 3)); yr = 2 * Xr[:, 0] - Xr[:, 1] + rng.normal(0, 0.1, 120)
    _, r2 = regress(Xr, yr)
    fc = forecast(list(range(20)), 3)
    print(f"  classify acc={acc:.2f} | regress R²={r2:.2f} | forecast(next 3)={fc}")
    ok = acc > 0.9 and r2 > 0.85 and len(fc) == 3
    print(f"  tabular_ml selftest {'PASS' if ok else 'CHECK'} — classify/regress/forecast on the CPU (sklearn/statsmodels, 18 cores)")
