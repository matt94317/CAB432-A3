// "Showing 1–10 of 64 posts" with Previous / page numbers / Next, as in the design.
export default function Pagination({
  page,
  pageSize,
  total,
  noun,
  onPage,
}: {
  page: number;
  pageSize: number;
  total: number;
  noun: string;
  onPage: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(total, page * pageSize);
  // 1 … around the current page … last
  const shown = [...new Set([1, page - 1, page, page + 1, pages])].filter((p) => p >= 1 && p <= pages).sort((a, b) => a - b);
  const button = "flex h-9 min-w-9 items-center justify-center rounded-lg px-[13px] text-xs font-semibold";

  return (
    <nav aria-label="Pages" className="flex flex-wrap items-center justify-between gap-3 p-[18px]">
      <p className="text-xs text-ink-muted">
        Showing {first}–{last} of {total} {noun}
      </p>
      {pages > 1 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => onPage(page - 1)}
            disabled={page === 1}
            className={`${button} border border-line bg-surface text-ink disabled:opacity-50`}
          >
            Previous
          </button>
          {shown.map((p, i) => (
            <span key={p} className="flex gap-1.5">
              {i > 0 && p - shown[i - 1] > 1 && <span className={`${button} text-ink`}>…</span>}
              <button
                type="button"
                onClick={() => onPage(p)}
                aria-current={p === page ? "page" : undefined}
                className={`${button} ${p === page ? "bg-brand-soft text-brand" : "text-ink hover:bg-canvas"}`}
              >
                {p}
              </button>
            </span>
          ))}
          <button
            type="button"
            onClick={() => onPage(page + 1)}
            disabled={page === pages}
            className={`${button} border border-line bg-surface text-ink disabled:opacity-50`}
          >
            Next
          </button>
        </div>
      )}
    </nav>
  );
}
