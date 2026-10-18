import type { Metrics } from "@/api/queries/dashboard";
import StatCard from "@/components/ui/StatCard";
import { formatCount, formatExact } from "@/lib/format";

// Total posts, views and engagement for a campaign or creator (US-20, US-21), as the
// design's post performance tiles.
export default function CampaignTotals({ totals }: { totals: Metrics }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-[18px] lg:grid-cols-4">
      <StatCard
        icon="eye"
        label="Total views"
        value={formatCount(totals.views)}
        note={`Across ${totals.posts} ${totals.posts === 1 ? "post" : "posts"}`}
        title={`${formatExact(totals.views)} views`}
      />
      <StatCard
        icon="heart"
        label="Total engagements"
        value={formatCount(totals.engagement)}
        note="Likes, comments and shares"
        title={`${formatExact(totals.likes)} likes, ${formatExact(totals.comments)} comments, ${formatExact(totals.shares)} shares`}
      />
      <StatCard icon="check" label="Tracked posts" value={formatExact(totals.posts)} note="Counting toward targets" />
      <StatCard
        icon="trending-up"
        label="Engagement rate"
        value={totals.engagement_rate === null ? "–" : `${(totals.engagement_rate * 100).toFixed(1)}%`}
        note="Engagements per view"
      />
    </div>
  );
}
