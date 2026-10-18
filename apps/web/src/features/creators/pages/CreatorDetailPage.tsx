import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useCreator, useCreatorCampaigns } from "@/api/queries/creators";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import CampaignStatusBadge from "@/features/campaigns/components/CampaignStatusBadge";
import { formatTarget } from "@/lib/targets";
import CreatorFormDialog from "../components/CreatorFormDialog";
import DeleteCreatorDialog from "../components/DeleteCreatorDialog";

// One creator: profile, contact details and the campaigns they're on with their
// target in each. Posts and performance across campaigns arrive with US-21.
export default function CreatorDetailPage() {
  const { creatorId = "" } = useParams();
  const navigate = useNavigate();
  const creator = useCreator(creatorId);
  const campaigns = useCreatorCampaigns(creatorId);
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  return (
    <div className="px-4 py-6 sm:px-6">
      <Link to="/creators" className="text-sm text-gray-500 hover:text-gray-900">
        ← All creators
      </Link>

      {creator.isPending && <p className="mt-6 text-sm text-gray-500">Loading creator…</p>}
      {creator.isError && (
        <div className="mt-6">
          <Alert>{creator.error.message}</Alert>
        </div>
      )}

      {creator.data && (
        <>
          <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl font-semibold text-gray-900">{creator.data.name}</h1>
              <p className="mt-1 text-sm text-gray-500">
                <a
                  href={creator.data.profile_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand underline-offset-4 hover:underline"
                >
                  @{creator.data.handle}
                </a>
                {creator.data.niche && ` · ${creator.data.niche}`}
              </p>
              {(creator.data.email || creator.data.phone) && (
                <p className="mt-2 flex flex-wrap gap-x-4 text-sm text-gray-600">
                  {creator.data.email && (
                    <a href={`mailto:${creator.data.email}`} className="hover:text-gray-900">
                      {creator.data.email}
                    </a>
                  )}
                  {creator.data.phone && (
                    <a href={`tel:${creator.data.phone}`} className="hover:text-gray-900">
                      {creator.data.phone}
                    </a>
                  )}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setEditing(true)}>
                Edit
              </Button>
              <Button variant="secondary" className="!text-red-600" onClick={() => setDeleting(true)}>
                Remove
              </Button>
            </div>
          </div>

          <section className="mt-8">
            <h2 className="text-lg font-semibold text-gray-900">Campaigns</h2>
            {campaigns.isError && (
              <div className="mt-3">
                <Alert>{campaigns.error.message}</Alert>
              </div>
            )}
            {campaigns.data?.length === 0 && (
              <p className="mt-2 text-sm text-gray-500">
                Not on any campaigns yet. Open a campaign and choose “Assign creators” to add them.
              </p>
            )}
            {campaigns.data && campaigns.data.length > 0 && (
              <ul className="mt-3 divide-y divide-gray-100 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                {campaigns.data.map((row) => (
                  <li key={row.campaign_id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3">
                    <div className="min-w-0 flex-1">
                      <Link
                        to={`/campaigns/${row.campaign_id}`}
                        className="block truncate font-medium text-gray-900 hover:text-brand"
                      >
                        {row.name}
                      </Link>
                      <p className="truncate text-sm text-gray-500">{row.brand}</p>
                    </div>
                    <span className="text-sm text-gray-600">{formatTarget(row.target_posts, row.target_period)}</span>
                    <CampaignStatusBadge campaign={row} />
                  </li>
                ))}
              </ul>
            )}
          </section>

          <CreatorFormDialog open={editing} creator={creator.data} onClose={() => setEditing(false)} />
          <DeleteCreatorDialog
            creator={deleting ? creator.data : undefined}
            onClose={() => setDeleting(false)}
            onDeleted={() => navigate("/creators", { replace: true })}
          />
        </>
      )}
    </div>
  );
}
