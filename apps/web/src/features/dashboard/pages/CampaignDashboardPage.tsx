import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useCampaign } from "@/api/queries/campaigns";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import CampaignCreators from "@/features/campaigns/components/CampaignCreators";
import CampaignFormDialog from "@/features/campaigns/components/CampaignFormDialog";
import CampaignStatusBadge from "@/features/campaigns/components/CampaignStatusBadge";
import { formatDateRange } from "@/lib/format";

// Campaign dashboard (US-19, US-20, US-22). Shows the campaign and its creators with
// their targets; posts, progress, totals and behind-target flags arrive with Epics 4 and 5.
export default function CampaignDashboardPage() {
  const { campaignId = "" } = useParams();
  const campaign = useCampaign(campaignId);
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

          <CampaignCreators campaign={campaign.data} />

          <CampaignFormDialog open={editing} campaign={campaign.data} onClose={() => setEditing(false)} />
        </>
      )}
    </div>
  );
}
