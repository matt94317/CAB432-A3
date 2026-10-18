// Initials avatar: people in Hookd have no photos yet, so this stands in for the
// round photos in the design.
const SIZES = {
  sm: "size-[27px] text-[10px]",
  md: "size-[34px] text-xs",
  lg: "size-[72px] text-xl",
};

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const letters = parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : (parts[0] ?? "?").slice(0, 2);
  return letters.toUpperCase();
}

export default function Avatar({ name, size = "md" }: { name: string; size?: keyof typeof SIZES }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-brand-soft font-semibold text-brand ${SIZES[size]}`}
    >
      {initials(name)}
    </span>
  );
}
