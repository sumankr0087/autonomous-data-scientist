"""Streamlit UI for the Autonomous Data Scientist.

Run locally:   streamlit run app.py
Deploy (free): Streamlit Community Cloud -> set GOOGLE_API_KEY in Secrets.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from config.settings import get_settings  # noqa: E402

from ads.core.memory import list_runs  # noqa: E402
from ads.data.seed import seed_database  # noqa: E402
from ads.graph.workflow import run_workflow  # noqa: E402
from ads.tools.database import Database  # noqa: E402

st.set_page_config(page_title="Autonomous Data Scientist", page_icon="🤖", layout="wide")

# On Streamlit Cloud the key comes from st.secrets; mirror it into the env.
try:
    if "GOOGLE_API_KEY" in st.secrets and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass

EXAMPLES = [
    "Why did sales drop in Maharashtra last quarter?",
    "Which product categories grew the most in 2025?",
    "What factors drive revenue? Predict the key drivers.",
    "Compare online vs retail vs partner channel revenue by region.",
]

st.title("🤖 Autonomous Data Scientist")
st.caption("Ask a business question → the agents generate SQL, analyse the data, "
           "train a model if needed, draw a chart, and write an executive report.")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Setup")
    settings = get_settings()
    db = Database()
    seeded = db.exists() and bool(db.list_tables())
    st.write(f"**Provider:** {settings.llm_provider} · `{settings.llm_model}`")
    if not settings.active_api_key:
        st.error("No API key set. Add GOOGLE_API_KEY to your environment / Secrets.")
    st.write(f"**Warehouse:** {'✅ seeded' if seeded else '❌ not seeded'}")
    if not seeded and st.button("Seed sample data"):
        with st.spinner("Seeding sample sales data..."):
            seed_database(db)
        st.rerun()

    st.divider()
    st.subheader("💡 Examples")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            st.session_state["question"] = ex

    st.divider()
    st.subheader("🕑 Recent runs")
    for r in list_runs(8):
        st.caption(f"{r.get('status', '?')} · {r.get('question', '')[:48]}")

# --- Main ---
question = st.text_input("Business question", value=st.session_state.get("question", ""))
go = st.button("Run analysis", type="primary", disabled=not question)

if go and question:
    if not Database().exists() or not Database().list_tables():
        st.warning("Please seed the sample data first (button in the sidebar).")
        st.stop()
    if not get_settings().active_api_key:
        st.error("No API key configured — set GOOGLE_API_KEY to run the agents.")
        st.stop()

    with st.spinner("Agents working: planning → SQL → EDA → ML → charts → report…"):
        result = run_workflow(question)

    if result.get("status") == "completed":
        st.success(f"Done — steps: {' → '.join(result.get('steps_completed', []))}")
    else:
        st.warning(f"Finished with status: {result.get('status')}")

    tab_report, tab_plan, tab_sql, tab_eda, tab_ml, tab_chart = st.tabs(
        ["📄 Report", "🧠 Plan", "🗃️ SQL & Data", "📊 EDA", "🤖 ML", "📈 Chart"]
    )

    with tab_report:
        st.markdown(result.get("report", "_No report_"))

    with tab_plan:
        st.write(f"**Rationale:** {result.get('rationale', '')}")
        st.write(f"**Needs ML:** {result.get('needs_ml')}")
        for i, step in enumerate(result.get("plan", []), 1):
            st.write(f"{i}. {step}")

    with tab_sql:
        st.code(result.get("sql", "-- no SQL"), language="sql")
        rows = result.get("query_result", [])
        if rows:
            st.caption(f"{result.get('row_count', len(rows))} rows")
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tab_eda:
        st.markdown((result.get("eda") or {}).get("narrative", "_No EDA_"))

    with tab_ml:
        ml = result.get("ml") or {}
        if ml.get("ran"):
            st.write(ml.get("summary", ""))
            imp = ml.get("importances")
            if imp:
                st.dataframe(pd.DataFrame(imp), use_container_width=True)
        else:
            st.info(ml.get("summary", "ML was not required for this question."))

    with tab_chart:
        charts = result.get("viz", [])
        if charts:
            for c in charts:
                if Path(c).exists():
                    st.image(c, use_container_width=True)
        else:
            st.info("No chart generated for this result.")
