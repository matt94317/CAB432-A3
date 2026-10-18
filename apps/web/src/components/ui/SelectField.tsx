import { type SelectHTMLAttributes, useId } from "react";

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: { value: string; label: string }[];
}

export default function SelectField({ label, options, id, className = "", ...props }: SelectFieldProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label htmlFor={selectId} className="text-sm font-medium text-gray-900">
        {label}
      </label>
      <select
        {...props}
        id={selectId}
        className="rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
