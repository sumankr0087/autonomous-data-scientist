// Display helpers for table/number formatting.

// Whole numbers as-is, decimals rounded to 2 places (avoids floating-point noise
// like 12826219.900000008), everything else rendered as plain text.
export function fmtCell(v: unknown): string {
  if (typeof v === "number" && Number.isFinite(v)) {
    return Number.isInteger(v)
      ? v.toLocaleString("en-US")
      : v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return String(v);
}
