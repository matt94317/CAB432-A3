import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger" | "link";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand text-white hover:opacity-90 px-4 py-2.5",
  secondary: "border border-gray-300 bg-white text-gray-900 hover:bg-gray-50 px-4 py-2.5",
  danger: "bg-red-600 text-white hover:bg-red-700 px-4 py-2.5",
  link: "text-brand underline-offset-4 hover:underline",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export default function Button({
  variant = "primary",
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
      className={`rounded-lg text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
    >
      {loading ? "Please wait…" : children}
    </button>
  );
}
