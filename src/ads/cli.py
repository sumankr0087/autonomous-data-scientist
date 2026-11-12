"""Command-line entry point for the Autonomous Data Scientist.

Step 1 scope: bootstrap the application — load config, initialise logging, run a
self-check and print a startup banner. The actual agent workflow (`run`) is
wired up in later steps; for now it reports that it is not yet implemented so the
CLI is runnable end to end.
"""

from __future__ import annotations

import argparse
import sys

from config.settings import get_settings

from ads.core.constants import VERSION
from ads.core.exceptions import ADSError
from ads.core.logging import bind, get_logger, setup_logging

log = get_logger(__name__)

BANNER = r"""
   _   _   _ _____ ___  _   _  ___  __  __  ___  _   _ ___
  /_\ | | | |_   _/ _ \| \ | |/ _ \|  \/  |/ _ \| | | / __|
 / _ \| |_| | | || (_) | .  | (_) | |\/| | (_) | |_| \__ \
/_/ \_\\___/  |_| \___/|_|\_|\___/|_|  |_|\___/ \___/|___/
        Autonomous Data Scientist Agent  v{version}
""".format(version=VERSION)


def self_check() -> int:
    """Validate the environment and configuration. Returns an exit code."""
    settings = get_settings()
    log.info("Running self-check", extra={"environment": settings.environment})

    ok = True

    # 1. API key presence (warn only — not required to boot).
    if not settings.active_api_key:
        log.warning(
            "No API key configured for provider '%s' — set it in .env before running the agent.",
            settings.llm_provider,
        )
    else:
        log.info("LLM provider configured", extra={"provider": settings.llm_provider})

    # 2. Runtime directories.
    from config.settings import ARTIFACTS_DIR, DATA_DIR, LOGS_DIR

    for directory in (LOGS_DIR, DATA_DIR, ARTIFACTS_DIR):
        if not directory.exists():
            log.error("Required directory missing: %s", directory)
            ok = False
    if ok:
        log.info("Runtime directories present")

    log.info("Self-check %s", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def cmd_seed(args: argparse.Namespace) -> int:
    """Generate the sample dataset and load it into DuckDB."""
    from ads.data.seed import seed_database
    from ads.tools.database import Database

    db = Database()
    log.info("Seeding sample warehouse at %s", db.path)
    counts = seed_database(db)
    for table, n in counts.items():
        log.info("  %-10s %6d rows", table, n)
    log.info("Seed complete. Tables: %s", ", ".join(db.list_tables()))
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    """Print the warehouse schema (what the SQL agent sees)."""
    from ads.tools.sql_tool import SQLTool

    print(SQLTool().get_schema())
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run the agent workflow against a business question."""
    import sys as _sys

    from config.settings import get_settings
    from ads.graph.workflow import run_workflow

    approver = None
    if get_settings().enable_human_approval and not args.yes and _sys.stdin.isatty():
        def approver(state):  # noqa: ANN001
            print("\n--- Human approval ---")
            print(f"Plan: {state.get('plan')}")
            print(f"SQL rows: {state.get('row_count')}")
            return input("Proceed to generate the report? [Y/n] ").strip().lower() in ("", "y", "yes")

    result = run_workflow(args.question, approver=approver)
    print("\n" + "=" * 60)
    print(f"Question : {args.question}")
    print(f"Status   : {result.get('status')}")
    print(f"Steps    : {' -> '.join(result.get('steps_completed', []))}")
    print("-" * 60)
    print("PLAN (from the Planner agent):")
    if result.get("rationale"):
        print(f"  rationale : {result['rationale']}")
    print(f"  needs_ml  : {result.get('needs_ml')}")
    for i, step in enumerate(result.get("plan", []), 1):
        print(f"  {i}. {step}")

    if result.get("sql"):
        print("-" * 60)
        print(f"SQL (rows={result.get('row_count', 0)}):")
        print(f"  {result['sql']}")

    eda = result.get("eda") or {}
    if eda.get("narrative"):
        print("-" * 60)
        print("EDA — key findings:")
        print(eda["narrative"])

    print("=" * 60)
    print(result.get("report", "(no report)"))
    return 0 if result.get("status") == "completed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ads",
        description="Autonomous Data Scientist Agent",
    )
    parser.add_argument("--version", action="version", version=f"ads {VERSION}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="Validate configuration and environment.")
    sub.add_parser("seed", help="Generate the sample dataset into DuckDB.")
    sub.add_parser("schema", help="Print the warehouse schema.")

    sub.add_parser("history", help="List recent runs from memory.")

    run_p = sub.add_parser("run", help="Answer a business question end to end.")
    run_p.add_argument("question", help="A natural-language business question.")
    run_p.add_argument("--yes", action="store_true", help="Skip human approval prompt.")

    return parser


def cmd_history(args: argparse.Namespace) -> int:
    from ads.core.memory import list_runs

    runs = list_runs(20)
    if not runs:
        print("No runs yet.")
        return 0
    for r in runs:
        print(f"- [{r.get('status')}] {r.get('question')}  ({r.get('run_id')})")
    return 0


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    sys.stdout.write(BANNER + "\n")

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "check" or args.command is None:
            return self_check()
        if args.command == "seed":
            return cmd_seed(args)
        if args.command == "schema":
            return cmd_schema(args)
        if args.command == "history":
            return cmd_history(args)
        if args.command == "run":
            return cmd_run(args)
        parser.print_help()
        return 0
    except ADSError as exc:
        log.error("Application error: %s", exc)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        log.warning("Interrupted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
