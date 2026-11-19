"""Tests for the Step 4 Planner agent (no network — fake LLM injected)."""

from __future__ import annotations

from ads.agents.planner import PlanResult, plan
from ads.llm.client import BaseLLMClient, LLMResponse


class FakeLLM(BaseLLMClient):
    def __init__(self, text: str) -> None:  # noqa: D107
        self.text = text

    def complete(self, prompt, *, system=None, **kwargs):  # noqa: D102
        return LLMResponse(text=self.text, model="fake")


SCHEMA = "- sales(state VARCHAR, quarter VARCHAR, revenue DOUBLE)"


def test_plan_parses_clean_json():
    llm = FakeLLM(
        '{"steps":["q","eda","report"],"needs_sql":true,"needs_ml":true,'
        '"needs_viz":true,"rationale":"ok"}'
    )
    result = plan("Why did sales drop?", SCHEMA, llm=llm)
    assert isinstance(result, PlanResult)
    assert result.steps == ["q", "eda", "report"]
    assert result.needs_ml is True


def test_plan_parses_json_with_markdown_fences():
    llm = FakeLLM('```json\n{"steps":["a","b"],"needs_ml":false}\n```')
    result = plan("How many orders?", SCHEMA, llm=llm)
    assert result.steps == ["a", "b"]
    assert result.needs_ml is False


def test_plan_falls_back_on_garbage():
    llm = FakeLLM("sorry, I cannot help with that")
    result = plan("Why did sales drop?", SCHEMA, llm=llm)
    # Default plan kicks in; "why" implies ML.
    assert result.steps
    assert result.needs_ml is True
    assert "Default plan" in result.rationale


def test_default_plan_skips_ml_for_simple_lookup():
    llm = FakeLLM("not json")
    result = plan("How many orders in total?", SCHEMA, llm=llm)
    assert result.needs_ml is False
