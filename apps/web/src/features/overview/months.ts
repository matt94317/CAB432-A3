// Month helpers for the overview's month picker. Months are "YYYY-MM" strings.

export function monthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

/** The current month and the 11 before it, newest first. */
export function recentMonths(today = new Date()): string[] {
  return Array.from({ length: 12 }, (_, i) => monthKey(new Date(today.getFullYear(), today.getMonth() - i, 1)));
}

const shortDate = new Intl.DateTimeFormat(undefined, { month: "short", day: "2-digit" });

/** "2026-10" -> "Oct 01 – Oct 31, 2026" */
export function monthRangeLabel(month: string): string {
  const [year, number] = month.split("-").map(Number);
  const first = new Date(year, number - 1, 1);
  const last = new Date(year, number, 0);
  return `${shortDate.format(first)} – ${shortDate.format(last)}, ${year}`;
}
