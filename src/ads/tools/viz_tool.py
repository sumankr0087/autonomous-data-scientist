"""Visualization tool — render charts from the query result into `artifacts/`.

Headless (Agg backend). Generic: picks the focus numeric metric and the first
label-like column and draws a horizontal bar chart of the top movers. Returns the
list of saved file paths.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # no display / headless

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ARTIFACTS_DIR  # noqa: E402

from ads.core.logging import get_logger  # noqa: E402
from ads.tools.eda_tool import _focus_column  # noqa: E402

log = get_logger(__name__)


def _label_column(df: pd.DataFrame) -> str | None:
    cats = df.select_dtypes(exclude="number").columns.tolist()
    return cats[0] if cats else None


def make_charts(
    data: pd.DataFrame | list[dict],
    run_id: str = "run",
    top_n: int = 10,
) -> list[str]:
    df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data or [])
    if df.empty:
        return []

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    focus = _focus_column(df)
    label = _label_column(df)
    if not focus:
        return []

    try:
        plot_df = df.copy()
        if label:
            # Combine label columns if several categoricals exist for readable bars.
            cats = df.select_dtypes(exclude="number").columns.tolist()[:3]
            plot_df["_label"] = plot_df[cats].astype(str).agg(" | ".join, axis=1)
            label = "_label"
        else:
            plot_df["_label"] = plot_df.index.astype(str)
            label = "_label"

        plot_df = plot_df.sort_values(focus).head(top_n)  # biggest negative movers
        fig, ax = plt.subplots(figsize=(9, 5))
        colors = ["#d62728" if v < 0 else "#2ca02c" for v in plot_df[focus]]
        ax.barh(plot_df[label], plot_df[focus], color=colors)
        ax.set_title(f"Top movers by {focus}")
        ax.set_xlabel(focus)
        ax.invert_yaxis()
        fig.tight_layout()
        out = ARTIFACTS_DIR / f"chart_{run_id}_{focus}.png"
        fig.savefig(out, dpi=120)
        plt.close(fig)
        paths.append(str(out))
        log.info("Saved chart: %s", out)
    except Exception as exc:  # noqa: BLE001
        log.warning("Chart generation failed: %s", exc)

    return paths
