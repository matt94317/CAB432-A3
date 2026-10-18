import { type SelectHTMLAttributes, useId } from "react";
import { fieldClasses } from "./TextField";

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: { value: string; label: string }[];
}

export default function SelectField({ label, options, id, className = "", ...props }: SelectFieldProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  return (
    <div className={`flex flex-col gap-[9px] ${className}`}>
      <label htmlFor={selectId} className="text-[13px] text-ink">
        {label}
      </label>
      <select {...props} id={selectId} className={`${fieldClasses} h-11`}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
