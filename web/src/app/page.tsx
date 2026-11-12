"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { FiPlay, FiSettings, FiLoader } from "react-icons/fi";

const EXAMPLES = [
  "Why did sales drop in Maharashtra last quarter?",
  "Which product categories grew the most in 2025?",
  "What factors drive revenue? Predict the key drivers.",
  "Compare online vs retail vs partner channel revenue by region.",
];

const DEFAULT_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RunResult = {
  status: string;
  plan: string[];
  needs_ml: boolean;
  rationale: string;
  sql: string;
  row_count: number;
  columns: string[];
  rows: Record<string, unknown>[];
  eda: string;
  ml: { ran: boolean; summary: string; importances?: { feature: string; importance: number }[] };
  report: string;
  charts: string[];
};

const TABS = ["Report", "Plan", "SQL & Data", "EDA", "ML", "Chart"] as const;

export default function Home() {
  const [apiBase, setApiBase] = useState(DEFAULT_API);
  const [showSettings, setShowSettings] = useState(false);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<RunResult | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]>("Report");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("ads_api_base");
      if (saved) setApiBase(saved);
    } catch {}
  }, []);

  function saveApiBase(v: string) {
    setApiBase(v);
    try {
      localStorage.setItem("ads_api_base", v);
    } catch {}
  }

  async function run() {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${apiBase.replace(/\/$/, "")}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const data = await res.json();
      if (data.status === "error") {
        setError(`Backend error: ${data.error}`);
        return;
      }
      setResult(data);
      setTab("Report");
    } catch (e) {
      setError(
        `Could not reach the backend at ${apiBase}. Make sure the FastAPI server is running and the URL is set (⚙).`
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <header className="mb-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold">
              🤖 <span className="pink-text">Autonomous Data Scientist</span>
            </h1>
            <p className="text-sm text-neutral-600 mt-2 max-w-2xl">
              Ask a business question — the agents generate SQL, analyse the data, train a
              model if needed, draw a chart, and write an executive report.
            </p>
          </div>
          <button
            onClick={() => setShowSettings((v) => !v)}
            className="text-neutral-500 hover:text-violet-600 p-2"
            aria-label="Settings"
          >
            <FiSettings size={20} />
          </button>
        </div>

        {showSettings && (
          <div className="card p-4 mt-4">
            <label className="text-xs uppercase tracking-wider text-neutral-500">
              Backend API URL
            </label>
            <input
              value={apiBase}
              onChange={(e) => saveApiBase(e.target.value)}
              placeholder="https://your-api.onrender.com"
              className="mt-1 w-full bg-neutral-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
            />
            <p className="text-xs text-neutral-500 mt-2">
              Deploy the FastAPI backend (see repo README) and paste its URL here. Saved in your browser.
            </p>
          </div>
        )}
      </header>

      {/* Examples */}
      <div className="flex flex-wrap gap-2 mb-4">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setQuestion(ex)}
            className="text-xs card px-3 py-1.5 hover:border-violet-400 transition text-neutral-700"
          >
            {ex}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Ask a business question…"
          className="flex-1 card px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
        />
        <button onClick={run} disabled={loading || !question.trim()} className="btn-primary flex items-center gap-2">
          {loading ? <FiLoader className="animate-spin" /> : <FiPlay />}
          {loading ? "Running…" : "Run"}
        </button>
      </div>

      {error && <div className="mt-4 card p-4 text-sm text-red-600 border-red-200">{error}</div>}

      {loading && (
        <div className="mt-6 text-sm text-neutral-500">
          Agents working: planning → SQL → EDA → ML → chart → report… (first run may take ~20s)
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="mt-6">
          <div className="text-xs text-emerald-600 mb-3">
            Status: {result.status}
          </div>
          <div className="flex gap-1 border-b border-black/10 mb-4 overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-3 py-2 text-sm whitespace-nowrap ${
                  tab === t ? "text-violet-700 border-b-2 border-violet-600 font-semibold" : "text-neutral-500"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {tab === "Report" && (
            <div className="prose-report card p-5 text-sm">
              <ReactMarkdown>{result.report || "_No report_"}</ReactMarkdown>
            </div>
          )}

          {tab === "Plan" && (
            <div className="card p-5 text-sm">
              <p className="text-neutral-600 mb-2">
                <strong>Rationale:</strong> {result.rationale}
              </p>
              <p className="text-neutral-600 mb-3">
                <strong>Needs ML:</strong> {String(result.needs_ml)}
              </p>
              <ol className="list-decimal pl-5 space-y-1">
                {result.plan?.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </div>
          )}

          {tab === "SQL & Data" && (
            <div className="card p-5">
              <pre className="text-xs overflow-auto bg-neutral-50 p-3 rounded-lg">{result.sql}</pre>
              <p className="text-xs text-neutral-500 my-2">{result.row_count} rows</p>
              {result.rows?.length > 0 && (
                <div className="overflow-auto max-h-80">
                  <table className="text-xs w-full">
                    <thead>
                      <tr>
                        {Object.keys(result.rows[0]).map((c) => (
                          <th key={c} className="text-left p-1.5 border-b font-semibold">{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.rows.slice(0, 50).map((r, i) => (
                        <tr key={i} className="border-b">
                          {Object.values(r).map((v, j) => (
                            <td key={j} className="p-1.5">{String(v)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {tab === "EDA" && (
            <div className="prose-report card p-5 text-sm">
              <ReactMarkdown>{result.eda || "_No EDA_"}</ReactMarkdown>
            </div>
          )}

          {tab === "ML" && (
            <div className="card p-5 text-sm">
              {result.ml?.ran ? (
                <>
                  <p className="mb-3">{result.ml.summary}</p>
                  {result.ml.importances && (
                    <table className="text-xs w-full">
                      <thead>
                        <tr><th className="text-left p-1.5 border-b">Feature</th><th className="text-left p-1.5 border-b">Importance</th></tr>
                      </thead>
                      <tbody>
                        {result.ml.importances.map((d, i) => (
                          <tr key={i} className="border-b"><td className="p-1.5">{d.feature}</td><td className="p-1.5">{d.importance}</td></tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </>
              ) : (
                <p className="text-neutral-500">{result.ml?.summary || "ML was not required for this question."}</p>
              )}
            </div>
          )}

          {tab === "Chart" && (
            <div className="card p-5">
              {result.charts?.length > 0 ? (
                result.charts.map((c, i) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img key={i} src={c} alt="chart" className="w-full rounded-lg" />
                ))
              ) : (
                <p className="text-sm text-neutral-500">No chart generated.</p>
              )}
            </div>
          )}
        </div>
      )}

      <footer className="mt-16 pt-6 border-t border-black/10 text-center text-xs text-neutral-500">
        Built by Suman Kumar ·{" "}
        <a className="text-violet-600" href="https://github.com/sumankr0087/autonomous-data-scientist">
          GitHub
        </a>
      </footer>
    </main>
  );
}
