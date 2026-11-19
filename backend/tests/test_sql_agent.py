"""Tests for the Step 5 SQL agent (fake LLM + seeded temp DuckDB, no network)."""

from __future__ import annotations

import pytest

from ads.agents.sql_agent import answer
from ads.data.seed import seed_database
from ads.llm.client import BaseLLMClient, LLMResponse
from ads.tools.database import Database
from ads.tools.sql_tool import SQLTool


class ScriptedLLM(BaseLLMClient):
    """Returns a scripted list of replies, one per call."""

    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)

    def complete(self, prompt, *, system=None, **kwargs):
        return LLMResponse(text=self._replies.pop(0), model="fake")


@pytest.fixture
def tool(tmp_path):
    db = Database(path=str(tmp_path / "t.duckdb"))
    seed_database(db)
    return SQLTool(db=db)


def test_sql_agent_runs_valid_query(tool):
    llm = ScriptedLLM(
        ["SELECT state, SUM(revenue) AS rev FROM sales GROUP BY state"]
    )
    res = answer("Revenue by state?", sql_tool=tool, llm=llm)
    assert res.ok is True
    assert res.row_count == 12
    assert "rev" in res.columns
    assert res.attempts == 1


def test_sql_agent_strips_markdown_fences(tool):
    llm = ScriptedLLM(["```sql\nSELECT COUNT(*) AS n FROM sales\n```"])
    res = answer("How many rows?", sql_tool=tool, llm=llm)
    assert res.ok is True
    assert res.rows[0]["n"] > 1000


def test_sql_agent_self_corrects_on_error(tool):
    # First reply is a write (rejected), second is valid -> should recover.
    llm = ScriptedLLM(
        [
            "DELETE FROM sales",  # rejected by SQLTool guard
            "SELECT region, SUM(revenue) AS rev FROM sales GROUP BY region",
        ]
    )
    res = answer("Revenue by region?", sql_tool=tool, llm=llm, max_retries=3)
    assert res.ok is True
    assert res.attempts == 2
    assert len(res.rows) == 4  # 4 regions


def test_sql_agent_gives_up_after_retries(tool):
    llm = ScriptedLLM(["DROP TABLE sales"] * 3)
    res = answer("bad", sql_tool=tool, llm=llm, max_retries=3)
    assert res.ok is False
    assert res.attempts == 3
    assert res.error is not None
