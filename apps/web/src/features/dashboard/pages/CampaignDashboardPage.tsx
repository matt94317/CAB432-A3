import { Suspense, lazy, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useCampaign } from "@/api/queries/campaigns";
import { useCampaignDashboard } from "@/api/queries/dashboard";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import PageHeader from "@/components/ui/PageHeader";
import CampaignCreators from "@/features/campaigns/components/CampaignCreators";
import CampaignFormDialog from "@/features/campaigns/components/CampaignFormDialog";
import CampaignStatusBadge from "@/features/campaigns/components/CampaignStatusBadge";
import CampaignPosts from "@/features/posts/components/CampaignPosts";
import { formatDateRange } from "@/lib/format";
import CampaignTotals from "../components/CampaignTotals";

// Recharts is large; load it only when a dashboard has a chart to draw
const MetricsChart = lazy(() => import("../components/MetricsChart"));

// Campaign dashboard: totals and running performance (US-20), each creator's posts vs
// target with behind-target flags (US-19, US-22), and the campaign's posts.
export default function CampaignDashboardPage() {
  const { campaignId = "" } = useParams();
  const campaign = useCampaign(campaignId);
  const dashboard = useCampaignDashboard(campaignId);
  const [editing, setEditing] = useState(false);

  return (
    <div className="flex flex-col gap-[26px]">
      <Link to="/campaigns" className="inline-flex w-fit items-center gap-1 text-xs text-ink-muted hover:text-ink">
        <Icon name="chevron-right" className="size-3 rotate-180" />
        All campaigns
      </Link>

      {campaign.isPending && <p className="text-[13px] text-ink-muted">Loading campaign…</p>}
      {campaign.isError && <Alert>{campaign.error.message}</Alert>}

      {campaign.data && (
        <>
          <PageHeader
            title={
              <span className="flex flex-wrap items-center gap-3">
                {campaign.data.name}
                <CampaignStatusBadge campaign={campaign.data} />
              </span>
            }
            description={
              <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="uppercase tracking-wide">{campaign.data.brand}</span>
                <span aria-hidden="true">·</span>
                <span className="inline-flex items-center gap-1.5">
                  <Icon name="calendar" className="size-3" />
                  {formatDateRange(campaign.data.start_date, campaign.data.end_date)}
                </span>
              </span>
            }
            actions={
              campaign.data.status === "active" && (
                <Button variant="secondary" onClick={() => setEditing(true)}>
                  Edit campaign
                </Button>
              )
            }
          >
            <ul className="mt-3 flex flex-wrap gap-1.5" aria-label="Tracking hashtags">
              {campaign.data.tracking_hashtags.map((tag) => (
                <li key={tag} className="rounded-full bg-brand-soft px-2.5 py-0.5 text-[11px] text-brand">
                  #{tag}
                </li>
              ))}
            </ul>
          </PageHeader>

          {dashboard.isError && <Alert>{dashboard.error.message}</Alert>}
          {dashboard.data && dashboard.data.creators.length > 0 && (
            <>
              <CampaignTotals totals={dashboard.data.totals} />
              <Suspense fallback={<div className="h-[340px] rounded-card border border-line bg-surface" />}>
                <MetricsChart daily={dashboard.data.daily} />
              </Suspense>
            </>
          )}

          <CampaignCreators campaign={campaign.data} />
          <CampaignPosts campaign={campaign.data} />

          <CampaignFormDialog open={editing} campaign={campaign.data} onClose={() => setEditing(false)} />
        </>
      )}
    </div>
  );
}
