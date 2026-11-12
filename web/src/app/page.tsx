"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { FiSend, FiSettings, FiPlus, FiTrash2, FiMenu, FiInfo, FiX } from "react-icons/fi";

const EXAMPLES = [
  "Why did sales drop in Maharashtra last quarter?",
  "Which product categories grew the most this year?",
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

type Msg = { id: string; question: string; result: RunResult };
type Conversation = { id: string; title: string; messages: Msg[]; ts: number };

const TABS = ["Report", "Plan", "SQL & Data", "EDA", "ML", "Chart"] as const;
type Tab = (typeof TABS)[number];

export default function Home() {
  const [apiBase, setApiBase] = useState(DEFAULT_API);
  const [showSettings, setShowSettings] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const savedApi = localStorage.getItem("ads_api_base");
      if (savedApi) setApiBase(savedApi);
      const saved = localStorage.getItem("ads_convs");
      if (saved) {
        const c: Conversation[] = JSON.parse(saved);
        setConvs(c);
        if (c.length) setActiveId(c[0].id);
      }
    } catch {}
  }, []);

  function persist(c: Conversation[]) {
    try {
      localStorage.setItem("ads_convs", JSON.stringify(c.slice(0, 30)));
    } catch {}
  }
  function saveApiBase(v: string) {
    setApiBase(v);
    try {
      localStorage.setItem("ads_api_base", v);
    } catch {}
  }

  const active = convs.find((c) => c.id === activeId) || null;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [active?.messages.length, loading]);

  async function run(q?: string) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    setLoading(true);
    setError("");
    setQuestion("");
    setPending(text);
    try {
      const res = await fetch(`${apiBase.replace(/\/$/, "")}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const data = await res.json();
      if (data.status === "error") {
        setError(`Backend error: ${data.error}`);
        return;
      }
      const msg: Msg = { id: crypto.randomUUID(), question: text, result: data };

      setConvs((prev) => {
        let next: Conversation[];
        if (activeId && prev.some((c) => c.id === activeId)) {
          // append to the active conversation
          next = prev.map((c) =>
            c.id === activeId ? { ...c, messages: [...c.messages, msg], ts: Date.now() } : c
          );
        } else {
          // start a new conversation
          const conv: Conversation = {
            id: crypto.randomUUID(),
            title: text,
            messages: [msg],
            ts: Date.now(),
          };
          setActiveId(conv.id);
          next = [conv, ...prev];
        }
        persist(next);
        return next;
      });
    } catch {
      setError(
        `Could not reach the backend at ${apiBase}. It may be waking up (free tier sleeps ~15 min — first call takes ~50s). Try again, or set the URL (⚙).`
      );
    } finally {
      setLoading(false);
      setPending(null);
    }
  }

  function newChat() {
    setActiveId(null);
    setError("");
    setQuestion("");
    setSidebarOpen(false);
  }
  function deleteConv(id: string) {
    const c = convs.filter((x) => x.id !== id);
    setConvs(c);
    persist(c);
    if (activeId === id) setActiveId(c[0]?.id ?? null);
  }

  return (
    <div className="flex h-screen overflow-hidden text-neutral-800">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 fixed md:static z-30 w-64 h-full bg-white/80 backdrop-blur border-r border-black/10 flex flex-col transition-transform`}
      >
        <div className="p-3">
          <button onClick={newChat} className="w-full flex items-center justify-center gap-2 btn-primary">
            <FiPlus /> New analysis
          </button>
        </div>
        <div className="px-3 text-[0.65rem] uppercase tracking-widest text-neutral-400">Conversations</div>
        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
          {convs.length === 0 && <p className="text-xs text-neutral-400 px-2 py-3">No conversations yet.</p>}
          {convs.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center gap-1 rounded-lg px-2 py-2 cursor-pointer text-sm ${
                c.id === activeId ? "bg-violet-100 text-violet-800" : "hover:bg-black/5"
              }`}
              onClick={() => {
                setActiveId(c.id);
                setSidebarOpen(false);
              }}
            >
              <span className="flex-1 truncate">{c.title}</span>
              <span className="text-[0.6rem] text-neutral-400">{c.messages.length}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConv(c.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-neutral-400 hover:text-red-500"
              >
                <FiTrash2 size={13} />
              </button>
            </div>
          ))}
        </div>
        <div className="p-3 border-t border-black/10 text-[0.65rem] text-neutral-400">
          Built by Suman Kumar ·{" "}
          <a className="text-violet-600" href="https://github.com/sumankr0087/autonomous-data-scientist">
            GitHub
          </a>
        </div>
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/20 z-20 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        <header className="flex items-center justify-between px-4 py-3 border-b border-black/10 bg-white/60 backdrop-blur">
          <div className="flex items-center gap-2 min-w-0">
            <button className="md:hidden text-neutral-600" onClick={() => setSidebarOpen(true)}>
              <FiMenu size={20} />
            </button>
            <span className="text-xl">🤖</span>
            <h1 className="font-bold truncate pink-text">Autonomous Data Scientist</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowAbout(true)}
              className="flex items-center gap-1 text-sm text-neutral-600 hover:text-violet-600"
            >
              <FiInfo size={16} /> <span className="hidden sm:inline">About</span>
            </button>
            <button onClick={() => setShowSettings((v) => !v)} className="text-neutral-500 hover:text-violet-600">
              <FiSettings size={18} />
            </button>
          </div>
        </header>

        {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}

        {showSettings && (
          <div className="card m-3 p-3 rounded-xl">
            <label className="text-xs uppercase tracking-wider text-neutral-500">Backend API URL</label>
            <input
              value={apiBase}
              onChange={(e) => saveApiBase(e.target.value)}
              className="mt-1 w-full bg-neutral-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
            />
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-5">
            {!active && !loading && !pending && (
              <div className="text-center mt-10">
                <h2 className="text-2xl font-bold mb-2 pink-text">Ask a business question</h2>
                <p className="text-neutral-500 text-sm mb-6">
                  The agents generate SQL, analyse the data, train a model if needed, draw a chart, and
                  write an executive report. Keep asking in the same chat to build on it.
                </p>
                <div className="flex flex-col gap-2 max-w-xl mx-auto">
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex}
                      onClick={() => run(ex)}
                      className="card rounded-xl px-4 py-3 text-sm text-left hover:border-violet-400 transition"
                    >
                      {ex}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {active?.messages.map((m) => (
              <div key={m.id} className="space-y-3">
                <div className="flex justify-end">
                  <div className="bg-violet-600 text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm max-w-[85%]">
                    {m.question}
                  </div>
                </div>
                <AnswerCard result={m.result} />
              </div>
            ))}

            {loading && (
              <div className="space-y-3">
                {pending && (
                  <div className="flex justify-end">
                    <div className="bg-violet-600 text-white rounded-2xl rounded-br-sm px-4 py-2 text-sm max-w-[85%]">
                      {pending}
                    </div>
                  </div>
                )}
                <div className="flex justify-start">
                  <div className="card rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-neutral-500">
                    <span className="inline-block animate-pulse">
                      Agents working: planning → SQL → EDA → ML → chart → report…
                    </span>
                  </div>
                </div>
              </div>
            )}

            {error && <div className="card p-4 text-sm text-red-600 border-red-200">{error}</div>}
            <div ref={endRef} />
          </div>
        </div>

        <div className="border-t border-black/10 bg-white/70 backdrop-blur px-4 py-3">
          <div className="max-w-3xl mx-auto flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && run()}
              placeholder={active ? "Ask a follow-up in this chat…" : "Ask a business question…"}
              className="flex-1 card rounded-full px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
            />
            <button
              onClick={() => run()}
              disabled={loading || !question.trim()}
              className="btn-primary !rounded-full !px-4 flex items-center gap-2"
            >
              <FiSend />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AboutModal({ onClose }: { onClose: () => void }) {
  const tabs: [string, string][] = [
    ["📄 Report", "A business-ready executive report: a direct answer, key findings, the likely cause/drivers, recommended actions, and a confidence & caveats note."],
    ["🧠 Plan", "The step-by-step plan the AI decided on, its rationale, and whether a machine-learning model was needed."],
    ["🗃️ SQL & Data", "The exact SQL query the agent wrote, plus the raw result table it ran against the database."],
    ["📊 EDA", "Exploratory data analysis — trends, group comparisons and anomalies found in the result."],
    ["🤖 ML", "When useful, a trained baseline model with its metrics and the top feature importances (what drives the outcome)."],
    ["📈 Chart", "A chart visualising the key movers in the result."],
  ];
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl max-w-lg w-full max-h-[85vh] overflow-y-auto p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-3">
          <h2 className="text-xl font-bold pink-text">About this app</h2>
          <button onClick={onClose} className="text-neutral-400 hover:text-neutral-700">
            <FiX size={20} />
          </button>
        </div>

        <p className="text-sm text-neutral-700 leading-relaxed mb-4">
          <strong>Autonomous Data Scientist</strong> lets you ask a business question in plain
          English. A team of AI agents then does the whole analysis for you — no SQL, Python or ML
          knowledge needed. They <strong>write and run SQL</strong>, <strong>explore the data</strong>,
          <strong> train a model</strong> when it helps, <strong>draw a chart</strong>, and{" "}
          <strong>write an executive report</strong> with recommendations.
        </p>

        <h3 className="font-semibold text-sm mb-2">What you get back (the tabs on each answer):</h3>
        <ul className="space-y-2 mb-4">
          {tabs.map(([t, d]) => (
            <li key={t} className="text-sm">
              <span className="font-semibold text-violet-700">{t}</span>
              <span className="text-neutral-600"> — {d}</span>
            </li>
          ))}
        </ul>

        <h3 className="font-semibold text-sm mb-2">What it can answer</h3>
        <p className="text-sm text-neutral-600 leading-relaxed mb-2">
          It runs on a sample retail <strong>sales dataset</strong> covering 12 Indian states across
          4 regions, multiple product categories &amp; products, and three sales channels
          (Online / Retail / Partner), spanning the last two years. Ask about any of these
          dimensions — one state or all of them, a region, a channel, a product, a year or quarter.
        </p>
        <div className="bg-violet-50 rounded-lg p-3 text-xs text-neutral-700 space-y-1 mb-4">
          <p>• &quot;Why did sales drop in Maharashtra last quarter?&quot;</p>
          <p>• &quot;Which product categories grew the most this year?&quot;</p>
          <p>• &quot;Compare online vs retail vs partner revenue by region.&quot;</p>
          <p>• &quot;What factors drive revenue?&quot;</p>
        </div>

        <p className="text-xs text-neutral-400">
          Demo note: the backend runs on a free tier that sleeps after inactivity, so the first
          question may take ~50s to wake up. Built by Suman Kumar ·{" "}
          <a className="text-violet-600" href="https://github.com/sumankr0087/autonomous-data-scientist">
            source on GitHub
          </a>
          .
        </p>
      </div>
    </div>
  );
}

function AnswerCard({ result }: { result: RunResult }) {
  const [tab, setTab] = useState<Tab>("Report");
  return (
    <div className="card rounded-2xl rounded-bl-sm p-4">
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
      <ResultTab tab={tab} r={result} />
    </div>
  );
}

function ResultTab({ tab, r }: { tab: Tab; r: RunResult }) {
  if (tab === "Report")
    return (
      <div className="prose-report text-sm">
        <ReactMarkdown>{r.report || "_No report_"}</ReactMarkdown>
      </div>
    );
  if (tab === "Plan")
    return (
      <div className="text-sm">
        <p className="text-neutral-600 mb-2">
          <strong>Rationale:</strong> {r.rationale}
        </p>
        <p className="text-neutral-600 mb-3">
          <strong>Needs ML:</strong> {String(r.needs_ml)}
        </p>
        <ol className="list-decimal pl-5 space-y-1">
          {r.plan?.map((s, i) => <li key={i}>{s}</li>)}
        </ol>
      </div>
    );
  if (tab === "SQL & Data")
    return (
      <div>
        <pre className="text-xs overflow-auto bg-neutral-50 p-3 rounded-lg">{r.sql || "-- no SQL"}</pre>
        <p className="text-xs text-neutral-500 my-2">{r.row_count} rows</p>
        {r.rows?.length > 0 && (
          <div className="overflow-auto max-h-80">
            <table className="text-xs w-full">
              <thead>
                <tr>
                  {Object.keys(r.rows[0]).map((c) => (
                    <th key={c} className="text-left p-1.5 border-b font-semibold">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {r.rows.slice(0, 50).map((row, i) => (
                  <tr key={i} className="border-b">
                    {Object.values(row).map((v, j) => (
                      <td key={j} className="p-1.5">{String(v)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  if (tab === "EDA")
    return (
      <div className="prose-report text-sm">
        <ReactMarkdown>{r.eda || "_No EDA_"}</ReactMarkdown>
      </div>
    );
  if (tab === "ML")
    return r.ml?.ran ? (
      <div className="text-sm">
        <p className="mb-3">{r.ml.summary}</p>
        {r.ml.importances && (
          <table className="text-xs w-full">
            <thead>
              <tr>
                <th className="text-left p-1.5 border-b">Feature</th>
                <th className="text-left p-1.5 border-b">Importance</th>
              </tr>
            </thead>
            <tbody>
              {r.ml.importances.map((d, i) => (
                <tr key={i} className="border-b">
                  <td className="p-1.5">{d.feature}</td>
                  <td className="p-1.5">{d.importance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    ) : (
      <p className="text-sm text-neutral-500">{r.ml?.summary || "ML was not required."}</p>
    );
  return r.charts?.length > 0 ? (
    <div>
      {r.charts.map((c, i) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img key={i} src={c} alt="chart" className="w-full rounded-lg" />
      ))}
    </div>
  ) : (
    <p className="text-sm text-neutral-500">No chart generated.</p>
  );
}
