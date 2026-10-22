import type { ReactNode } from "react";
import Icon, { type IconName } from "./Icon";

// A headline number. "tile" stands alone (dashboard metrics); "inline" sits inside a
// shared summary card with an icon chip (campaign and creator overviews).
export default function StatCard({
  label,
  value,
  note,
  icon,
  variant = "tile",
  title,
}: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  icon?: IconName;
  variant?: "tile" | "inline";
  title?: string;
}) {
  if (variant === "inline") {
    return (
      <div className="flex min-w-0 flex-1 gap-3.5" title={title}>
        {icon && (
          <span className="flex size-9 shrink-0 items-center justify-center rounded-[10px] bg-brand-soft text-brand">
            <Icon name={icon} className="size-[18px]" />
          </span>
        )}
        <div className="min-w-0">
          <p className="text-[11px] text-ink-muted">{label}</p>
          <p className="mt-1 text-[25px] leading-tight tabular-nums text-ink">{value}</p>
          {note && <p className="mt-1 text-[10px] text-ink-muted">{note}</p>}
        </div>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-3.5 rounded-card border border-line bg-surface p-5" title={title}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs text-ink-muted">{label}</p>
        {icon && <Icon name={icon} className="size-4 text-ink-muted" />}
      </div>
      <p className="text-[29px] leading-[1.15] tabular-nums text-ink">{value}</p>
      {note && <p className="text-[11px] text-ink-muted">{note}</p>}
    </div>
  );
}
