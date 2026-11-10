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


def cmd_run(args: argparse.Namespace) -> int:
    """Run the agent workflow against a business question (later steps)."""
    run_log = bind(log, run_id="cli")
    run_log.info("Received question: %s", args.question)
    run_log.warning(
        "The agent workflow is not implemented yet (Step 1 = foundation). "
        "SQL / EDA / ML / report agents are added in the next steps."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ads",
        description="Autonomous Data Scientist Agent",
    )
    parser.add_argument("--version", action="version", version=f"ads {VERSION}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="Validate configuration and environment.")

    run_p = sub.add_parser("run", help="Answer a business question (coming in later steps).")
    run_p.add_argument("question", help="A natural-language business question.")

    return parser


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    sys.stdout.write(BANNER + "\n")

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "check" or args.command is None:
            return self_check()
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
