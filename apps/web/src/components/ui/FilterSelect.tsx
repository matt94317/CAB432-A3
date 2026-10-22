import Icon from "./Icon";

// The design's filter pill ("All campaigns ⌄"), as a native select.
export default function FilterSelect<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <label className="relative inline-flex h-[39px] max-w-full items-center rounded-lg border border-line bg-surface text-xs text-ink-muted focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="h-full max-w-full cursor-pointer appearance-none truncate bg-transparent pl-3 pr-8 outline-none"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <Icon name="chevron-down" className="pointer-events-none absolute right-3 size-[13px]" />
    </label>
  );
}
