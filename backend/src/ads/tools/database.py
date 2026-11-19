"""DuckDB connection manager.

A thin, safe wrapper around DuckDB used by every data tool. Queries return
pandas DataFrames; schema introspection feeds the SQL agent's prompt.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import duckdb
import pandas as pd

from config.settings import get_settings

from ads.core.exceptions import SQLExecutionError
from ads.core.logging import get_logger

log = get_logger(__name__)


class Database:
    """Manages access to the DuckDB warehouse file."""

    def __init__(self, path: str | None = None) -> None:
        self.path = str(path or get_settings().duckdb_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self, read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
        """Yield a DuckDB connection, always closed afterwards."""
        con = duckdb.connect(self.path, read_only=read_only)
        try:
            yield con
        finally:
            con.close()

    def exists(self) -> bool:
        return Path(self.path).exists()

    def execute_df(self, sql: str, params: list[Any] | None = None) -> pd.DataFrame:
        """Run a read-only query and return the result as a DataFrame."""
        try:
            with self.connect(read_only=True) as con:
                return con.execute(sql, params or []).fetch_df()
        except Exception as exc:  # noqa: BLE001
            raise SQLExecutionError("Query failed", details=str(exc)) from exc

    def write_df(self, df: pd.DataFrame, table: str, replace: bool = True) -> int:
        """Create (or replace) a table from a DataFrame. Returns row count."""
        with self.connect(read_only=False) as con:
            con.register("_tmp_df", df)
            verb = "CREATE OR REPLACE TABLE" if replace else "CREATE TABLE IF NOT EXISTS"
            con.execute(f"{verb} {table} AS SELECT * FROM _tmp_df")
            con.unregister("_tmp_df")
        log.info("Wrote table", extra={"table": table, "rows": len(df)})
        return len(df)

    def list_tables(self) -> list[str]:
        if not self.exists():
            return []
        with self.connect(read_only=True) as con:
            rows = con.execute("SHOW TABLES").fetchall()
        return [r[0] for r in rows]

    def schema_text(self) -> str:
        """Return a compact text description of all tables & columns for the LLM."""
        if not self.exists() or not self.list_tables():
            return "(no tables — run `python main.py seed` first)"
        lines: list[str] = []
        with self.connect(read_only=True) as con:
            for table in self.list_tables():
                cols = con.execute(f"PRAGMA table_info('{table}')").fetchall()
                col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
                lines.append(f"- {table}({col_desc})")
        return "\n".join(lines)
