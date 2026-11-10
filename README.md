# 🤖 Autonomous Data Scientist Agent

A production-grade, multi-agent AI system that turns a plain-English **business
question** into a full data-science workflow — **SQL → EDA → ML → visualization →
executive report** — with no SQL, Python or ML knowledge required from the user.

> Example: _"Why did sales drop in Maharashtra last quarter?"_ → the system
> queries the warehouse, analyses trends, detects anomalies, trains models,
> generates charts, and writes a business-ready report.

---

## ✨ What it does

| Capability | Description |
|---|---|
| Understands a question | Planner agent decomposes intent into a step plan |
| Generates SQL | SQL agent writes & validates queries against DuckDB |
| Performs EDA | EDA agent profiles data, finds trends & anomalies |
| Trains ML models | ML agent builds baseline models for prediction/drivers |
| Creates visualizations | Viz agent produces charts for the findings |
| Writes insights | Report agent composes an executive summary |

**Advanced patterns:** reflection, tool-calling, memory, multi-agent
orchestration, and a human-in-the-loop approval gate.

---

## 🏗️ Architecture

Multi-agent workflow orchestrated with **LangGraph**. A shared, typed state
object flows through specialised agent nodes; each node reads the state, calls
its tools, and writes results back.

```
                         ┌──────────────┐
   business question ───▶│   Planner    │  decompose → step plan
                         └──────┬───────┘
                                ▼
                         ┌──────────────┐     ┌───────────────┐
                         │  SQL Agent   │────▶│ DuckDB (tool) │
                         └──────┬───────┘     └───────────────┘
                                ▼
                         ┌──────────────┐
                         │  EDA Agent   │  trends · anomalies · profile
                         └──────┬───────┘
                                ▼
                         ┌──────────────┐
                         │   ML Agent   │  baseline models · drivers
                         └──────┬───────┘
                                ▼
                         ┌──────────────┐
                         │  Viz Agent   │  charts / figures
                         └──────┬───────┘
                                ▼
                         ┌──────────────┐
                         │ Report Agent │──▶ executive report (Markdown/PDF)
                         └──────┬───────┘
                                ▼
                     human approval loop ⟲ (optional, before side-effects)
```

### Project layout

```
autonomous-data-scientist/
├── main.py                 # entry point (adds src/ to path → CLI)
├── config/
│   └── settings.py         # typed settings (pydantic-settings, .env)
├── src/ads/
│   ├── core/               # logging, exceptions, constants
│   ├── llm/                # provider-agnostic LLM client (openai/anthropic)
│   ├── tools/              # SQL, EDA, ML, viz tools        (later steps)
│   ├── agents/             # planner, sql, eda, ml, report  (later steps)
│   ├── graph/              # LangGraph state + workflow      (later steps)
│   └── cli.py              # CLI commands (check / run)
├── data/                   # DuckDB warehouse + sample data  (later steps)
├── logs/                   # rotating logs (app.log / app.jsonl)
├── artifacts/              # generated charts & reports      (later steps)
└── tests/                  # pytest suite
```

### Tech stack

LangGraph · LangChain · OpenAI / Anthropic · DuckDB · pandas · scikit-learn ·
matplotlib / Plotly · Streamlit · Pydantic · Rich.

---

## 🚦 Build roadmap (step by step)

- [x] **Step 1 — Foundation:** project scaffold, typed config, production logging
  (console + rotating file, JSON option), exception hierarchy, provider-agnostic
  LLM client, runnable CLI + smoke tests.
- [ ] **Step 2 — Data layer:** DuckDB connection, sample dataset seeding, SQL tool.
- [ ] **Step 3 — Workflow skeleton:** shared `GraphState`, LangGraph wiring, node stubs.
- [ ] **Step 4 — Planner agent:** question → structured plan.
- [ ] **Step 5 — SQL agent:** generate → validate → execute, with retries.
- [ ] **Step 6 — EDA agent:** profiling, trend & anomaly detection.
- [ ] **Step 7 — ML agent:** baseline models & driver analysis.
- [ ] **Step 8 — Viz + Report agents:** charts and the executive report.
- [ ] **Step 9 — Advanced:** reflection, memory, human-approval loop.
- [ ] **Step 10 — Streamlit UI.**
- [ ] **Step 11 — Tests, Docker, CI.**

---

## 🛠️ Getting started

```bash
# 1. Create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env        # then add your API key

# 4. Validate the setup
python main.py check
```

`python main.py check` loads the config, initialises logging, verifies runtime
directories, and reports whether the environment is ready.

### Run the tests

```bash
pytest
```

---

## ⚙️ Configuration

All settings come from environment variables / `.env` (see `.env.example`):
`LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`,
`LOG_LEVEL`, `LOG_JSON`, `DUCKDB_PATH`, `MAX_AGENT_STEPS`,
`ENABLE_HUMAN_APPROVAL`, `ENABLE_REFLECTION`.

## 📋 Logging

Structured logging is configured once at startup: colourised console output (via
Rich) plus a rotating file handler at `logs/app.log` (or `app.jsonl` when
`LOG_JSON=true`). Attach context with `bind(log, run_id=...)` so every line for a
run is traceable.

## 📄 License

MIT © Suman Kumar
