"use client";

import { EXAMPLES } from "../lib/types";

export function EmptyState({ onPick }: { onPick: (example: string) => void }) {
  return (
    <div className="text-center mt-10">
      <h2 className="text-2xl font-bold mb-2 pink-text">Ask a business question</h2>
      <p className="text-neutral-500 text-sm mb-6">
        The agents generate SQL, analyse the data, train a model if needed, draw a chart, and write an
        executive report. Keep asking in the same chat to build on it.
      </p>
      <div className="flex flex-col gap-2 max-w-xl mx-auto">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => onPick(ex)}
            className="card rounded-xl px-4 py-3 text-sm text-left hover:border-violet-400 transition"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
