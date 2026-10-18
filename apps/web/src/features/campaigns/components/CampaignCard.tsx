import { Link } from "react-router-dom";
import type { CampaignListItem } from "@/api/queries/campaigns";
import Button from "@/components/ui/Button";
import { formatDateRange } from "@/lib/format";
import CampaignStatusBadge from "./CampaignStatusBadge";

const MAX_TAGS = 4;

interface CampaignCardProps {
  campaign: CampaignListItem;
  busy: boolean;
  onEdit: () => void;
  onArchiveToggle: () => void;
  onDelete: () => void;
}

// One campaign in the list: status, dates, hashtags and progress at a glance (US-06).
export default function CampaignCard({ campaign, busy, onEdit, onArchiveToggle, onDelete }: CampaignCardProps) {
  const archived = campaign.status === "archived";
  const extraTags = campaign.tracking_hashtags.length - MAX_TAGS;
  const progress = campaign.progress;

  return (
    <li className="flex flex-col rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            to={`/campaigns/${campaign.id}`}
            className="block truncate font-semibold text-gray-900 hover:text-brand"
          >
            {campaign.name}
          </Link>
          <p className="truncate text-sm text-gray-500">{campaign.brand}</p>
        </div>
        <CampaignStatusBadge campaign={campaign} />
      </div>

      <p className="mt-3 text-sm text-gray-600">{formatDateRange(campaign.start_date, campaign.end_date)}</p>

      <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Tracking hashtags">
        {campaign.tracking_hashtags.slice(0, MAX_TAGS).map((tag) => (
          <li key={tag} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
            #{tag}
          </li>
        ))}
        {extraTags > 0 && <li className="px-1 text-xs text-gray-500">+{extraTags} more</li>}
      </ul>

      <div className="mt-4 text-sm">
        {progress && progress.target_posts > 0 ? (
          <>
            <div className="flex justify-between text-gray-600">
              <span>{progress.creators} creators</span>
              <span>
                {progress.posts} / {progress.target_posts} posts
              </span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full bg-brand"
                style={{ width: `${Math.min(100, (progress.posts / progress.target_posts) * 100)}%` }}
              />
            </div>
          </>
        ) : (
          <p className="text-gray-400">No creators assigned yet</p>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-gray-100 pt-3">
        {!archived && (
          <Button variant="link" onClick={onEdit} disabled={busy}>
            Edit
          </Button>
        )}
        <Button variant="link" onClick={onArchiveToggle} disabled={busy}>
          {archived ? "Restore" : "Archive"}
        </Button>
        <Button variant="link" onClick={onDelete} disabled={busy} className="ml-auto !text-red-600">
          Delete
        </Button>
      </div>
    </li>
  );
}
