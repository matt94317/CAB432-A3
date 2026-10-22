import { type InputHTMLAttributes, type ReactNode, useId } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  /** "lg" is the taller field used on the sign-in pages. */
  fieldSize?: "md" | "lg";
  /** Rendered inside the field on the right, e.g. a show-password button. */
  trailing?: ReactNode;
}

export const fieldClasses =
  "w-full rounded-lg border border-line bg-surface px-[15px] text-sm text-ink outline-none placeholder:text-ink-subtle focus:border-brand focus:ring-2 focus:ring-brand/20";

export default function TextField({
  label,
  hint,
  fieldSize = "md",
  trailing,
  id,
  className = "",
  ...props
}: TextFieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const hintId = hint ? `${inputId}-hint` : undefined;

  return (
    <div className={`flex flex-col gap-[9px] ${className}`}>
      <label htmlFor={inputId} className="text-[13px] text-ink">
        {label}
      </label>
      <div className="relative">
        <input
          {...props}
          id={inputId}
          aria-describedby={hintId}
          className={`${fieldClasses} ${fieldSize === "lg" ? "h-[50px]" : "h-11"} ${trailing ? "pr-11" : ""}`}
        />
        {trailing && <div className="absolute inset-y-0 right-0 flex items-center pr-3">{trailing}</div>}
      </div>
      {hint && (
        <p id={hintId} className="text-xs text-ink-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
