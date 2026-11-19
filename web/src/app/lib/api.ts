// Backend API calls, isolated from UI components.

import type { ModelOption, RunResult } from "./types";

export const DEFAULT_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const root = (apiBase: string) => apiBase.replace(/\/$/, "");

export type ProvidersResponse = {
  providers: ModelOption[];
  default_provider: string;
  default_model: string;
};

export async function getProviders(apiBase: string): Promise<ProvidersResponse> {
  const r = await fetch(`${root(apiBase)}/providers`);
  return r.json();
}

export async function postRun(
  apiBase: string,
  question: string,
  provider?: string,
  model?: string,
): Promise<RunResult & { message?: string; error?: string }> {
  const res = await fetch(`${root(apiBase)}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, provider, model }),
  });
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}
