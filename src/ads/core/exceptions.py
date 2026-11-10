"""Typed exception hierarchy for the Autonomous Data Scientist.

A single base (`ADSError`) lets callers catch everything from this system while
still allowing fine-grained handling per failure domain (config, LLM, SQL,
tools, agents, workflow).
"""

from __future__ import annotations


class ADSError(Exception):
    """Base class for all application errors."""

    def __init__(self, message: str, *, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.message}" + (f" ({self.details})" if self.details else "")


class ConfigError(ADSError):
    """Missing or invalid configuration (e.g. no API key for the provider)."""


class LLMError(ADSError):
    """The LLM provider failed, timed out, or returned an unusable response."""


class SQLGenerationError(ADSError):
    """The agent could not produce valid SQL for the question."""


class SQLExecutionError(ADSError):
    """A generated query failed to execute against the database."""


class ToolError(ADSError):
    """A tool (EDA, ML, visualization, report) failed during execution."""


class AgentError(ADSError):
    """An agent node failed irrecoverably."""


class WorkflowError(ADSError):
    """The orchestration graph failed or exceeded its step budget."""


class HumanRejectedError(ADSError):
    """The human-in-the-loop approval step rejected the proposed action."""
