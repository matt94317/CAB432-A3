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

  return (
    <div className="w-full min-w-36 sm:w-44" title={range}>
      <div className="flex justify-between text-xs text-gray-600">
        <span>
          <span className="font-medium text-gray-900">{posts}</span> / {target} this {progress.target_period}
        </span>
        {progress.status === "behind" && <span>{due} due by today</span>}
      </div>
      <div className="relative mt-1 h-1.5 rounded-full bg-gray-100">
        <div
          className={`h-full rounded-full ${progress.status === "behind" ? "bg-behind" : "bg-on-target"}`}
          style={{ width: share(posts) }}
        />
        {progress.status === "behind" && due > 0 && (
          <div className="absolute -top-0.5 h-2.5 w-px bg-gray-500" style={{ left: share(due) }} aria-hidden="true" />
        )}
      </div>
    </div>
  );
}
