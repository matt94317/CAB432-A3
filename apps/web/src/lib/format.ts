// Date formatters. Campaign dates are calendar dates ("2026-11-01"), so parse them
// as local dates to avoid them shifting a day in timezones behind UTC.

const dateFormat = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric" });

export function parseDate(isoDate: string): Date {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export function formatDate(isoDate: string): string {
  return dateFormat.format(parseDate(isoDate));
}

export function formatDateRange(start: string, end: string): string {
  return `${formatDate(start)} – ${formatDate(end)}`;
}

export function toIsoDate(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function addDays(date: Date, days: number): Date {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

// Metric and time formatters for posts and sync status.

const countFormat = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });
const exactFormat = new Intl.NumberFormat();
const dateTimeFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });
const relativeFormat = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

/** 1234 -> "1.2K" */
export function formatCount(n: number): string {
  return countFormat.format(n);
}

/** 1234 -> "1,234" */
export function formatExact(n: number): string {
  return exactFormat.format(n);
}

export function formatDateTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso));
}

/** A timestamp as "just now", "5 minutes ago", "yesterday"… */
export function formatRelative(iso: string, now: Date = new Date()): string {
  const seconds = (new Date(iso).getTime() - now.getTime()) / 1000;
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return relativeFormat.format(Math.round(seconds / size), unit);
  }
  return "just now";
}
