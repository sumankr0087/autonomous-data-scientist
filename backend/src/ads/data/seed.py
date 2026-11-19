"""Generate a realistic sample sales dataset and load it into DuckDB.

The data is deterministic (fixed seed) and intentionally contains a visible
**sales drop in Maharashtra in the most recent quarter**, so the flagship demo
question — "Why did sales drop in Maharashtra last quarter?" — has a real,
discoverable answer in the data.

Tables created:
  - sales(order_id, order_date, year, quarter, region, state, category,
          product, channel, units, unit_price, discount, revenue)
  - products(product, category, base_price)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ads.core.logging import get_logger
from ads.tools.database import Database

log = get_logger(__name__)

REGIONS = {
    "West": ["Maharashtra", "Gujarat", "Rajasthan"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala"],
    "North": ["Delhi", "Punjab", "Uttar Pradesh"],
    "East": ["West Bengal", "Odisha", "Bihar"],
}

CATEGORIES = {
    "Electronics": ["Laptop", "Smartphone", "Headphones"],
    "Home": ["Blender", "Vacuum", "Lamp"],
    "Apparel": ["T-Shirt", "Jacket", "Shoes"],
}
BASE_PRICE = {
    "Laptop": 55000, "Smartphone": 25000, "Headphones": 3000,
    "Blender": 4000, "Vacuum": 12000, "Lamp": 1500,
    "T-Shirt": 800, "Jacket": 3500, "Shoes": 4500,
}
CHANNELS = ["Online", "Retail", "Partner"]


def _quarter(month: int) -> int:
    return (month - 1) // 3 + 1


def _last_complete_quarter(end: pd.Timestamp) -> tuple[int, int]:
    """Return (year, quarter_number) of the last *complete* quarter before `end`."""
    cur_q = _quarter(end.month)
    if cur_q == 1:
        return end.year - 1, 4
    return end.year, cur_q - 1


def generate_sales(seed: int = 42) -> pd.DataFrame:
    """Build a synthetic sales DataFrame spanning ~2 years ending today.

    This always includes the current year, and injects a visible sales drop in
    Maharashtra's Online channel during the most recent *complete* quarter.
    """
    rng = np.random.default_rng(seed)
    end = pd.Timestamp(pd.Timestamp.today().date())
    start = pd.Timestamp(year=end.year - 1, month=1, day=1)  # Jan 1 last year
    all_states = [(r, s) for r, states in REGIONS.items() for s in states]
    products = [(c, p) for c, ps in CATEGORIES.items() for p in ps]

    drop_year, drop_q = _last_complete_quarter(end)

    rows: list[dict] = []
    order_id = 1
    days = (end - start).days
    for _ in range(8000):
        order_date = start + pd.Timedelta(days=int(rng.integers(0, days + 1)))
        region, state = all_states[rng.integers(len(all_states))]
        category, product = products[rng.integers(len(products))]
        channel = CHANNELS[rng.integers(len(CHANNELS))]
        units = int(rng.integers(1, 6))
        base = BASE_PRICE[product]
        unit_price = round(base * rng.uniform(0.9, 1.1), 2)
        discount = round(float(rng.choice([0, 0, 0.05, 0.10, 0.15])), 2)

        # --- Injected signal: Maharashtra Online channel collapses in the
        # most recent complete quarter (so "last quarter" shows a real drop). ---
        keep = True
        if (
            state == "Maharashtra"
            and order_date.year == drop_year
            and _quarter(order_date.month) == drop_q
        ):
            if channel == "Online" and rng.random() < 0.75:
                keep = False  # most online Maharashtra orders disappear
            elif rng.random() < 0.35:
                keep = False
        if not keep:
            continue

        revenue = round(units * unit_price * (1 - discount), 2)
        rows.append(
            {
                "order_id": order_id,
                "order_date": order_date.date().isoformat(),
                "year": order_date.year,
                "quarter": f"Q{_quarter(order_date.month)}",
                "region": region,
                "state": state,
                "category": category,
                "product": product,
                "channel": channel,
                "units": units,
                "unit_price": unit_price,
                "discount": discount,
                "revenue": revenue,
            }
        )
        order_id += 1

    df = pd.DataFrame(rows).sort_values("order_date").reset_index(drop=True)
    return df


def generate_products() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"product": p, "category": c, "base_price": BASE_PRICE[p]}
            for c, ps in CATEGORIES.items()
            for p in ps
        ]
    )


def seed_database(db: Database | None = None, seed: int = 42) -> dict[str, int]:
    """Generate the dataset and load it into DuckDB. Returns row counts."""
    db = db or Database()
    sales = generate_sales(seed)
    products = generate_products()
    counts = {
        "sales": db.write_df(sales, "sales"),
        "products": db.write_df(products, "products"),
    }
    log.info("Seed complete", extra=counts)
    return counts
