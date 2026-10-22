import FilterSelect from "@/components/ui/FilterSelect";
import { monthRangeLabel, recentMonths } from "../months";

// The design's date range filter: one of the last 12 months.
export default function MonthPicker({ value, onChange }: { value: string; onChange: (month: string) => void }) {
  return (
    <FilterSelect
      label="Month"
      value={value}
      onChange={onChange}
      options={recentMonths().map((month) => ({ value: month, label: monthRangeLabel(month) }))}
    />
  );
}
