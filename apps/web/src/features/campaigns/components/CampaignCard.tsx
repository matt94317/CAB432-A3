import { Link } from "react-router-dom";
import type { CampaignListItem } from "@/api/queries/campaigns";
import Icon from "@/components/ui/Icon";
import Menu from "@/components/ui/Menu";
import { demoCover } from "@/lib/demoImages";
import { formatDateRange } from "@/lib/format";
import CampaignStatusBadge from "./CampaignStatusBadge";

const MAX_TAGS = 3;

interface CampaignCardProps {
  campaign: CampaignListItem;
  busy: boolean;
  onEdit: () => void;
  onArchiveToggle: () => void;
  onDelete: () => void;
}

// One campaign in the directory: status, brand, dates, creators and this period's
// posts against target (US-06). Campaigns have no imagery, so the design's cover
// photo is a tinted band with the hashtags (or a stock photo in demo builds).
export default function CampaignCard({ campaign, busy, onEdit, onArchiveToggle, onDelete }: CampaignCardProps) {
  const archived = campaign.status === "archived";
  const progress = campaign.progress;
  const percent = progress && progress.target_posts > 0 ? Math.round((progress.posts / progress.target_posts) * 100) : 0;
  const extraTags = campaign.tracking_hashtags.length - MAX_TAGS;
  const cover = demoCover(campaign.brand, campaign.id);

  return (
    <li className="flex flex-col overflow-hidden rounded-card border border-line bg-surface">
      <div className="relative h-[92px] bg-warm px-[15px] pt-3.5">
        {cover && (
          <img
            src={cover}
            alt=""
            aria-hidden="true"
            loading="lazy"
            className={`absolute inset-0 size-full object-cover ${archived ? "grayscale" : ""}`}
          />
        )}
        <div className="relative flex items-start justify-between">
          <CampaignStatusBadge campaign={campaign} />
          <Menu
            label={`Actions for ${campaign.name}`}
            triggerClassName="flex size-[26px] items-center justify-center rounded-full bg-surface text-ink hover:bg-canvas disabled:opacity-60"
            trigger={<Icon name="ellipsis" className="size-4" />}
            items={[
              ...(archived ? [] : [{ label: "Edit", onSelect: onEdit }]),
              { label: archived ? "Restore" : "Archive", onSelect: onArchiveToggle },
              { label: "Delete", onSelect: onDelete, danger: true },
            ]}
          />
        </div>
        <ul className="absolute bottom-3 left-[15px] right-[15px] flex flex-wrap gap-1.5" aria-label="Tracking hashtags">
          {campaign.tracking_hashtags.slice(0, MAX_TAGS).map((tag) => (
            <li key={tag} className="rounded-full bg-surface/80 px-2 py-0.5 text-[10px] text-brand">
              #{tag}
            </li>
          ))}
          {extraTags > 0 && <li className="px-1 text-[10px] text-brand">+{extraTags}</li>}
        </ul>
      </div>

      <div className={`flex flex-1 flex-col gap-[15px] p-5 ${busy ? "opacity-60" : ""}`}>
        <div className="flex flex-col gap-1.5">
          <p className="truncate text-[9px] uppercase tracking-wide text-ink-muted">{campaign.brand} · UGC campaign</p>
          <Link to={`/campaigns/${campaign.id}`} className="truncate text-[19px] font-semibold text-ink hover:text-brand">
            {campaign.name}
          </Link>
          <p className="flex items-center gap-1.5 text-[11px] text-ink-muted">
            <Icon name="calendar" className="size-3" />
            {formatDateRange(campaign.start_date, campaign.end_date)}
          </p>
        </div>

        {progress && progress.target_posts > 0 ? (
          <>
            <div className="flex items-center justify-between text-[11px] text-ink-muted">
              <span className="flex items-center gap-1.5">
                <Icon name="users" className="size-3.5" />
                {progress.creators} {progress.creators === 1 ? "creator" : "creators"}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex justify-between">
                <span className="text-[11px] font-medium text-ink">
                  {progress.posts} / {progress.target_posts} posts this period
                </span>
                <span className="text-[10px] text-ink-muted">{percent}%</span>
              </div>
              <div className="h-[5px] overflow-hidden rounded-full bg-brand-soft">
                <div className="h-full rounded-full bg-brand" style={{ width: `${Math.min(100, percent)}%` }} />
              </div>
            </div>
            <div className="mt-auto border-t border-line pt-[15px]">
              {progress.behind > 0 ? (
                <p className="flex items-center gap-1.5 text-[10px] text-behind">
                  <Icon name="alert" className="size-3" />
                  {progress.behind} {progress.behind === 1 ? "creator" : "creators"} behind target
                </p>
              ) : (
                <p className="flex items-center gap-1.5 text-[10px] text-on-target">
                  <Icon name="check" className="size-3" />
                  All creators on track
                </p>
              )}
            </div>
          </>
        ) : (
          <p className="mt-auto border-t border-line pt-[15px] text-[11px] text-ink-subtle">No creators assigned yet</p>
        )}
      </div>
    </li>
  );
}
