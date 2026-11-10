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
- [x] **Step 2 — Data layer:** DuckDB connection manager, deterministic sample
  sales dataset (with a built-in Maharashtra Q4 drop), seeding routine, and a
  guarded read-only SQL tool. Commands: `python main.py seed`, `python main.py schema`.
- [x] **Step 3 — Workflow skeleton:** shared `GraphState`, LangGraph wiring
  (planner → sql → eda → ml → viz → report), runnable stub nodes.
  Command: `python main.py run "Why did sales drop in Maharashtra last quarter?"`
- [x] **Step 4 — Planner agent:** question + schema -> ordered plan + step flags (Gemini, JSON, fallback).
- [x] **Step 5 — SQL agent:** generate -> validate -> execute with self-correcting retries (Gemini).
- [ ] **Step 6 — EDA agent:** profiling, trend & anomaly detection.
- [ ] **Step 7 — ML agent:** baseline models & driver analysis.
- [ ] **Step 8 — Viz + Report agents:** charts and the executive report.
- [ ] **Step 9 — Advanced:** reflection, memory, human-approval loop.
- [ ] **Step 10 — Streamlit UI.**
- [ ] **Step 11 — Tests, Docker, CI.**

---

## 🧭 Step-by-step build guide (continue on your own machine)

This section is written so a developer **or an AI coding agent (e.g. Antigravity,
Cursor, Claude Code)** can continue the project one step at a time. Steps 1–3 are
done. For each remaining step: create the listed files, implement the described
behaviour, run the test command, then commit.

**Conventions used throughout**
- Package root: `src/ads/`. Config: `config/settings.py`. Entry point: `main.py`.
- Agents read/write a single `GraphState` (`src/ads/graph/state.py`).
- Every node returns a `dict` of updates; list fields (`errors`, `steps_completed`)
  accumulate. Replace the stub in `src/ads/graph/nodes.py` with the real agent.
- Use `get_logger(__name__)` and `bind(log, run_id=...)` for logging — never `print`.
- Call the LLM only through `get_llm_client()` (`src/ads/llm/client.py`).
- Query data only through `SQLTool` (`src/ads/tools/sql_tool.py`) — never raw DuckDB.
- Add a test per step under `tests/`; keep `pytest` green.
- Workflow to run after each step: `python main.py run "<question>"`.

### ✅ Step 1 — Foundation *(done)*
Config, logging, exceptions, provider-agnostic LLM client, CLI. Test: `pytest -k smoke`.

### ✅ Step 2 — Data layer *(done)*
`src/ads/tools/database.py`, `src/ads/data/seed.py`, `src/ads/tools/sql_tool.py`.
Seed: `python main.py seed`. Schema: `python main.py schema`.

### ✅ Step 3 — Workflow skeleton *(done)*
`src/ads/graph/{state,nodes,workflow}.py`. Run: `python main.py run "..."`.

### ✅ Step 4 — Planner agent *(done)*
`src/ads/agents/planner.py` — `plan(question, schema, llm=None) -> PlanResult`
(pydantic: `steps`, `needs_sql`, `needs_ml`, `needs_viz`, `rationale`). Prompts
Gemini for strict JSON, parses defensively (handles ```json fences), and falls
back to a sensible default plan if the LLM is unavailable. Wired into
`planner_node`; `GraphState` gains `needs_ml` / `rationale`. Tests inject a fake
LLM (no network). Test: `pytest -k planner`.

### ✅ Step 5 — SQL agent *(done)*
`src/ads/agents/sql_agent.py` — `answer(question, schema, plan, llm=None, sql_tool=None)`
→ `SQLAnswer(ok, sql, columns, rows, row_count, attempts, error)`. Prompts Gemini
for a single DuckDB SELECT (concise; prefers existing dim columns), runs it via
`SQLTool`, and **self-corrects** by feeding errors back on retry. Uses a larger
token budget (gemini-2.5-flash spends output tokens on reasoning). Wired into
`sql_node`. Tests use a scripted fake LLM + seeded temp DB. Test: `pytest -k sql_agent`.

### ⬜ Step 6 — EDA agent
- **Goal:** profile the result set — summary stats, time trends, group comparisons,
  anomaly/outlier detection — and summarise findings in text.
- **Create:** `src/ads/agents/eda_agent.py` + helpers in `src/ads/tools/eda_tool.py`
  (pandas describe, groupby trends, z-score / IQR anomalies).
- **Wire:** `eda_node` stores `eda` (dict of findings) in state.
- **Test:** feed a DataFrame with a known spike; assert the anomaly is detected.

### ⬜ Step 7 — ML agent
- **Goal:** when `needs_ml`, train a baseline model (regression/classification) to
  find drivers; report feature importances and key metrics.
- **Create:** `src/ads/agents/ml_agent.py` + `src/ads/tools/ml_tool.py`
  (scikit-learn pipeline, train/test split, metrics, feature importance).
- **Wire:** `ml_node` stores `ml` (metrics + drivers). Skip when `plan.needs_ml` is false.
- **Test:** small synthetic dataset; assert a model trains and returns importances.

### ⬜ Step 8 — Visualization + Report agents
- **Goal:** render charts for the findings and compose an executive report.
- **Create:** `src/ads/tools/viz_tool.py` (matplotlib/Plotly → PNG in `artifacts/`),
  `src/ads/agents/report_agent.py` (LLM turns findings into a Markdown report;
  optionally export PDF).
- **Wire:** `viz_node` stores chart paths in `viz`; `report_node` stores `report`.
- **Test:** assert chart files are created and the report mentions the key finding.

### ⬜ Step 9 — Advanced patterns
- **Reflection:** after SQL/EDA, ask the LLM to critique and optionally revise.
- **Memory:** persist run history (SQLite/JSON) keyed by `run_id`.
- **Human approval:** add a LangGraph `interrupt` before report/side-effects when
  `settings.enable_human_approval` is true; resume on approval.
- **Test:** simulate a rejection → `HumanRejectedError`; approval → completes.

### ⬜ Step 10 — Streamlit UI
- **Create:** `app.py` (Streamlit): question box → run workflow → show plan, SQL,
  tables, charts and the report; stream node status.
- **Run:** `streamlit run app.py`.

### ⬜ Step 11 — Tests, Docker, CI, deploy
- **Add:** broader tests, `Dockerfile`, GitHub Actions (lint + test).
- **Deploy (free):** push to GitHub → connect the repo to **Streamlit Community
  Cloud** → set `GOOGLE_API_KEY` as a secret → get a public `*.streamlit.app` URL.

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
