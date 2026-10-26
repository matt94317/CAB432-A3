import { Link } from "react-router-dom";
import type { Creator } from "@/api/queries/creators";
import Avatar from "@/components/ui/Avatar";
import { demoAvatar } from "@/lib/demoImages";
import Badge from "@/components/ui/Badge";
import Icon from "@/components/ui/Icon";
import Menu from "@/components/ui/Menu";

interface CreatorCardProps {
  creator: Creator;
  onEdit: () => void;
  onRemove: () => void;
}

// One creator in the roster (US-07, US-08). The design's portrait photo becomes a
// tinted band with an initials avatar, since creators have no photos yet.
export default function CreatorCard({ creator, onEdit, onRemove }: CreatorCardProps) {
  const campaigns = creator.campaign_count;
  return (
    <li className="flex flex-col overflow-hidden rounded-card border border-line bg-surface">
      <div className="relative flex h-[110px] items-end bg-warm px-5 pb-0">
        <div className="absolute left-3.5 top-3.5">
          {campaigns > 0 ? (
            <Badge tone="success">
              On {campaigns} {campaigns === 1 ? "campaign" : "campaigns"}
            </Badge>
          ) : (
            <Badge>Not assigned</Badge>
          )}
        </div>
        <div className="absolute right-3.5 top-3.5">
          <Menu
            label={`Actions for ${creator.name}`}
            triggerClassName="flex size-[29px] items-center justify-center rounded-full bg-surface text-ink hover:bg-canvas"
            trigger={<Icon name="ellipsis" className="size-4" />}
            items={[
              { label: "Edit", onSelect: onEdit },
              { label: "Remove", onSelect: onRemove, danger: true },
            ]}
          />
        </div>
        <span className="translate-y-1/2 rounded-full ring-4 ring-surface">
          <Avatar name={creator.name} size="lg" src={demoAvatar(creator.handle)} />
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-3.5 p-5 pt-12">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <Link to={`/creators/${creator.id}`} className="block truncate text-lg font-semibold text-ink hover:text-brand">
              {creator.name}
            </Link>
            <p className="truncate text-[11px] text-ink-muted">@{creator.handle}</p>
          </div>
          <a
            href={creator.profile_url}
            target="_blank"
            rel="noreferrer"
            aria-label={`@${creator.handle} on TikTok`}
            className="mt-1 text-ink-muted hover:text-ink"
          >
            <Icon name="music" className="size-[15px]" />
          </a>
        </div>

        <p className="text-[10px] text-ink-muted">{creator.niche ?? "No niche set"}</p>

        <div className="flex flex-col gap-1 rounded-lg bg-canvas px-3.5 py-3 text-[11px]">
          {creator.email || creator.phone ? (
            <>
              {creator.email && <span className="truncate text-ink">{creator.email}</span>}
              {creator.phone && <span className="truncate text-ink-muted">{creator.phone}</span>}
            </>
          ) : (
            <span className="text-ink-subtle">No contact details yet</span>
          )}
        </div>

        <div className="mt-auto grid grid-cols-2 gap-2">
          <Link
            to={`/creators/${creator.id}`}
            className="flex h-9 items-center justify-center rounded-lg border border-line bg-surface text-xs font-semibold text-ink hover:bg-canvas"
          >
            View profile
          </Link>
          <button
            type="button"
            onClick={onEdit}
            className="flex h-9 items-center justify-center rounded-lg bg-brand-soft text-xs font-semibold text-brand hover:bg-brand-muted/60"
          >
            Edit
          </button>
        </div>
      </div>
    </li>
  );
}
