"""Static catalog: example questions and the selectable LLM provider/model list."""

from __future__ import annotations

EXAMPLES = [
    "Why did sales drop in Maharashtra last quarter?",
    "Which product categories grew the most in 2025?",
    "What factors drive revenue? Predict the key drivers.",
    "Compare online vs retail vs partner channel revenue by region.",
]

# Models shown in the UI dropdown (only those with a server-side key actually appear).
# Order = priority. Groq (strong) is first, so it is the default on initial render;
# Gemini is the lightweight fallback.
PROVIDER_CATALOG = [
    {"id": "groq", "label": "Groq · GPT-OSS 120B (strong, free)", "model": "openai/gpt-oss-120b"},
    {"id": "groq", "label": "Groq · GPT-OSS 20B (fastest)", "model": "openai/gpt-oss-20b"},
    {"id": "gemini", "label": "Google Gemini · Flash-Lite", "model": "gemini-flash-lite-latest"},
]


def default_model(provider: str) -> str:
    """Return the first catalog model id for a provider, or empty string."""
    for p in PROVIDER_CATALOG:
        if p["id"] == provider:
            return p["model"]
    return ""
