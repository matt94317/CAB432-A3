import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyMetrics } from "@/api/queries/dashboard";
import { formatCount, formatDate, formatExact } from "@/lib/format";

// Views by posting day: one series, so no legend; posts and engagement are in the
// tooltip and the table rather than on a second axis.
export default function MetricsChart({ daily }: { daily: DailyMetrics[] }) {
  if (daily.length === 0 || daily.every((d) => d.posts === 0)) return null;

  return (
    <figure className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <figcaption className="text-sm font-medium text-gray-900">Views by posting day</figcaption>
      <p className="text-xs text-gray-500">Current views of the posts published each day</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={daily} margin={{ top: 4, right: 4, bottom: 0, left: 0 }} barCategoryGap={2}>
            <CartesianGrid vertical={false} stroke="#e5e7eb" strokeWidth={1} />
            <XAxis
              dataKey="date"
              tickFormatter={(d: string) => formatDate(d).replace(/,? \d{4}$/, "")}
              tick={{ fontSize: 11, fill: "#6b7280" }}
              tickLine={false}
              axisLine={{ stroke: "#e5e7eb" }}
              minTickGap={24}
            />
            <YAxis
              tickFormatter={(v: number) => formatCount(v)}
              tick={{ fontSize: 11, fill: "#6b7280" }}
              tickLine={false}
              axisLine={false}
              width={40}
              allowDecimals={false}
            />
            <Tooltip cursor={{ fill: "#f3f4f6" }} content={<DayTooltip />} />
            {/* No grow-in animation: the dashboard refetches after every change, and replaying
                it each time is distracting. Fill uses the token: @theme inline emits no --color-brand */}
            <Bar
              dataKey="views"
              fill="var(--hk-color-accent)"
              maxBarSize={24}
              radius={[4, 4, 0, 0]}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <details className="mt-2 text-xs text-gray-600">
        <summary className="cursor-pointer text-gray-500 hover:text-gray-900">Show as table</summary>
        <div className="mt-2 max-h-48 overflow-y-auto">
          <table className="w-full text-left">
            <thead className="text-gray-500">
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
                  <tr key={d.date} className="border-t border-gray-100">
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

function DayTooltip({ active, payload }: { active?: boolean; payload?: { payload: DailyMetrics }[] }) {
  const day = active ? payload?.[0]?.payload : undefined;
  if (!day) return null;
  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs shadow-md">
      <p className="font-medium text-gray-900">{formatDate(day.date)}</p>
      <p className="mt-1 text-gray-600">
        {formatExact(day.views)} views · {day.posts} {day.posts === 1 ? "post" : "posts"}
      </p>
      <p className="text-gray-600">{formatExact(day.engagement)} engagement</p>
    </div>
  );
}
