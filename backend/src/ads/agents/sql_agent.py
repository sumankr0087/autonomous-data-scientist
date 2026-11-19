"""SQL agent.

Takes the question (+ plan + schema), asks the LLM to write a DuckDB SELECT,
runs it through the guarded `SQLTool`, and **self-corrects**: if the query is
rejected or fails, the error is fed back to the LLM and it retries (a reflection
loop) up to `max_retries` times.

`answer(..., llm=..., sql_tool=...)` accepts injected dependencies so tests run
without a network or a real warehouse.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from ads.core.exceptions import LLMError, RateLimitError, SQLExecutionError, SQLGenerationError
from ads.core.logging import get_logger
from ads.llm.client import BaseLLMClient, get_llm_client
from ads.tools.sql_tool import SQLTool

log = get_logger(__name__)


@dataclass
class SQLAnswer:
    ok: bool
    sql: str = ""
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    attempts: int = 0
    error: str | None = None


SYSTEM = (
    "You are an expert data analyst who writes correct, efficient DuckDB SQL. "
    "You return ONLY a single read-only SELECT statement — no prose, no markdown, "
    "no explanation, no semicolon."
)

PROMPT = """\
Question: {question}

Analysis plan:
{plan}

Database schema (DuckDB):
{schema}

Write ONE DuckDB SELECT query that returns the data needed to answer the
question. Rules:
- Use only tables/columns that exist in the schema.
- Prefer existing dimension columns (e.g. year, quarter, state, region,
  category, product, channel) over computing values from dates when they exist.
- Read-only: SELECT/WITH only. No INSERT/UPDATE/DELETE/DDL.
- Prefer clear column aliases and GROUP BY where aggregating.
- Keep the query concise; avoid unnecessary CTEs and over-engineering.
- Return ONLY the SQL.
{retry}"""


def _clean_sql(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:sql)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned.rstrip(";").strip()


def generate_sql(
    question: str,
    schema: str,
    plan: list[str] | None,
    llm: BaseLLMClient,
    previous_error: str | None = None,
    previous_sql: str | None = None,
) -> str:
    retry = ""
    if previous_error:
        retry = (
            f"\nYour previous query:\n{previous_sql}\n"
            f"failed with error:\n{previous_error}\n"
            "Fix it and return only the corrected SQL."
        )
    prompt = PROMPT.format(
        question=question,
        plan="\n".join(f"- {s}" for s in (plan or [])) or "(no plan)",
        schema=schema,
        retry=retry,
    )
    # Generous token budget: gemini-2.5-flash spends output tokens on reasoning,
    # so a small cap can truncate the SQL mid-statement.
    return _clean_sql(llm.complete(prompt, system=SYSTEM, max_tokens=8000).text)


def answer(
    question: str,
    schema: str | None = None,
    plan: list[str] | None = None,
    llm: BaseLLMClient | None = None,
    sql_tool: SQLTool | None = None,
    max_retries: int = 3,
    max_rows_kept: int = 500,
) -> SQLAnswer:
    """Generate, run and (if needed) self-correct SQL for the question."""
    # Offline guard (test-suite): skip live LLM unless a client is injected.
    if llm is None and os.getenv("ADS_DISABLE_LLM"):
        return SQLAnswer(ok=False, error="LLM disabled (offline)", attempts=0)

    tool = sql_tool or SQLTool()
    schema = schema or tool.get_schema()
    try:
        client = llm or get_llm_client()
    except Exception as exc:  # noqa: BLE001 - e.g. missing/invalid API key
        return SQLAnswer(ok=False, error=f"LLM unavailable: {exc}", attempts=0)

    last_error: str | None = None
    last_sql: str | None = None

    for attempt in range(1, max_retries + 1):
        try:
            sql = generate_sql(question, schema, plan, client, last_error, last_sql)
            last_sql = sql
            log.info("SQL attempt %d", attempt, extra={"sql": sql[:200]})
            df = tool.run(sql)
            records = df.head(max_rows_kept).to_dict("records")
            return SQLAnswer(
                ok=True,
                sql=sql,
                columns=list(df.columns),
                rows=records,
                row_count=len(df),
                attempts=attempt,
            )
        except RateLimitError:
            raise  # don't retry a quota/rate limit — surface it
        except (SQLGenerationError, SQLExecutionError, LLMError) as exc:
            last_error = str(exc)
            log.warning("SQL attempt %d failed: %s", attempt, last_error)

    return SQLAnswer(ok=False, sql=last_sql or "", attempts=max_retries, error=last_error)
