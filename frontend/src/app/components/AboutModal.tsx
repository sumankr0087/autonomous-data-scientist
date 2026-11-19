"use client";

import { FiX } from "react-icons/fi";

export function AboutModal({ onClose }: { onClose: () => void }) {
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
          <strong>AI Business Analyst</strong> lets you ask a business question in plain English. A team
          of AI agents then does the whole analysis for you — no SQL, Python or ML knowledge needed. They{" "}
          <strong>write and run SQL</strong>, <strong>explore the data</strong>,
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

        <h3 className="font-semibold text-sm mb-2">Choose your AI model</h3>
        <p className="text-sm text-neutral-600 leading-relaxed mb-4">
          Use the <strong>AI model</strong> dropdown under the question box to switch the model that powers
          your analysis:
        </p>
        <ul className="space-y-2 mb-4 text-sm">
          <li>
            <span className="font-semibold text-violet-700">Groq · GPT-OSS 120B / 20B</span>
            <span className="text-neutral-600"> — fast, with a generous free tier (default). 120B is
            stronger; 20B is fastest.</span>
          </li>
          <li>
            <span className="font-semibold text-violet-700">Google Gemini · Flash-Lite</span>
            <span className="text-neutral-600"> — Google&apos;s model (smaller free daily limit).</span>
          </li>
        </ul>

        <h3 className="font-semibold text-sm mb-2">What it can answer</h3>
        <p className="text-sm text-neutral-600 leading-relaxed mb-2">
          It runs on a sample retail <strong>sales dataset</strong> covering 12 Indian states across 4
          regions, multiple product categories &amp; products, and three sales channels (Online / Retail /
          Partner), spanning the last two years. Ask about any of these dimensions — one state or all of
          them, a region, a channel, a product, a year or quarter.
        </p>
        <div className="bg-violet-50 rounded-lg p-3 text-xs text-neutral-700 space-y-1 mb-4">
          <p>• &quot;Why did sales drop in Maharashtra last quarter?&quot;</p>
          <p>• &quot;Which product categories grew the most this year?&quot;</p>
          <p>• &quot;Compare online vs retail vs partner revenue by region.&quot;</p>
          <p>• &quot;What factors drive revenue?&quot;</p>
        </div>

        <p className="text-xs text-neutral-400">
          Demo note: the backend runs on a free tier that sleeps after inactivity, so the first question
          may take ~50s to wake up. Built by Suman Kumar ·{" "}
          <a className="text-violet-600" target="_blank" rel="noreferrer" href="https://github.com/sumankr0087/autonomous-data-scientist">
            source on GitHub
          </a>
          .
        </p>
      </div>
    </div>
  );
}
