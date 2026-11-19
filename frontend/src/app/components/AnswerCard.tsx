"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { fmtCell } from "../lib/format";
import { TABS, type RunResult, type Tab } from "../lib/types";

export function AnswerCard({ result }: { result: RunResult }) {
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
        <ol className="list-decimal pl-5 space-y-1">{r.plan?.map((s, i) => <li key={i}>{s}</li>)}</ol>
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
                      <td key={j} className="p-1.5">{fmtCell(v)}</td>
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
                  <td className="p-1.5">{fmtCell(d.importance)}</td>
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
