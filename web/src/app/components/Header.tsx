"use client";

import { FiMenu, FiInfo, FiSettings } from "react-icons/fi";

export function Header({
  onMenu,
  onAbout,
  onToggleSettings,
}: {
  onMenu: () => void;
  onAbout: () => void;
  onToggleSettings: () => void;
}) {
  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-black/10 bg-white/60 backdrop-blur">
      <div className="flex items-center gap-2 min-w-0">
        <button className="md:hidden text-neutral-600" onClick={onMenu}>
          <FiMenu size={20} />
        </button>
        <span className="text-xl">📊</span>
        <div className="min-w-0">
          <h1 className="font-bold truncate pink-text leading-tight">AI Business Analyst</h1>
          <p className="hidden sm:block text-[0.65rem] text-neutral-500 leading-tight">
            Ask your sales data — get instant insights, charts &amp; reports
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={onAbout}
          className="flex items-center gap-1 text-sm text-neutral-600 hover:text-violet-600"
        >
          <FiInfo size={16} /> <span className="hidden sm:inline">About</span>
        </button>
        <button onClick={onToggleSettings} className="text-neutral-500 hover:text-violet-600">
          <FiSettings size={18} />
        </button>
      </div>
    </header>
  );
}
