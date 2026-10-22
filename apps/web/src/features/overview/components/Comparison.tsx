// "↗ 24.6%  vs. the same days last month". Up is green; down stays neutral, since a
// quieter week isn't an error. The arrow carries the direction either way.
export function percentChange(current: number, previous: number): number | null {
  return previous > 0 ? ((current - previous) / previous) * 100 : null;
}

export default function Comparison({
  current,
  previous,
  label,
  points = false,
}: {
  current: number;
  previous: number;
  label: string;
  /** Compare as percentage points (for rates) instead of a relative change. */
  points?: boolean;
}) {
  const change = points ? (current - previous) * 100 : percentChange(current, previous);
  if (change === null || (!points && previous === 0)) {
    return <span className="text-ink-muted">{current > 0 ? `New ${label}` : `Nothing yet ${label}`}</span>;
  }
  const up = change >= 0;
  const amount = `${Math.abs(change).toFixed(1)}${points ? " pts" : "%"}`;
  return (
    <span className="flex items-center gap-1.5">
      <span className={up ? "text-on-target" : "text-ink-muted"}>
        {up ? "↗" : "↘"} {amount}
      </span>
      <span className="text-ink-muted">{label}</span>
    </span>
  );
}
