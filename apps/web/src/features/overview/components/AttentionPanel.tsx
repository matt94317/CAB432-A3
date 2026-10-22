import { Link } from "react-router-dom";
import type { AttentionItem } from "@/api/queries/overview";
import Badge from "@/components/ui/Badge";
import Icon, { type IconName } from "@/components/ui/Icon";

const KINDS: Record<AttentionItem["kind"], { icon: IconName; colour: string }> = {
  behind: { icon: "alert", colour: "text-behind" },
  ending_soon: { icon: "calendar-clock", colour: "text-behind" },
  no_creators: { icon: "users", colour: "text-brand" },
  not_synced: { icon: "refresh", colour: "text-ink-muted" },
};

const MAX_ITEMS = 5;

// "Needs your attention": real to-dos, each linking to the campaign to act on.
export default function AttentionPanel({ items }: { items: AttentionItem[] }) {
  const shown = items.slice(0, MAX_ITEMS);
  return (
    <section className="flex flex-col gap-[18px] rounded-card border border-line bg-surface p-[22px]">
      <h2 className="text-base text-ink">Needs your attention</h2>
      <div className="flex items-center gap-2">
        {items.length > 0 ? (
          <Badge tone="warning" dot={false}>
            {items.length === 1 ? "1 to-do" : `${items.length} to-dos`}
          </Badge>
        ) : (
          <Badge tone="success" dot={false}>
            All clear
          </Badge>
        )}
        <span className="text-[11px] text-ink-muted">
          {items.length > 0 ? "Let’s keep things moving." : "Nothing needs you right now."}
        </span>
      </div>
      {shown.length > 0 && (
        <ul className="flex flex-col gap-[14px]">
          {shown.map((item) => {
            const { icon, colour } = KINDS[item.kind];
            const body = (
              <>
                <span className="flex size-[34px] shrink-0 items-center justify-center rounded-[9px] bg-canvas">
                  <Icon name={icon} className={`size-[17px] ${colour}`} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-xs text-ink">{item.title}</span>
                  <span className="block truncate text-[11px] text-ink-muted">{item.detail}</span>
                </span>
                <Icon name="chevron-right" className="size-3.5 text-ink-muted" />
              </>
            );
            return (
              <li key={`${item.kind}-${item.campaign_id}-${item.title}`}>
                {item.campaign_id ? (
                  <Link to={`/campaigns/${item.campaign_id}`} className="flex items-center gap-[11px] rounded-lg hover:bg-canvas">
                    {body}
                  </Link>
                ) : (
                  <div className="flex items-center gap-[11px]">{body}</div>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {items.length > MAX_ITEMS && (
        <Link to="/campaigns" className="text-xs text-brand hover:underline">
          +{items.length - MAX_ITEMS} more on Campaigns
        </Link>
      )}
    </section>
  );
}
