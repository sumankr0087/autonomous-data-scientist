"""Project entry point.

Adds `src/` to the path so the `ads` package is importable without an editable
install, then delegates to the CLI. Run `python main.py check` to validate setup.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ads.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
