"use client";

export function SettingsPanel({
  apiBase,
  onChange,
}: {
  apiBase: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="card m-3 p-3 rounded-xl">
      <label className="text-xs uppercase tracking-wider text-neutral-500">Backend API URL</label>
      <input
        value={apiBase}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full bg-neutral-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
      />
    </div>
  );
}
