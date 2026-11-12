<!-- Hugging Face Spaces metadata (used when this repo is deployed as a Docker Space) -->
---
title: Autonomous Data Scientist API
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

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
- [x] **Step 6 — EDA agent:** deterministic profiling + anomaly detection + LLM narrative.
- [x] **Step 7 — ML agent:** baseline RandomForest, metrics + feature importances (runs when needs_ml).
- [x] **Step 8 — Viz + Report agents:** matplotlib charts + LLM executive report saved to artifacts/
- [x] **Step 9 — Advanced:** reflection, run memory, human-approval gate.
- [x] **Step 10 — Streamlit UI** (app.py).
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

### ✅ Step 6 — EDA agent *(done)*
`src/ads/tools/eda_tool.py` — deterministic `analyze_dataframe(df)` → findings
(shape, numeric summaries, focus-metric extremes, IQR anomalies). `src/ads/agents/eda_agent.py`
— `analyze(data, question, llm=None) -> EdaResult(findings, narrative)`: the stats
are deterministic, the narrative is LLM-written with an offline template fallback.
Wired into `eda_node` (stores `eda = {findings, narrative}`). Test: `pytest -k eda`.

### ✅ Step 7 — ML agent *(done)*
`src/ads/tools/ml_tool.py` — `train_baseline(df, target)` → `MlOutcome` (auto task
detection, one-hot encoding, RandomForest, metrics + ranked feature importances).
`src/ads/agents/ml_agent.py` — `run_ml(data, question)` → `MlResult`. Runs only
when `needs_ml` (else `ml_node` skips). Test: `pytest -k ml_report`.

### ✅ Step 8 — Visualization + Report agents *(done)*
`src/ads/tools/viz_tool.py` — headless matplotlib `make_charts()` → PNG(s) of the
top movers in `artifacts/`. `src/ads/agents/report_agent.py` — `compose(...)`
writes an executive Markdown report (LLM + offline fallback) to
`artifacts/report_<run_id>.md`. Wired into `viz_node` / `report_node`; the `run`
command prints the SQL, EDA findings and final report. Test: `pytest -k ml_report`.

### ✅ Step 9 — Advanced patterns *(done)*
**Reflection:** the report includes a "Confidence & Caveats" section when
`enable_reflection`. **Memory:** `src/ads/core/memory.py` persists each run to
`artifacts/history/<run_id>.json` (`python main.py history`, or the UI sidebar).
**Human approval:** `report_node` consults an approver before the final report when
`enable_human_approval`; the CLI prompts interactively (`--yes` to skip), the UI
auto-approves. Test: `pytest -k memory`.

### ✅ Step 10 — Streamlit UI *(done)*
`app.py` — question box, example buttons, seed button, recent-runs sidebar, and
tabbed results (Report / Plan / SQL & Data / EDA / ML / Chart). Run: `streamlit run app.py`.

### ✅ Step 11 — Infra + deploy *(done)*
`Dockerfile`, `.streamlit/config.toml`, `.github/workflows/ci.yml` (offline pytest),
a static showcase in `site/` deployed to GitHub Pages via
`.github/workflows/pages.yml`, and Streamlit-Cloud deploy steps below.

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

## 🚀 Deployment

The app has a **Python backend** (the agents + your API key) and a **static
frontend**. The backend can't run on GitHub Pages, so it's a two-part deploy:

### 1. Backend → Hugging Face Spaces (free) — FastAPI
1. Create a new **Space** at <https://huggingface.co/new-space> → SDK **Docker** →
   name it `autonomous-data-scientist`.
2. In the Space → **Settings → Variables and secrets** → add secret
   **`GOOGLE_API_KEY`**.
3. Push this repo to the Space (it builds the `Dockerfile`, serving the API on
   port 7860):
   ```bash
   git remote add space https://huggingface.co/spaces/<your-hf-username>/autonomous-data-scientist
   git push space main
   ```
4. The API is live at `https://<your-hf-username>-autonomous-data-scientist.hf.space`.

(Alternative: **Render** — `render.yaml` is included; New → Blueprint → add
`GOOGLE_API_KEY`. Any host that runs `uvicorn api:app` works.)

### 2. Frontend (React/Next) → GitHub Pages
The `web/` Next.js app is built & published by `.github/workflows/pages.yml` →
`https://sumankr0087.github.io/autonomous-data-scientist/`.
- One-time: repo **Settings → Pages → Source: GitHub Actions** (the workflow also
  auto-enables it).
- Point the frontend at your backend **either** by setting a repo **Variable**
  `API_URL` (Settings → Secrets and variables → Actions → Variables) before the
  build, **or** by opening the site and entering the backend URL in the ⚙ settings
  (saved in your browser).

### Also available: Streamlit (one-click, all-in-one)
`app.py` is a complete Streamlit UI — deploy on
[Streamlit Community Cloud](https://share.streamlit.io) (main file `app.py`, add
`GOOGLE_API_KEY` to Secrets) for a single `*.streamlit.app` URL with no separate
backend.

### Run locally

```bash
# backend
pip install -r requirements.txt
python main.py seed
uvicorn api:app --reload                 # http://localhost:8000

# frontend (new terminal)
cd web && npm install && npm run dev      # http://localhost:3000
```

### Docker (Streamlit variant)

```bash
docker build -t ads .
docker run -p 8501:8501 -e GOOGLE_API_KEY=your-key ads
```

## 📄 License

MIT © Suman Kumar
