import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyMetrics } from "@/api/queries/dashboard";
import { formatCount, formatDate, formatExact } from "@/lib/format";

const MEASURES = [
  { key: "views", label: "Views" },
  { key: "engagement", label: "Engagement" },
  { key: "posts", label: "Posts" },
] as const;

type Measure = (typeof MEASURES)[number]["key"];

// The design's "Content performance" card: one running-total line per measure
// (views, engagement or posts of the campaign's posts, by posting day). One series, so
// no legend; the tab names it. Exact daily numbers are in the tooltip and the table.
export default function MetricsChart({ daily }: { daily: DailyMetrics[] }) {
  const [measure, setMeasure] = useState<Measure>("views");
  if (daily.length === 0 || daily.every((d) => d.posts === 0)) return null;

  let running = { views: 0, engagement: 0, posts: 0 };
  const series = daily.map((day) => {
    running = {
      views: running.views + day.views,
      engagement: running.engagement + day.engagement,
      posts: running.posts + day.posts,
    };
    return { ...day, total: running[measure] };
  });
  const label = MEASURES.find((m) => m.key === measure)!.label;

  return (
    <figure className="flex flex-col gap-5 rounded-card border border-line bg-surface p-[22px]">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-base text-ink">Content performance</span>
        <span className="text-[10px] text-ink-muted">Running total by posting day</span>
      </figcaption>
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
      <div className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series} margin={{ top: 6, right: 6, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--hk-color-line)" strokeWidth={1} />
            <XAxis
              dataKey="date"
              tickFormatter={(d: string) => formatDate(d).replace(/,? \d{4}$/, "")}
              tick={{ fontSize: 10, fill: "var(--hk-color-fg-subtle)" }}
              tickLine={false}
              axisLine={false}
              minTickGap={32}
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
              content={<DayTooltip label={label} />}
            />
            {/* No draw-in animation: the dashboard refetches after every change */}
            <Line
              type="monotone"
              dataKey="total"
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
      <details className="text-xs text-ink-muted">
        <summary className="cursor-pointer hover:text-ink">Show as table</summary>
        <div className="mt-2 max-h-48 overflow-y-auto">
          <table className="w-full text-left">
            <thead>
              <tr>
                <th className="py-1 font-medium">Day</th>
                <th className="py-1 text-right font-medium">Posts</th>
                <th className="py-1 text-right font-medium">Views</th>
                <th className="py-1 text-right font-medium">Engagement</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {daily
                .filter((d) => d.posts > 0)
                .map((d) => (
                  <tr key={d.date} className="border-t border-line">
                    <td className="py-1">{formatDate(d.date)}</td>
                    <td className="py-1 text-right">{d.posts}</td>
                    <td className="py-1 text-right">{formatExact(d.views)}</td>
                    <td className="py-1 text-right">{formatExact(d.engagement)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}

function DayTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { payload: DailyMetrics & { total: number } }[];
  label: string;
}) {
  const day = active ? payload?.[0]?.payload : undefined;
  if (!day) return null;
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-[11px] shadow-md">
      <p className="font-medium text-ink">{formatDate(day.date)}</p>
      <p className="mt-1 text-ink-muted">
        {label} so far: <span className="text-ink">{formatExact(day.total)}</span>
      </p>
      <p className="text-ink-muted">
        That day: {day.posts} {day.posts === 1 ? "post" : "posts"}, {formatExact(day.views)} views
      </p>
    </div>
  );
}
