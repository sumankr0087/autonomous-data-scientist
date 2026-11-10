"""Pytest configuration: make `src/` importable."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

# Keep the test-suite hermetic: no live LLM calls unless a client is injected.
os.environ["ADS_DISABLE_LLM"] = "1"
