"""Tests for the Step 2 data layer: DuckDB, seeding and the SQL tool."""

from __future__ import annotations

import pytest

from ads.core.exceptions import SQLGenerationError
from ads.data.seed import seed_database
from ads.tools.database import Database
from ads.tools.sql_tool import SQLTool


@pytest.fixture
def seeded_db(tmp_path):
    db = Database(path=str(tmp_path / "test.duckdb"))
    seed_database(db)
    return db


def test_seed_creates_tables(seeded_db):
    tables = set(seeded_db.list_tables())
    assert {"sales", "products"} <= tables


def test_sales_has_rows(seeded_db):
    df = seeded_db.execute_df("SELECT COUNT(*) AS n FROM sales")
    assert df["n"].iloc[0] > 1000


def test_schema_text_lists_columns(seeded_db):
    schema = seeded_db.schema_text()
    assert "sales(" in schema
    assert "revenue" in schema


def test_maharashtra_drop_is_present(seeded_db):
    """The injected signal: Maharashtra Online revenue collapses in the most
    recent complete quarter vs the same quarter a year earlier."""
    import pandas as pd

    from ads.data.seed import _last_complete_quarter

    end = pd.Timestamp(pd.Timestamp.today().date())
    drop_year, drop_qn = _last_complete_quarter(end)
    q = f"""
        SELECT year, SUM(revenue) AS rev
        FROM sales
        WHERE state = 'Maharashtra' AND channel = 'Online' AND quarter = 'Q{drop_qn}'
        GROUP BY year ORDER BY year
    """
    df = seeded_db.execute_df(q)
    by_year = dict(zip(df["year"], df["rev"]))
    # Drop-quarter online revenue is far below the prior year's same quarter.
    assert by_year.get(drop_year, 0) < by_year.get(drop_year - 1, 1e12)


def test_sql_tool_runs_select(seeded_db):
    tool = SQLTool(db=seeded_db)
    df = tool.run("SELECT state, SUM(revenue) AS rev FROM sales GROUP BY state")
    assert "rev" in df.columns
    assert len(df) == 12  # 12 states


def test_sql_tool_blocks_writes(seeded_db):
    tool = SQLTool(db=seeded_db)
    for bad in ["DROP TABLE sales", "DELETE FROM sales", "UPDATE sales SET units=0"]:
        with pytest.raises(SQLGenerationError):
            tool.run(bad)


def test_sql_tool_blocks_multiple_statements(seeded_db):
    tool = SQLTool(db=seeded_db)
    with pytest.raises(SQLGenerationError):
        tool.run("SELECT 1; SELECT 2")
