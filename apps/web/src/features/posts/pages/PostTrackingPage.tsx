import { useState } from "react";
import { useCampaigns } from "@/api/queries/campaigns";
import { type Post, useAllPosts, useRemovePost, useSyncAll } from "@/api/queries/posts";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FilterSelect from "@/components/ui/FilterSelect";
import Icon from "@/components/ui/Icon";
import PageHeader from "@/components/ui/PageHeader";
import Pagination from "@/components/ui/Pagination";
import SearchField from "@/components/ui/SearchField";
import StatCard from "@/components/ui/StatCard";
import Tabs from "@/components/ui/Tabs";
import { formatCount, formatExact, formatRelative } from "@/lib/format";
import AddPostDialog from "../components/AddPostDialog";
import MovePostDialog from "../components/MovePostDialog";
import PostInsights from "../components/PostInsights";
import PostTable, { type PostSort, engagementRatio } from "../components/PostTable";
import { downloadPostsCsv } from "../csv";

type Source = "all" | "hashtag" | "manual";
type Range = "all" | "7" | "30" | "month";

const PAGE_SIZE = 10;
const RANGES: { value: Range; label: string }[] = [
  { value: "all", label: "All time" },
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
  { value: "month", label: "This month" },
];

function inRange(post: Post, range: Range, now = new Date()): boolean {
  const posted = new Date(post.posted_at);
  if (range === "all") return true;
  if (range === "month") return posted.getFullYear() === now.getFullYear() && posted.getMonth() === now.getMonth();
  return now.getTime() - posted.getTime() <= Number(range) * 86400000;
}

const SORTS: Record<PostSort, (a: Post, b: Post) => number> = {
  posted: (a, b) => b.posted_at.localeCompare(a.posted_at),
  views: (a, b) => b.views - a.views,
  engagement: (a, b) => (engagementRatio(b) ?? -1) - (engagementRatio(a) ?? -1),
};

// Every tracked post across campaigns: totals, filters, the post table and highlights
// (US-15 to US-18), from the design's post tracking page.
export default function PostTrackingPage() {
  const posts = useAllPosts();
  const campaigns = useCampaigns("all");
  const sync = useSyncAll();
  const remove = useRemovePost();

  const [source, setSource] = useState<Source>("all");
  const [campaignId, setCampaignId] = useState("all");
  const [range, setRange] = useState<Range>("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<PostSort>("views");
  const [page, setPage] = useState(1);
  const [adding, setAdding] = useState(false);
  const [moving, setMoving] = useState<Post | undefined>();
  const [removing, setRemoving] = useState<Post | undefined>();

  const campaignsById = new Map(campaigns.data?.map((c) => [c.id, c]));
  const campaignName = (post: Post) => campaignsById.get(post.campaign_id)?.name ?? "Campaign";
  const editable = (post: Post) => campaignsById.get(post.campaign_id)?.status === "active";

  const needle = search.trim().replace(/^@/, "").toLowerCase();
  const filtered = (posts.data ?? []).filter(
    (p) =>
      (campaignId === "all" || p.campaign_id === campaignId) &&
      inRange(p, range) &&
      (!needle ||
        p.caption.toLowerCase().includes(needle) ||
        p.creator.name.toLowerCase().includes(needle) ||
        p.creator.handle.includes(needle)),
  );
  const shown = filtered.filter((p) => source === "all" || p.match_source === source).sort(SORTS[sort]);
  const pageCount = Math.max(1, Math.ceil(shown.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const pageRows = shown.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const views = shown.reduce((s, p) => s + p.views, 0);
  const engagement = shown.reduce((s, p) => s + p.likes + p.comments + p.shares, 0);
  const lastSynced = (posts.data ?? []).reduce<string | null>(
    (latest, p) => (p.last_synced_at && (!latest || p.last_synced_at > latest) ? p.last_synced_at : latest),
    null,
  );

  const filterTo = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setPage(1);
  };

  return (
    <div className="flex flex-col gap-[26px]">
      <PageHeader
        title="Every post. The whole picture."
        description="From first post to real impact. Follow your content’s journey."
        actions={
          <>
            <Button
              variant="secondary"
              icon="download"
              disabled={shown.length === 0}
              onClick={() => downloadPostsCsv(shown, campaignName, `hookd-posts-${new Date().toISOString().slice(0, 10)}.csv`)}
            >
              Export report
            </Button>
            <Button icon="plus" onClick={() => setAdding(true)}>
              Add post
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:gap-[18px] lg:grid-cols-4">
        <StatCard icon="eye" label="Total views" value={formatCount(views)} note={`Across ${shown.length} ${shown.length === 1 ? "post" : "posts"}`} title={`${formatExact(views)} views`} />
        <StatCard icon="heart" label="Total engagements" value={formatCount(engagement)} note="Likes, comments and shares" />
        <StatCard icon="check" label="Published posts" value={formatExact(shown.length)} note="In this view" />
        <StatCard
          icon="trending-up"
          label="Avg. engagement rate"
          value={views ? `${((engagement / views) * 100).toFixed(1)}%` : "–"}
          note="Engagements per view"
        />
      </div>

      <div className="flex flex-col gap-5">
        <Tabs
          label="Post source"
          value={source}
          onChange={filterTo(setSource)}
          tabs={[
            { value: "all", label: "All posts", count: filtered.length },
            { value: "hashtag", label: "Matched by hashtag", count: filtered.filter((p) => p.match_source === "hashtag").length },
            { value: "manual", label: "Added manually", count: filtered.filter((p) => p.match_source === "manual").length },
          ]}
        />

        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex w-full flex-wrap gap-[9px] sm:w-auto">
            <SearchField label="Search posts" placeholder="Search posts or creators..." value={search} onChange={filterTo(setSearch)} />
            <FilterSelect
              label="Campaign"
              value={campaignId}
              onChange={filterTo(setCampaignId)}
              options={[{ value: "all", label: "All campaigns" }, ...(campaigns.data ?? []).map((c) => ({ value: c.id, label: c.name }))]}
            />
            <FilterSelect label="Date range" value={range} onChange={filterTo(setRange)} options={RANGES} />
          </div>
          <div className="flex items-center gap-[7px]">
            <Icon name="refresh" className="size-3 text-ink-muted" />
            <span className="text-[10px] text-ink-muted">{lastSynced ? `Synced ${formatRelative(lastSynced)}` : "Not synced yet"}</span>
            <Button variant="secondary" size="sm" loading={sync.isPending} onClick={() => sync.mutate()}>
              Sync now
            </Button>
          </div>
        </div>

        {sync.error && <Alert>{sync.error.message}</Alert>}
        {sync.data && (
          <Alert tone="success">
            {sync.data.mode === "queued"
              ? `Sync queued for ${sync.data.creators} creators. Posts will update shortly.`
              : `Synced ${sync.data.creators} ${sync.data.creators === 1 ? "creator" : "creators"}: ${sync.data.added ?? 0} new, ${sync.data.updated ?? 0} updated.`}
            {(sync.data.failed?.length ?? 0) > 0 && ` Couldn't sync ${sync.data.failed!.map((f) => `@${f.handle}`).join(", ")}.`}
          </Alert>
        )}
        {posts.isPending && <p className="text-[13px] text-ink-muted">Loading posts…</p>}
        {posts.isError && <Alert>{posts.error.message}</Alert>}

        {posts.data && shown.length === 0 && (
          <div className="rounded-card border border-dashed border-line-strong bg-surface px-6 py-12 text-center">
            <p className="font-medium text-ink">{posts.data.length === 0 ? "No posts tracked yet" : "No posts match these filters"}</p>
            <p className="mt-1 text-[13px] text-ink-muted">
              {posts.data.length === 0
                ? "Assign creators to a live campaign and sync, or add a post by link."
                : "Try another campaign, date range or search."}
            </p>
          </div>
        )}

        {pageRows.length > 0 && (
          <div className="overflow-hidden rounded-card border border-line bg-surface">
            <div className="[&>div]:rounded-none [&>div]:border-0">
              <PostTable
                posts={pageRows}
                editable={pageRows.some(editable)}
                campaignName={campaignName}
                sort={sort}
                onSort={filterTo(setSort)}
                onMove={setMoving}
                onRemove={setRemoving}
              />
            </div>
            <div className="border-t border-line">
              <Pagination page={currentPage} pageSize={PAGE_SIZE} total={shown.length} noun="posts" onPage={setPage} />
            </div>
          </div>
        )}
      </div>

      <PostInsights posts={shown} campaignName={campaignName} />

      <AddPostDialog open={adding} onClose={() => setAdding(false)} />
      <MovePostDialog post={moving} onClose={() => setMoving(undefined)} />
      <ConfirmDialog
        open={removing !== undefined}
        title="Remove post?"
        confirmLabel="Remove post"
        danger
        pending={remove.isPending}
        error={remove.error?.message}
        onCancel={() => {
          remove.reset();
          setRemoving(undefined);
        }}
        onConfirm={() => removing && remove.mutate(removing.id, { onSuccess: () => setRemoving(undefined) })}
      >
        <p>
          This post by <span className="font-medium text-ink">@{removing?.creator.handle}</span> will stop counting toward{" "}
          {removing && campaignName(removing)}. Sync won't add it back; you can add it again by link.
        </p>
      </ConfirmDialog>
    </div>
  );
}
