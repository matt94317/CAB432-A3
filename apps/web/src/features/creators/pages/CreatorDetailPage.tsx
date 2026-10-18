import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useCreator } from "@/api/queries/creators";
import { useCreatorPerformance } from "@/api/queries/dashboard";
import Alert from "@/components/ui/Alert";
import Avatar from "@/components/ui/Avatar";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import CampaignStatusBadge from "@/features/campaigns/components/CampaignStatusBadge";
import CampaignTotals from "@/features/dashboard/components/CampaignTotals";
import PeriodProgress from "@/features/dashboard/components/PeriodProgress";
import ProgressStatusBadge from "@/features/dashboard/components/ProgressStatusBadge";
import PostTable from "@/features/posts/components/PostTable";
import CreatorFormDialog from "../components/CreatorFormDialog";
import DeleteCreatorDialog from "../components/DeleteCreatorDialog";

// One creator: profile and contact details, then their performance across every
// campaign: totals, posts vs target in each campaign, and all their posts (US-21).
export default function CreatorDetailPage() {
  const { creatorId = "" } = useParams();
  const navigate = useNavigate();
  const creator = useCreator(creatorId);
  const performance = useCreatorPerformance(creatorId);
  const campaignNames = new Map(performance.data?.campaigns.map((c) => [c.campaign_id, c.name]));
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  return (
    <div className="flex flex-col gap-[26px]">
      <Link to="/creators" className="inline-flex w-fit items-center gap-1 text-xs text-ink-muted hover:text-ink">
        <Icon name="chevron-right" className="size-3 rotate-180" />
        All creators
      </Link>

      {creator.isPending && <p className="text-[13px] text-ink-muted">Loading creator…</p>}
      {creator.isError && <Alert>{creator.error.message}</Alert>}

      {creator.data && (
        <>
          <section className="overflow-hidden rounded-card border border-line bg-surface">
            <div className="flex h-[72px] items-center bg-brand-soft px-[23px]">
              <p className="text-[11px] font-semibold tracking-wide text-brand">GOOD PEOPLE MAKE GREAT THINGS.</p>
            </div>
            <div className="flex flex-wrap items-center gap-5 px-[23px] py-6">
              <Avatar name={creator.data.name} size="lg" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h1 className="text-[25px] leading-tight text-ink">{creator.data.name}</h1>
                  {creator.data.niche && <Badge tone="brand" dot={false}>{creator.data.niche}</Badge>}
                </div>
                <a
                  href={creator.data.profile_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1.5 text-[13px] text-ink-muted hover:text-ink"
                >
                  <Icon name="music" className="size-3.5" />@{creator.data.handle}
                </a>
                {(creator.data.email || creator.data.phone) && (
                  <p className="mt-1.5 flex flex-wrap gap-x-4 text-[11px] text-ink-muted">
                    {creator.data.email && (
                      <a href={`mailto:${creator.data.email}`} className="hover:text-ink">
                        {creator.data.email}
                      </a>
                    )}
                    {creator.data.phone && (
                      <a href={`tel:${creator.data.phone}`} className="hover:text-ink">
                        {creator.data.phone}
                      </a>
                    )}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => setEditing(true)}>
                  Edit
                </Button>
                <Button variant="secondary" size="sm" className="!text-danger" onClick={() => setDeleting(true)}>
                  Remove
                </Button>
              </div>
            </div>
          </section>

          {performance.isError && <Alert>{performance.error.message}</Alert>}
          {performance.data && performance.data.totals.posts > 0 && <CampaignTotals totals={performance.data.totals} />}

          <section className="overflow-hidden rounded-card border border-line bg-surface">
            <h2 className="px-5 py-4 text-base text-ink">Campaigns</h2>
            {performance.data?.campaigns.length === 0 && (
              <p className="border-t border-line px-5 py-6 text-[13px] text-ink-muted">
                Not on any campaigns yet. Open a campaign and choose “Assign creators” to add them.
              </p>
            )}
            {performance.data && performance.data.campaigns.length > 0 && (
              <>
                <div className="hidden h-11 items-center gap-4 bg-sunken px-5 text-[9px] font-semibold tracking-wide text-ink-muted sm:flex">
                  <span className="flex-1">CAMPAIGN</span>
                  <span className="w-44">THIS PERIOD</span>
                  <span className="w-28 text-right">STATUS</span>
                </div>
                <ul className="divide-y divide-line border-t border-line sm:border-t-0">
                  {performance.data.campaigns.map((row) => (
                    <li key={row.campaign_id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-[13px]">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Link
                            to={`/campaigns/${row.campaign_id}`}
                            className="truncate text-xs font-medium text-ink hover:text-brand"
                          >
                            {row.name}
                          </Link>
                          <CampaignStatusBadge campaign={{ status: row.campaign_status, phase: row.phase }} />
                        </div>
                        <p className="mt-0.5 truncate text-[10px] text-ink-muted">
                          {row.brand} · {row.totals.posts} {row.totals.posts === 1 ? "post" : "posts"}
                        </p>
                      </div>
                      <PeriodProgress progress={row} />
                      <div className="sm:w-28 sm:text-right">
                        <ProgressStatusBadge status={row.status} />
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </section>

          {performance.data && performance.data.posts.length > 0 && (
            <section className="flex flex-col gap-4">
              <h2 className="text-base text-ink">Posts</h2>
              <PostTable
                posts={performance.data.posts}
                editable={false}
                campaignName={(post) => campaignNames.get(post.campaign_id) ?? "Campaign"}
                showCreator={false}
                onMove={() => {}}
                onRemove={() => {}}
              />
            </section>
          )}

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
