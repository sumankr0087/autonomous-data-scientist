"""ML tool — train a baseline model and report drivers (feature importance).

Deterministic, no LLM. Auto-detects the task (regression for a numeric target,
classification otherwise), one-hot encodes low-cardinality categoricals, trains a
RandomForest, and returns metrics + ranked feature importances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from ads.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class MlOutcome:
    ok: bool
    task: str = ""
    target: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    importances: list[dict[str, Any]] = field(default_factory=list)
    note: str = ""


def _encode_features(X: pd.DataFrame, max_cardinality: int = 20) -> pd.DataFrame:
    keep = []
    for col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            keep.append(col)
        elif X[col].nunique(dropna=True) <= max_cardinality:
            keep.append(col)
    X = X[keep]
    return pd.get_dummies(X, drop_first=True).fillna(0)


def train_baseline(
    df: pd.DataFrame,
    target: str | None = None,
    min_rows: int = 20,
    top_k: int = 10,
) -> MlOutcome:
    """Train a baseline RandomForest and return metrics + importances."""
    if df is None or df.empty:
        return MlOutcome(False, note="No data to model.")

    numeric = df.select_dtypes(include="number").columns.tolist()
    if target is None:
        target = numeric[-1] if numeric else None
    if not target or target not in df.columns:
        return MlOutcome(False, note="No suitable target column to model.")

    if len(df) < min_rows:
        return MlOutcome(
            False, target=target,
            note=f"Insufficient rows ({len(df)}) to train a reliable model (need >= {min_rows}).",
        )

    y = df[target]
    X = _encode_features(df.drop(columns=[target]))
    if X.shape[1] == 0:
        return MlOutcome(False, target=target, note="No usable features after encoding.")

    is_regression = pd.api.types.is_numeric_dtype(y)
    try:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
        from sklearn.model_selection import train_test_split

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
        if is_regression:
            model = RandomForestRegressor(n_estimators=200, random_state=42)
            model.fit(X_tr, y_tr)
            pred = model.predict(X_te)
            metrics = {
                "r2": round(float(r2_score(y_te, pred)), 4),
                "mae": round(float(mean_absolute_error(y_te, pred)), 4),
            }
            task = "regression"
        else:
            model = RandomForestClassifier(n_estimators=200, random_state=42)
            model.fit(X_tr, y_tr)
            pred = model.predict(X_te)
            metrics = {
                "accuracy": round(float(accuracy_score(y_te, pred)), 4),
                "f1_weighted": round(float(f1_score(y_te, pred, average="weighted")), 4),
            }
            task = "classification"
    except Exception as exc:  # noqa: BLE001
        return MlOutcome(False, target=target, note=f"Model training failed: {exc}")

    importances = sorted(
        (
            {"feature": f, "importance": round(float(imp), 4)}
            for f, imp in zip(X.columns, model.feature_importances_)
        ),
        key=lambda d: d["importance"],
        reverse=True,
    )[:top_k]

    log.info("ML %s on target=%s metrics=%s", task, target, metrics)
    return MlOutcome(True, task=task, target=target, metrics=metrics, importances=importances)
