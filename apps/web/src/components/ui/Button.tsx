import type { ButtonHTMLAttributes } from "react";
import Icon, { type IconName } from "./Icon";

type Variant = "primary" | "secondary" | "soft" | "danger" | "link";
type Size = "md" | "sm";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand text-white hover:bg-brand/90",
  secondary: "border border-line bg-surface text-ink hover:bg-canvas",
  soft: "bg-brand-soft text-brand hover:bg-brand-muted/60",
  danger: "bg-danger text-white hover:bg-danger/90",
  link: "text-brand underline-offset-4 hover:underline",
};

const SIZES: Record<Size, string> = {
  md: "h-11 px-[18px] text-[13px]",
  sm: "h-9 px-[13px] text-xs",
};

// Also used to style links that look like buttons
export function buttonClass(variant: Variant = "primary", size: Size = "md"): string {
  const shape = variant === "link" ? "text-[13px]" : `inline-flex items-center justify-center gap-2 rounded-lg ${SIZES[size]}`;
  return `font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${shape} ${VARIANTS[variant]}`;
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  icon?: IconName;
  loading?: boolean;
}

export default function Button({
  variant = "primary",
  size = "md",
  icon,
  loading = false,
  disabled,
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      aria-busy={loading}
      className={`${buttonClass(variant, size)} ${className}`}
    >
      {icon && !loading && <Icon name={icon} />}
      {loading ? "Please wait…" : children}
    </button>
  );
}
