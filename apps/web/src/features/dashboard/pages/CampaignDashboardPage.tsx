import { Suspense, lazy, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useCampaign } from "@/api/queries/campaigns";
import { useCampaignDashboard } from "@/api/queries/dashboard";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import CampaignCreators from "@/features/campaigns/components/CampaignCreators";
import CampaignFormDialog from "@/features/campaigns/components/CampaignFormDialog";
import CampaignStatusBadge from "@/features/campaigns/components/CampaignStatusBadge";
import CampaignPosts from "@/features/posts/components/CampaignPosts";
import { formatDateRange } from "@/lib/format";
import CampaignTotals from "../components/CampaignTotals";

// Recharts is large; load it only when a dashboard has a chart to draw
const MetricsChart = lazy(() => import("../components/MetricsChart"));

// Campaign dashboard: totals and daily views (US-20), each creator's posts vs target
// with behind-target flags (US-19, US-22), and the campaign's posts.
export default function CampaignDashboardPage() {
  const { campaignId = "" } = useParams();
  const campaign = useCampaign(campaignId);
  const dashboard = useCampaignDashboard(campaignId);
  const [editing, setEditing] = useState(false);

  return (
    <div className="px-4 py-6 sm:px-6">
      <Link to="/campaigns" className="text-sm text-gray-500 hover:text-gray-900">
        ← All campaigns
      </Link>

      {campaign.isPending && <p className="mt-6 text-sm text-gray-500">Loading campaign…</p>}
      {campaign.isError && (
        <div className="mt-6">
          <Alert>{campaign.error.message}</Alert>
        </div>
      )}

      {campaign.data && (
        <>
          <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-semibold text-gray-900">{campaign.data.name}</h1>
                <CampaignStatusBadge campaign={campaign.data} />
              </div>
              <p className="mt-1 text-sm text-gray-500">
                {campaign.data.brand} · {formatDateRange(campaign.data.start_date, campaign.data.end_date)}
              </p>
              <ul className="mt-3 flex flex-wrap gap-1.5" aria-label="Tracking hashtags">
                {campaign.data.tracking_hashtags.map((tag) => (
                  <li key={tag} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                    #{tag}
                  </li>
                ))}
              </ul>
            </div>
            {campaign.data.status === "active" && (
              <Button variant="secondary" onClick={() => setEditing(true)}>
                Edit campaign
              </Button>
            )}
          </div>

          {dashboard.isError && (
            <div className="mt-6">
              <Alert>{dashboard.error.message}</Alert>
            </div>
          )}
          {dashboard.data && dashboard.data.creators.length > 0 && (
            <div className="mt-6 flex flex-col gap-4">
              <CampaignTotals totals={dashboard.data.totals} />
              <Suspense fallback={<div className="h-72 rounded-xl border border-gray-200 bg-white" />}>
                <MetricsChart daily={dashboard.data.daily} />
              </Suspense>
            </div>
          )}

          <CampaignCreators campaign={campaign.data} />
          <CampaignPosts campaign={campaign.data} />

          <CampaignFormDialog open={editing} campaign={campaign.data} onClose={() => setEditing(false)} />
        </>
      )}
    </div>
  );
}
