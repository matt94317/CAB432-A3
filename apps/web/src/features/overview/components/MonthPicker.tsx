import Icon from "@/components/ui/Icon";
import { monthRangeLabel, recentMonths } from "../months";

// The design's date range filter, as a native month select.
export default function MonthPicker({ value, onChange }: { value: string; onChange: (month: string) => void }) {
  return (
    <label className="relative inline-flex h-[39px] items-center rounded-lg border border-line bg-surface text-xs text-ink-muted focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20">
      <span className="sr-only">Month</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-full cursor-pointer appearance-none bg-transparent pl-3 pr-8 outline-none"
      >
        {recentMonths().map((month) => (
          <option key={month} value={month}>
            {monthRangeLabel(month)}
          </option>
        ))}
      </select>
      <Icon name="chevron-down" className="pointer-events-none absolute right-3 size-[13px]" />
    </label>
  );
}
