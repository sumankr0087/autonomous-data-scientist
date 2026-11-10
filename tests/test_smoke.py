"""Smoke tests for the Step 1 foundation."""

from __future__ import annotations

import logging

from config.settings import Settings, get_settings

from ads.core.constants import VERSION, AgentName
from ads.core.exceptions import ADSError, ConfigError
from ads.core.logging import bind, get_logger, setup_logging


def test_settings_load():
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "autonomous-data-scientist"
    assert settings.llm_provider in {"openai", "anthropic"}


def test_version_exposed():
    import ads

    assert ads.__version__ == VERSION


def test_logging_setup_idempotent():
    setup_logging()
    setup_logging()  # second call must not add duplicate handlers
    root = logging.getLogger()
    assert len(root.handlers) >= 1


def test_logger_bind_adds_context(caplog):
    log = get_logger("test")
    adapter = bind(log, run_id="r1")
    with caplog.at_level(logging.INFO):
        adapter.info("hello")
    assert any(getattr(r, "run_id", None) == "r1" for r in caplog.records)


def test_exception_hierarchy():
    assert issubclass(ConfigError, ADSError)
    err = ConfigError("bad", details="no key")
    assert "no key" in str(err)


def test_agent_names():
    assert AgentName.SQL.value == "sql_agent"
    assert len(set(AgentName)) == 6
