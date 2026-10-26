import { Link } from "react-router-dom";
import type { Overview } from "@/api/queries/overview";
import Avatar from "@/components/ui/Avatar";
import { demoAvatar } from "@/lib/demoImages";
import Icon from "@/components/ui/Icon";
import { formatCount } from "@/lib/format";

// Top three creators by views on posts published in the month.
export default function StandoutCreators({ creators }: { creators: Overview["standout_creators"] }) {
  return (
    <section className="flex min-w-0 flex-col gap-5 rounded-card border border-line bg-surface p-[22px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base text-ink">Standout creators</h2>
          <p className="mt-0.5 text-xs text-ink-muted">Your community, making an impact.</p>
        </div>
        <Link to="/creators" className="shrink-0 text-xs text-brand hover:underline">
          View all →
        </Link>
      </div>
      {creators.length === 0 ? (
        <p className="text-[11px] text-ink-muted">Standouts appear once this month’s posts come in.</p>
      ) : (
        <ul className="flex flex-col gap-4">
          {creators.map((creator) => (
            <li key={creator.id} className="flex items-center gap-2.5">
              <Avatar name={creator.name} src={demoAvatar(creator.handle)} />
              <div className="min-w-0 flex-1">
                <Link to={`/creators/${creator.id}`} className="block truncate text-xs text-ink hover:text-brand">
                  {creator.name}
                </Link>
                <p className="truncate text-[10px] text-ink-muted">@{creator.handle}</p>
              </div>
              <div className="text-right">
                <p className="text-xs font-semibold tabular-nums text-ink">{formatCount(creator.views)}</p>
                <p className="text-[10px] text-on-target">
                  {creator.engagement_rate === null ? "—" : `${(creator.engagement_rate * 100).toFixed(1)}% eng.`}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
      <p className="flex gap-[9px] border-t border-line pt-4 text-[11px] text-ink-muted">
        <Icon name="heart" className="mt-0.5 size-[15px] text-brand" />
        A little appreciation goes a long way. Say thanks to your top creators.
      </p>
    </section>
  );
}
