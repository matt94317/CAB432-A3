import { Suspense, lazy, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMe } from "@/api/queries/me";
import { type Overview, useOverview } from "@/api/queries/overview";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import PageHeader from "@/components/ui/PageHeader";
import StatCard from "@/components/ui/StatCard";
import CampaignFormDialog from "@/features/campaigns/components/CampaignFormDialog";
import { formatCount, formatRelative } from "@/lib/format";
import ActiveCampaigns from "../components/ActiveCampaigns";
import AttentionPanel from "../components/AttentionPanel";
import Comparison, { percentChange } from "../components/Comparison";
import MonthPicker from "../components/MonthPicker";
import StandoutCreators from "../components/StandoutCreators";
import { monthKey } from "../months";

// Recharts is large; load it with the chart
const OverviewChart = lazy(() => import("../components/OverviewChart"));

const monthName = new Intl.DateTimeFormat(undefined, { month: "long" });

function greeting(now = new Date()): string {
  const hour = now.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

/** The design's one-line summary banner, written from the numbers. */
function summary(o: Overview): string {
  const views = o.totals.views;
  const before = o.comparing === "same_days" ? "the same days last month" : "the month before";
  const change = percentChange(views, o.previous.views);
  if (views === 0) {
    return o.active_campaigns.length
      ? "No views counted yet this month. Sync your live campaigns to pull in the latest from TikTok."
      : "Welcome to Hookd. Create a campaign and add your creators, and every post gets tracked here.";
  }
  if (change === null) return `Your first ${formatCount(views)} views are in. A great start.`;
  if (change >= 0) {
    return `Your content is finding its people. Views are up ${change.toFixed(1)}% on ${before}. Keep the momentum going.`;
  }
  return `Views are ${Math.abs(change).toFixed(1)}% below ${before}. A quick check-in with your creators could help.`;
}

// The workspace overview: what a manager sees right after logging in.
export default function OverviewPage() {
  const navigate = useNavigate();
  const me = useMe();
  const [month, setMonth] = useState(() => monthKey(new Date()));
  const overview = useOverview(month);
  const [creating, setCreating] = useState(false);

  const firstName = me.data?.name.split(" ")[0];
  const o = overview.data;
  const isCurrent = month === monthKey(new Date());
  const versus = o?.comparing === "same_days" ? "vs. same days last month" : "vs. the month before";

  return (
    <div className="flex flex-col gap-[26px]">
      <PageHeader
        title={`${greeting()}${firstName ? `, ${firstName}` : ""} ${greeting() === "Good evening" ? "☾" : "☀"}`}
        description="Here’s what’s happening with your creator community."
        actions={
          <>
            <MonthPicker value={month} onChange={setMonth} />
            <Button icon="plus" onClick={() => setCreating(true)}>
              Create campaign
            </Button>
          </>
        }
      />

      {overview.isPending && <p className="text-[13px] text-ink-muted">Loading your overview…</p>}
      {overview.isError && <Alert>{overview.error.message}</Alert>}

      {o && (
        <>
          <p className="flex items-center gap-3.5 rounded-card bg-brand-soft px-5 py-4 text-[13px] text-brand-strong">
            <Icon name="sparkles" className="size-[21px] text-brand" />
            <span className="flex-1">{summary(o)}</span>
          </p>

          <div className="grid grid-cols-2 gap-3 sm:gap-[18px] lg:grid-cols-4">
            <StatCard
              icon="eye"
              label="Total views"
              value={formatCount(o.totals.views)}
              note={<Comparison current={o.totals.views} previous={o.previous.views} label={versus} />}
            />
            <StatCard
              icon="heart"
              label="Engagement rate"
              value={o.totals.engagement_rate === null ? "–" : `${(o.totals.engagement_rate * 100).toFixed(1)}%`}
              note={
                o.totals.engagement_rate !== null && o.previous.engagement_rate !== null ? (
                  <Comparison
                    current={o.totals.engagement_rate}
                    previous={o.previous.engagement_rate}
                    label={versus}
                    points
                  />
                ) : (
                  <span className="text-ink-muted">Engagements per view</span>
                )
              }
            />
            <StatCard
              icon="clapperboard"
              label="Published posts"
              value={o.totals.posts}
              note={<Comparison current={o.totals.posts} previous={o.previous.posts} label={versus} />}
            />
            <StatCard
              icon="users"
              label="Active creators"
              value={o.active_creators}
              note={
                o.new_creators > 0 ? (
                  <span className="flex items-center gap-1.5">
                    <span className="text-on-target">↗ {o.new_creators} new</span>
                    <span className="text-ink-muted">this month</span>
                  </span>
                ) : (
                  <span className="text-ink-muted">On campaigns this month</span>
                )
              }
            />
          </div>

          <div className="grid items-start gap-[22px] lg:grid-cols-[minmax(0,1fr)_minmax(0,402px)]">
            <Suspense fallback={<div className="h-[325px] rounded-card border border-line bg-surface" />}>
              <OverviewChart
                month={o.month}
                daily={o.daily}
                previousDaily={o.previous_daily}
                currentLabel={isCurrent ? "This month" : monthName.format(new Date(`${o.month}-01T00:00`))}
              />
            </Suspense>
            <AttentionPanel items={o.needs_attention} />
          </div>

          <div className="grid gap-[22px] lg:grid-cols-[minmax(0,1fr)_minmax(0,402px)]">
            <ActiveCampaigns overview={o} />
            <StandoutCreators creators={o.standout_creators} />
          </div>

          <footer className="flex flex-wrap justify-between gap-2 text-[10px] text-ink-subtle">
            <span className="flex items-center gap-1.5">
              <Icon name="refresh" className="size-3" />
              {o.last_synced_at ? `Last synced ${formatRelative(o.last_synced_at)}` : "No creators synced yet"}
            </span>
            <span>Made for good collaborations.</span>
          </footer>
        </>
      )}

      <CampaignFormDialog
        open={creating}
        onClose={() => setCreating(false)}
        onSaved={(campaign) => navigate(`/campaigns/${campaign.id}`)}
      />
    </div>
  );
}
