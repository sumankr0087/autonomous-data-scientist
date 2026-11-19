// Shared types for the AI Business Analyst frontend.

export type RunResult = {
  status: string;
  fell_back_to?: string;
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

export type Msg = { id: string; question: string; result: RunResult };
export type Conversation = { id: string; title: string; messages: Msg[]; ts: number };
export type ModelOption = { provider: string; model: string; label: string };

export const TABS = ["Report", "Plan", "SQL & Data", "EDA", "ML", "Chart"] as const;
export type Tab = (typeof TABS)[number];

export const EXAMPLES = [
  "Why did sales drop in Maharashtra last quarter?",
  "Which product categories grew the most this year?",
  "What factors drive revenue? Predict the key drivers.",
  "Compare online vs retail vs partner channel revenue by region.",
];
