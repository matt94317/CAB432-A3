import { Link } from "react-router-dom";
import type { Post } from "@/api/queries/posts";
import Avatar from "@/components/ui/Avatar";
import Icon from "@/components/ui/Icon";
import Menu from "@/components/ui/Menu";
import { formatCount, formatExact } from "@/lib/format";

export type PostSort = "posted" | "views" | "engagement";

interface PostTableProps {
  posts: Post[];
  editable: boolean;
  /** Adds a campaign column. */
  campaignName?: (post: Post) => string;
  /** Hide the creator column, e.g. on a creator's own page. */
  showCreator?: boolean;
  /** Makes the views, engagement rate and posted headings sort buttons. */
  sort?: PostSort;
  onSort?: (sort: PostSort) => void;
  onMove: (post: Post) => void;
  onRemove: (post: Post) => void;
}

const METRICS = [
  { key: "views", label: "VIEWS" },
  { key: "likes", label: "LIKES" },
  { key: "comments", label: "COMMENTS" },
  { key: "shares", label: "SHARES" },
] as const;

const dateFormat = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric" });
const timeFormat = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" });

export function engagementRatio(post: Post): number | null {
  return post.views ? (post.likes + post.comments + post.shares) / post.views : null;
}

function engagementRate(post: Post): string | null {
  const ratio = engagementRatio(post);
  return ratio === null ? null : `${(ratio * 100).toFixed(1)}%`;
}

// Posts with views, likes, comments, shares and engagement rate (US-17), in the
// design's post tracking table. Scrolls sideways on small screens.
export default function PostTable({
  posts,
  editable,
  campaignName,
  showCreator = true,
  sort,
  onSort,
  onMove,
  onRemove,
}: PostTableProps) {
  const heading = "px-3 text-[9px] font-semibold tracking-wide text-ink-muted";
  // A heading that sorts the table when the page supports it ("VIEWS ↓")
  const sortable = (key: PostSort, label: string) =>
    onSort ? (
      <button
        type="button"
        onClick={() => onSort(key)}
        aria-pressed={sort === key}
        className={`font-semibold tracking-wide hover:text-ink ${sort === key ? "text-ink" : ""}`}
      >
        {label}
        {sort === key && " ↓"}
      </button>
    ) : (
      label
    );
  return (
    <div className="overflow-x-auto rounded-card border border-line bg-surface">
      <table className="w-full min-w-[52rem] text-left">
        <thead className="h-11 bg-sunken">
          <tr>
            <th scope="col" className={`${heading} pl-5`}>
              POST
            </th>
            {showCreator && (
              <th scope="col" className={heading}>
                CREATOR
              </th>
            )}
            {campaignName && (
              <th scope="col" className={heading}>
                CAMPAIGN
              </th>
            )}
            {METRICS.map((m) => (
              <th
                key={m.key}
                scope="col"
                className={`${heading} text-right`}
                aria-sort={sort === "views" && m.key === "views" ? "descending" : undefined}
              >
                {m.key === "views" ? sortable("views", m.label) : m.label}
              </th>
            ))}
            <th scope="col" className={`${heading} text-right`} aria-sort={sort === "engagement" ? "descending" : undefined}>
              {sortable("engagement", "ENG. RATE")}
            </th>
            <th scope="col" className={heading} aria-sort={sort === "posted" ? "descending" : undefined}>
              {sortable("posted", "POSTED")}
            </th>
            <th scope="col" className="pr-5">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {posts.map((post) => {
            const rate = engagementRate(post);
            const posted = new Date(post.posted_at);
            return (
              <tr key={post.id} className="align-middle">
                <td className="max-w-64 py-[13px] pl-5 pr-3">
                  <p className="line-clamp-2 text-[11px] text-ink" title={post.caption || undefined}>
                    {post.caption || "TikTok post"}
                  </p>
                  <p className="mt-1 flex items-center gap-[5px] text-[10px] text-ink-muted">
                    <Icon name="music" className="size-[11px]" />
                    TikTok · {post.match_source === "manual" ? "added manually" : "matched by hashtag"}
                    {post.last_synced_at === null && " · not synced"}
                  </p>
                </td>
                {showCreator && (
                  <td className="px-3 py-[13px]">
                    <div className="flex items-center gap-2">
                      <Avatar name={post.creator.name} size="sm" />
                      <div className="min-w-0">
                        <Link
                          to={`/creators/${post.creator.id}`}
                          className="block truncate text-[11px] font-medium text-ink hover:text-brand"
                        >
                          {post.creator.name}
                        </Link>
                        <p className="truncate text-[9px] text-ink-muted">@{post.creator.handle}</p>
                      </div>
                    </div>
                  </td>
                )}
                {campaignName && (
                  <td className="max-w-44 px-3 py-[13px]">
                    <Link
                      to={`/campaigns/${post.campaign_id}`}
                      className="line-clamp-2 text-[11px] text-ink-muted hover:text-ink"
                    >
                      {campaignName(post)}
                    </Link>
                  </td>
                )}
                {METRICS.map((m) => (
                  <td
                    key={m.key}
                    className="px-3 py-[13px] text-right text-xs tabular-nums text-ink"
                    title={formatExact(post[m.key])}
                  >
                    {formatCount(post[m.key])}
                  </td>
                ))}
                <td className={`px-3 py-[13px] text-right text-xs tabular-nums ${rate ? "text-on-target" : "text-ink-subtle"}`}>
                  {rate ?? "—"}
                </td>
                <td className="whitespace-nowrap px-3 py-[13px]">
                  <p className="text-[10px] text-ink">{dateFormat.format(posted)}</p>
                  <p className="mt-1 text-[9px] text-ink-muted">{timeFormat.format(posted)}</p>
                </td>
                <td className="py-[13px] pr-5">
                  <div className="flex items-center justify-end gap-2">
                    <a
                      href={post.url}
                      target="_blank"
                      rel="noreferrer"
                      aria-label="Open on TikTok"
                      className="flex size-[26px] items-center justify-center rounded-full text-ink-muted hover:bg-canvas hover:text-ink"
                    >
                      <Icon name="external-link" className="size-[15px]" />
                    </a>
                    {editable && (
                      <Menu
                        label="Post actions"
                        triggerClassName="flex size-[26px] items-center justify-center rounded-full text-ink-muted hover:bg-canvas hover:text-ink"
                        trigger={<Icon name="ellipsis" className="size-[15px]" />}
                        items={[
                          { label: "Move to another campaign", onSelect: () => onMove(post) },
                          { label: "Remove post", onSelect: () => onRemove(post), danger: true },
                        ]}
                      />
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
