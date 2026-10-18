import type { Metrics } from "@/api/queries/dashboard";
import { formatCount, formatExact } from "@/lib/format";

// Total posts, views and engagement for a campaign or creator (US-20, US-21).
export default function CampaignTotals({ totals }: { totals: Metrics }) {
  const tiles = [
    { label: "Posts", value: formatExact(totals.posts), exact: formatExact(totals.posts) },
    { label: "Views", value: formatCount(totals.views), exact: formatExact(totals.views) },
    {
      label: "Engagement",
      value: formatCount(totals.engagement),
      exact: `${formatExact(totals.likes)} likes, ${formatExact(totals.comments)} comments, ${formatExact(totals.shares)} shares`,
    },
    {
      label: "Engagement rate",
      value: totals.engagement_rate === null ? "–" : `${(totals.engagement_rate * 100).toFixed(1)}%`,
      exact: "Likes, comments and shares per view",
    },
  ];

  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {tiles.map((tile) => (
        <div key={tile.label} className="rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm" title={tile.exact}>
          <dt className="text-xs font-medium text-gray-500">{tile.label}</dt>
          <dd className="mt-1 text-2xl font-semibold tabular-nums text-gray-900">{tile.value}</dd>
        </div>
      ))}
    </dl>
  );
}
