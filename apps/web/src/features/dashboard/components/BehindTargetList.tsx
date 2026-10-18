import { Link } from "react-router-dom";
import { useBehindTarget } from "@/api/queries/dashboard";
import Alert from "@/components/ui/Alert";
import Avatar from "@/components/ui/Avatar";
import Badge from "@/components/ui/Badge";
import PeriodProgress from "./PeriodProgress";

// Who to chase: creators behind target this period on any live campaign (US-22).
export default function BehindTargetList() {
  const behind = useBehindTarget();

  if (behind.isError) return <Alert>{behind.error.message}</Alert>;
  if (!behind.data || behind.data.length === 0) return null;

  return (
    <section className="rounded-card border border-line bg-surface p-[22px]" aria-labelledby="behind-heading">
      <div className="flex flex-wrap items-center gap-3">
        <h2 id="behind-heading" className="text-base text-ink">
          Needs your attention
        </h2>
        <Badge tone="warning">
          {behind.data.length} behind target this period
        </Badge>
      </div>
      <ul className="mt-3 divide-y divide-line">
        {behind.data.map((item) => (
          <li key={`${item.campaign_id}-${item.creator.id}`} className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
            <Avatar name={item.creator.name} />
            <div className="min-w-0 flex-1">
              <Link to={`/creators/${item.creator.id}`} className="block truncate text-[13px] text-ink hover:text-brand">
                {item.creator.name}
              </Link>
              <p className="truncate text-[11px] text-ink-muted">
                <Link to={`/campaigns/${item.campaign_id}`} className="hover:text-ink">
                  {item.campaign_name}
                </Link>{" "}
                · {item.remaining} more this {item.target_period}
              </p>
            </div>
            <PeriodProgress progress={item} />
            {item.email && (
              <a href={`mailto:${item.email}`} className="text-xs font-semibold text-brand hover:underline">
                Email
              </a>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
