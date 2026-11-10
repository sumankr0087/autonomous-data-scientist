"""SQL tool used by the SQL agent.

Responsibilities
----------------
- `get_schema()`  : describe tables/columns so the LLM can write correct SQL.
- `validate()`    : allow only read-only (SELECT/WITH) single statements.
- `run()`         : execute a validated query and return a DataFrame.
- `sample()`      : preview rows from a table.

The validation layer is a safety guardrail: generated SQL is never allowed to
mutate the warehouse.
"""

from __future__ import annotations

import re

import pandas as pd

from ads.core.exceptions import SQLGenerationError
from ads.core.logging import get_logger
from ads.tools.database import Database

log = get_logger(__name__)

# Any of these keywords (as whole words) makes a statement non-read-only.
_FORBIDDEN = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "attach",
    "detach",
    "copy",
    "pragma",
    "install",
    "load",
    "export",
    "import",
    "grant",
    "set",
)


class SQLTool:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()

    # --- schema helpers -------------------------------------------------
    def get_schema(self) -> str:
        return self.db.schema_text()

    def sample(self, table: str, n: int = 5) -> pd.DataFrame:
        return self.db.execute_df(f"SELECT * FROM {table} LIMIT {int(n)}")

    # --- validation + execution ----------------------------------------
    def validate(self, sql: str) -> str:
        """Return cleaned SQL if it is a safe single read-only statement."""
        cleaned = sql.strip().rstrip(";").strip()
        if not cleaned:
            raise SQLGenerationError("Empty SQL statement")

        # Only one statement allowed.
        if ";" in cleaned:
            raise SQLGenerationError("Multiple SQL statements are not allowed")

        lowered = cleaned.lower()
        if not (lowered.startswith("select") or lowered.startswith("with")):
            raise SQLGenerationError("Only SELECT/WITH queries are allowed")

        for word in _FORBIDDEN:
            if re.search(rf"\b{word}\b", lowered):
                raise SQLGenerationError(f"Forbidden keyword in query: '{word}'")
        return cleaned

    def run(self, sql: str, max_rows: int = 10000) -> pd.DataFrame:
        cleaned = self.validate(sql)
        log.info("Executing SQL", extra={"sql": cleaned[:200]})
        df = self.db.execute_df(cleaned)
        if len(df) > max_rows:
            log.warning("Result truncated", extra={"rows": len(df), "max_rows": max_rows})
            df = df.head(max_rows)
        return df
