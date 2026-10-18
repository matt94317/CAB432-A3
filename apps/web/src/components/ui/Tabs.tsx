// Underlined tabs with counts ("All campaigns  6").
export default function Tabs<T extends string>({
  tabs,
  value,
  onChange,
  label,
}: {
  tabs: { value: T; label: string; count?: number }[];
  value: T;
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div className="flex gap-7 overflow-x-auto border-b border-line" role="tablist" aria-label={label}>
      {tabs.map((tab) => {
        const selected = tab.value === value;
        return (
          <button
            key={tab.value}
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(tab.value)}
            className={`-mb-px flex h-[46px] shrink-0 items-center gap-2 border-b-2 text-[13px] ${
              selected ? "border-brand font-semibold text-brand" : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {tab.label}
            {tab.count !== undefined && <span>{tab.count}</span>}
          </button>
        );
      })}
    </div>
  );
}
