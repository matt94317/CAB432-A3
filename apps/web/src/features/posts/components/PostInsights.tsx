import type { Post } from "@/api/queries/posts";
import { formatCount } from "@/lib/format";
import { engagementRatio } from "./PostTable";

const monthShort = new Intl.DateTimeFormat(undefined, { month: "short" });
const time = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" });

// The design's two insight cards: the best post in view, and the latest one.
// ("Coming up next" becomes "Latest post": Hookd doesn't track scheduled posts.)
export default function PostInsights({ posts, campaignName }: { posts: Post[]; campaignName: (post: Post) => string }) {
  if (posts.length === 0) return null;
  const top = posts.reduce((best, p) => (p.views > best.views ? p : best), posts[0]);
  const latest = posts.reduce((newest, p) => (p.posted_at > newest.posted_at ? p : newest), posts[0]);
  const weekAgo = Date.now() - 7 * 86400000;
  const thisWeek = posts.filter((p) => new Date(p.posted_at).getTime() >= weekAgo).length;
  const rate = engagementRatio(top);
  const latestDate = new Date(latest.posted_at);

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <section className="flex flex-col gap-[15px] rounded-card border border-line bg-surface p-5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base text-ink">A post worth celebrating</h2>
          <a href={top.url} target="_blank" rel="noreferrer" className="shrink-0 text-xs text-brand hover:underline">
            View post →
          </a>
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-ink">{top.caption || "TikTok post"}</p>
          <p className="mt-1.5 truncate text-[11px] text-ink-muted">
            {top.creator.name} · {campaignName(top)}
          </p>
          <p className="mt-2 flex gap-[22px] text-xs font-semibold">
            <span className="text-ink">{formatCount(top.views)} views</span>
            {rate !== null && <span className="text-on-target">{(rate * 100).toFixed(1)}% engagement</span>}
          </p>
        </div>
      </section>

      <section className="flex flex-col gap-[15px] rounded-card border border-line bg-surface p-5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base text-ink">Latest post</h2>
          <a href={latest.url} target="_blank" rel="noreferrer" className="shrink-0 text-xs text-brand hover:underline">
            View post →
          </a>
        </div>
        <div className="flex items-center gap-3.5">
          <span className="flex h-[72px] w-[62px] shrink-0 flex-col items-center justify-center gap-[3px] rounded-[10px] bg-brand-soft text-brand">
            <span className="text-[10px] uppercase">{monthShort.format(latestDate)}</span>
            <span className="text-[25px] leading-none">{latestDate.getDate()}</span>
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink">{latest.caption || "TikTok post"}</p>
            <p className="mt-1.5 truncate text-[11px] text-ink-muted">
              {latest.creator.name} · {time.format(latestDate)}
            </p>
            <p className="mt-1.5 text-[11px] text-brand">
              {thisWeek === 1 ? "1 post" : `${thisWeek} posts`} in the last 7 days
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
