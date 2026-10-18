import type { ReactNode } from "react";

// Page title, one-line description and the page's main actions.
export default function PageHeader({
  title,
  description,
  actions,
  children,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  /** Extra lines under the description, e.g. hashtags. */
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-[29px] leading-tight text-ink">{title}</h1>
        {description && <div className="mt-1.5 text-[13px] text-ink-muted">{description}</div>}
        {children}
      </div>
      {actions && <div className="flex flex-wrap gap-2.5">{actions}</div>}
    </div>
  );
}
