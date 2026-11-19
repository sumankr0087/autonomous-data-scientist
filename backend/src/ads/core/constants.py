"""Project-wide constants and enums."""

from __future__ import annotations

from enum import Enum


class AgentName(str, Enum):
    """Canonical names for every agent/node in the workflow graph."""

    PLANNER = "planner"
    SQL = "sql_agent"
    EDA = "eda_agent"
    ML = "ml_agent"
    VIZ = "viz_agent"
    REPORT = "report_agent"


class StepStatus(str, Enum):
    """Lifecycle status for a single workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_APPROVAL = "awaiting_approval"


# Application version (single source of truth).
VERSION = "0.1.0"
