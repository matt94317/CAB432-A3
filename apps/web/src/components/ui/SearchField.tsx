import Icon from "./Icon";

export default function SearchField({
  value,
  onChange,
  placeholder,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  label: string;
}) {
  return (
    <label className="flex h-[39px] w-full items-center gap-[9px] rounded-lg border border-line bg-surface px-3 focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20 sm:w-[270px]">
      <Icon name="search" className="size-[15px] text-ink-muted" />
      <span className="sr-only">{label}</span>
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="min-w-0 flex-1 bg-transparent text-xs text-ink outline-none placeholder:text-ink-subtle"
      />
    </label>
  );
}
