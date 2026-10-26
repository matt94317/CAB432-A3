// Round photo, or initials when there's none (Hookd stores no photos; demo builds
// pass stock ones, see lib/demoImages).
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

interface AvatarProps {
  name: string;
  size?: keyof typeof SIZES;
  src?: string;
  className?: string;
}

export default function Avatar({ name, size = "md", src, className = "" }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt=""
        aria-hidden="true"
        loading="lazy"
        className={`shrink-0 rounded-full object-cover ${SIZES[size]} ${className}`}
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-brand-soft font-semibold text-brand ${SIZES[size]} ${className}`}
    >
      {initials(name)}
    </span>
  );
}
