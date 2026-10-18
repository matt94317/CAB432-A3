import type { TargetPeriod } from "@/api/queries/assignments";

export const TARGET_PERIODS: { value: TargetPeriod; label: string }[] = [
  { value: "week", label: "per week" },
  { value: "month", label: "per month" },
];

export const MAX_TARGET_POSTS = 100;

/** "3 posts / week", "1 post / month" */
export function formatTarget(posts: number, period: TargetPeriod): string {
  return `${posts} ${posts === 1 ? "post" : "posts"} / ${period}`;
}
