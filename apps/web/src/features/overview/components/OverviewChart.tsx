import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyMetrics } from "@/api/queries/dashboard";
import { formatCount, formatExact } from "@/lib/format";

const MEASURES = [
  { key: "views", label: "Views" },
  { key: "engagement", label: "Engagement" },
  { key: "posts", label: "Posts" },
] as const;

type Measure = (typeof MEASURES)[number]["key"];

const dayLabel = new Intl.DateTimeFormat(undefined, { month: "short", day: "2-digit" });

function cumulative(days: DailyMetrics[], measure: Measure): number[] {
  let total = 0;
  return days.map((d) => (total += d[measure]));
}

interface Row {
  label: string;
  current?: number;
  previous?: number;
}

// "Content performance": this month vs last month, as running totals by day of month.
// Two series: a legend plus dashing for last month, so it never relies on colour alone.
export default function OverviewChart({
  month,
  daily,
  previousDaily,
  currentLabel,
}: {
  month: string;
  daily: DailyMetrics[];
  previousDaily: DailyMetrics[];
  currentLabel: string;
}) {
  const [measure, setMeasure] = useState<Measure>("views");
  const [year, number] = month.split("-").map(Number);
  const daysInMonth = new Date(year, number, 0).getDate();
  const current = cumulative(daily, measure);
  const previous = cumulative(previousDaily, measure);

  const rows: Row[] = Array.from({ length: daysInMonth }, (_, i) => ({
    label: dayLabel.format(new Date(year, number - 1, i + 1)),
    current: current[i],
    previous: previous[i],
  }));
  const empty = current.every((v) => v === 0) && previous.every((v) => v === 0);
  const label = MEASURES.find((m) => m.key === measure)!.label;

  return (
    <figure className="flex min-w-0 flex-col gap-5 rounded-card border border-line bg-surface p-[22px]">
      <figcaption className="text-base text-ink">Content performance</figcaption>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex gap-[18px] text-xs" role="tablist" aria-label="Measure">
          {MEASURES.map((m) => (
            <button
              key={m.key}
              role="tab"
              aria-selected={measure === m.key}
              onClick={() => setMeasure(m.key)}
              className={measure === m.key ? "font-semibold text-brand" : "text-ink-muted hover:text-ink"}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="flex gap-3.5 text-[10px] text-ink-muted" aria-label="Legend">
          <span className="flex items-center gap-[5px]">
            <span className="size-[7px] rounded-[2px] bg-brand" aria-hidden="true" />
            {currentLabel}
          </span>
          <span className="flex items-center gap-[5px]">
            <span className="h-0 w-3 border-t-2 border-dashed border-[var(--hk-color-accent-compare)]" aria-hidden="true" />
            Month before
          </span>
        </div>
      </div>
      {empty ? (
        <p className="flex h-[174px] items-center justify-center rounded-lg bg-canvas text-[13px] text-ink-muted">
          No posts in these months yet. Sync a campaign to pull them in.
        </p>
      ) : (
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 6, right: 6, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--hk-color-line)" strokeWidth={1} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10, fill: "var(--hk-color-fg-subtle)" }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
                minTickGap={40}
              />
              <YAxis
                tickFormatter={(v: number) => formatCount(v)}
                tick={{ fontSize: 10, fill: "var(--hk-color-fg-subtle)" }}
                tickLine={false}
                axisLine={false}
                width={36}
                allowDecimals={false}
              />
              <Tooltip
                cursor={{ stroke: "var(--hk-color-line-strong)", strokeWidth: 1 }}
                content={<RowTooltip label={label} currentLabel={currentLabel} />}
              />
              <Line
                type="monotone"
                dataKey="previous"
                stroke="var(--hk-color-accent-compare)"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                activeDot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="current"
                stroke="var(--hk-color-accent)"
                strokeWidth={2}
                strokeLinecap="round"
                dot={false}
                activeDot={{ r: 4, fill: "var(--hk-color-accent)", stroke: "var(--hk-color-surface)", strokeWidth: 2 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <details className="text-xs text-ink-muted">
        <summary className="cursor-pointer hover:text-ink">Show as table</summary>
        <div className="mt-2 max-h-48 overflow-y-auto">
          <table className="w-full text-left tabular-nums">
            <thead>
              <tr>
                <th className="py-1 font-medium">Day</th>
                <th className="py-1 text-right font-medium">{label}, {currentLabel.toLowerCase()}</th>
                <th className="py-1 text-right font-medium">{label}, month before</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.label} className="border-t border-line">
                  <td className="py-1">{row.label}</td>
                  <td className="py-1 text-right">{row.current === undefined ? "—" : formatExact(row.current)}</td>
                  <td className="py-1 text-right">{row.previous === undefined ? "—" : formatExact(row.previous)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}

function RowTooltip({
  active,
  payload,
  label,
  currentLabel,
}: {
  active?: boolean;
  payload?: { payload: Row }[];
  label: string;
  currentLabel: string;
}) {
  const row = active ? payload?.[0]?.payload : undefined;
  if (!row) return null;
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-[11px] shadow-md">
      <p className="font-medium text-ink">Day {row.label.split(" ").pop()}</p>
      {row.current !== undefined && (
        <p className="mt-1 text-ink-muted">
          {currentLabel}: <span className="text-ink">{formatExact(row.current)}</span> {label.toLowerCase()}
        </p>
      )}
      {row.previous !== undefined && (
        <p className="text-ink-muted">
          Month before: <span className="text-ink">{formatExact(row.previous)}</span>
        </p>
      )}
    </div>
  );
}
