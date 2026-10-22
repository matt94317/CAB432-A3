import { Link } from "react-router-dom";
import type { Overview } from "@/api/queries/overview";
import Badge from "@/components/ui/Badge";
import { formatDate } from "@/lib/format";

// Live campaigns with this period's posts against target, and the next one to wrap up.
export default function ActiveCampaigns({ overview }: { overview: Overview }) {
  const rows = overview.active_campaigns;
  return (
    <section className="flex min-w-0 flex-col gap-5 rounded-card border border-line bg-surface p-[22px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base text-ink">Active campaigns</h2>
          <p className="mt-0.5 text-xs text-ink-muted">
            {rows.length === 0
              ? "No live campaigns right now."
              : `${rows.length} live ${rows.length === 1 ? "campaign" : "campaigns"}. Plenty of possibility.`}
          </p>
        </div>
        <Link to="/campaigns" className="shrink-0 text-xs text-brand hover:underline">
          View all →
        </Link>
      </div>

      {rows.length > 0 && (
        <>
          <div className="hidden text-[10px] text-ink-subtle sm:flex">
            <span className="flex-1">CAMPAIGN</span>
            <span className="w-[195px]">THIS PERIOD</span>
            <span className="w-28">STATUS</span>
          </div>
          <ul className="flex flex-col gap-4">
            {rows.map((row) => {
              const share = row.target_posts ? Math.min(100, (row.posts / row.target_posts) * 100) : 0;
              return (
                <li key={row.id} className="flex flex-wrap items-center gap-x-4 gap-y-2">
                  <div className="flex w-full min-w-0 items-center gap-[11px] sm:w-auto sm:flex-1">
                    <span
                      aria-hidden="true"
                      className="flex size-[42px] shrink-0 items-center justify-center rounded-lg bg-warm text-sm font-semibold text-ink"
                    >
                      {row.brand.slice(0, 1).toUpperCase()}
                    </span>
                    <div className="min-w-0">
                      <Link to={`/campaigns/${row.id}`} className="block truncate text-xs text-ink hover:text-brand">
                        {row.name}
                      </Link>
                      <p className="truncate text-[10px] text-ink-muted">
                        {row.brand} · ends {formatDate(row.end_date)}
                      </p>
                    </div>
                  </div>
                  <div className="w-[195px]">
                    <p className="text-[11px] text-ink-muted">
                      {row.target_posts ? `${row.posts} / ${row.target_posts} posts` : "No targets yet"}
                    </p>
                    <div className="mt-[7px] h-[5px] w-[145px] overflow-hidden rounded-full bg-brand-soft">
                      <div className="h-full rounded-full bg-brand" style={{ width: `${share}%` }} />
                    </div>
                  </div>
                  <div className="w-28">
                    {row.creators === 0 ? (
                      <Badge dot={false}>No creators</Badge>
                    ) : row.behind > 0 ? (
                      <Badge tone="warning" dot={false}>
                        {row.behind} behind
                      </Badge>
                    ) : (
                      <Badge tone="success" dot={false}>
                        On track
                      </Badge>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </>
      )}

      {overview.next_milestone && (
        <p className="border-t border-line pt-4 text-[11px] text-ink-muted">
          Next milestone:{" "}
          <Link to={`/campaigns/${overview.next_milestone.campaign_id}`} className="text-ink hover:text-brand">
            {overview.next_milestone.name}
          </Link>{" "}
          wraps on {formatDate(overview.next_milestone.end_date)}.
        </p>
      )}
    </section>
  );
}
