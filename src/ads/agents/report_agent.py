"""Report agent.

Composes an executive Markdown report from everything the pipeline produced
(question, plan, SQL, EDA findings, optional ML results, chart paths). The prose
is LLM-written with an offline template fallback; the report is saved to
`artifacts/report_<run_id>.md`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from config.settings import ARTIFACTS_DIR

from ads.core.logging import get_logger
from ads.llm.client import BaseLLMClient, get_llm_client

log = get_logger(__name__)


@dataclass
class ReportResult:
    markdown: str
    path: str | None = None


SYSTEM = (
    "You are a senior data analyst writing a concise executive report for business "
    "stakeholders. Use clear Markdown with short sections and quantified findings."
)

PROMPT = """\
Write an executive report answering this question:
"{question}"

Analysis plan:
{plan}

Key findings from the data (EDA):
{eda}

Model / driver analysis (if any):
{ml}

Structure the report as Markdown with these sections:
# Executive Report
## Answer (2-3 sentences, direct)
## Key Findings (bullets, quantified)
## Likely Cause / Drivers
## Recommended Actions (2-4 bullets)
{reflection}
Be specific and use the numbers from the findings."""

REFLECTION_SECTION = (
    "## Confidence & Caveats (1-2 bullets: how confident, and any data limitations)\n"
)


def _template_report(question: str, plan, eda: str, ml: str) -> str:
    return (
        f"# Executive Report\n\n"
        f"## Question\n{question}\n\n"
        f"## Key Findings\n{eda or '(no findings)'}\n\n"
        f"## Model / Drivers\n{ml or '(not applicable)'}\n\n"
        f"## Plan\n" + "\n".join(f"- {s}" for s in (plan or []))
    )


def compose(
    question: str,
    plan: list[str] | None,
    eda_narrative: str,
    ml_summary: str,
    charts: list[str] | None = None,
    run_id: str = "run",
    llm: BaseLLMClient | None = None,
) -> ReportResult:
    """Build the report, save it, and return the markdown + path."""
    if llm is None and os.getenv("ADS_DISABLE_LLM"):
        markdown = _template_report(question, plan, eda_narrative, ml_summary)
    else:
        try:
            from config.settings import get_settings

            client = llm or get_llm_client()
            reflection = REFLECTION_SECTION if get_settings().enable_reflection else ""
            prompt = PROMPT.format(
                question=question,
                plan="\n".join(f"- {s}" for s in (plan or [])) or "(none)",
                eda=eda_narrative or "(none)",
                ml=ml_summary or "(not applicable)",
                reflection=reflection,
            )
            markdown = client.complete(prompt, system=SYSTEM, max_tokens=4000).text.strip()
            if not markdown:
                raise ValueError("empty report")
        except Exception as exc:  # noqa: BLE001
            log.warning("Report via LLM failed, using template: %s", exc)
            markdown = _template_report(question, plan, eda_narrative, ml_summary)

    if charts:
        markdown += "\n\n## Charts\n" + "\n".join(f"- `{c}`" for c in charts)

    path = None
    try:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        out = ARTIFACTS_DIR / f"report_{run_id}.md"
        out.write_text(markdown, encoding="utf-8")
        path = str(out)
        log.info("Saved report: %s", out)
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not save report: %s", exc)

    return ReportResult(markdown=markdown, path=path)
