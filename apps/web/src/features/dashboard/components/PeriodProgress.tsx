import type { CreatorProgressRow } from "@/api/queries/dashboard";
import { formatDate } from "@/lib/format";

// The period fields every progress row shares (campaign, behind-target and creator views)
type Progress = Pick<
  CreatorProgressRow,
  "posts_this_period" | "target_posts" | "target_period" | "expected_by_today" | "status" | "period_start" | "period_end"
>;

// "2 / 3 this week" with a bar; the tick marks how many were due by today.
export default function PeriodProgress({ progress }: { progress: Progress }) {
  const { posts_this_period: posts, target_posts: target, expected_by_today: due } = progress;
  const share = (n: number) => `${Math.min(100, (n / target) * 100)}%`;
  const range = `${formatDate(progress.period_start)} – ${formatDate(progress.period_end)}`;
  const behind = progress.status === "behind";

  return (
    <div className="w-full min-w-36 sm:w-44" title={range}>
      <div className="flex justify-between gap-2 text-[11px] text-ink-muted">
        <span>
          <span className="font-medium text-ink">{posts}</span> / {target} this {progress.target_period}
        </span>
        {behind && <span className="text-behind">{due} due by today</span>}
      </div>
      <div className="relative mt-2 h-[5px] rounded-full bg-brand-soft">
        <div
          className={`h-full rounded-full ${behind ? "bg-behind" : "bg-brand"}`}
          style={{ width: share(posts) }}
        />
        {behind && due > 0 && (
          <div className="absolute -top-[3px] h-[11px] w-px bg-ink-muted" style={{ left: share(due) }} aria-hidden="true" />
        )}
      </div>
    </div>
  );
}
