import { type ReactNode, useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { buttonClass } from "@/components/ui/Button";
import Icon, { type IconName } from "@/components/ui/Icon";

// Building blocks shared by the landing page sections.

// The design is 1440 wide with 80px gutters; content stops growing at 1280.
export function Container({ className = "", children }: { className?: string; children: ReactNode }) {
  return <div className={`mx-auto w-full max-w-[1440px] px-5 sm:px-10 xl:px-20 ${className}`}>{children}</div>;
}

export function Eyebrow({ className = "text-brand", children }: { className?: string; children: ReactNode }) {
  return <p className={`text-[11px] font-semibold leading-[1.45] ${className}`}>{children}</p>;
}

export function SectionHeading({ className = "", children }: { className?: string; children: ReactNode }) {
  return (
    <h2 className={`text-[32px] font-semibold leading-[1.14] text-ink sm:text-[43px] ${className}`}>{children}</h2>
  );
}

// A link styled as a button. `#section` targets stay on the page; anything else is an app route.
export function ActionLink({
  to,
  variant = "primary",
  icon,
  className = "",
  children,
}: {
  to: string;
  variant?: "primary" | "secondary";
  icon?: IconName;
  className?: string;
  children: ReactNode;
}) {
  const classes = `${buttonClass(variant)} ${className}`;
  const content = (
    <>
      {icon && <Icon name={icon} />}
      {children}
    </>
  );
  if (to.startsWith("#")) {
    return (
      <a href={to} className={classes}>
        {content}
      </a>
    );
  }
  return (
    <Link to={to} className={classes}>
      {content}
    </Link>
  );
}

// Overlapping round photos ("creator community").
export function AvatarStack({ photos, size, overlap }: { photos: string[]; size: string; overlap: string }) {
  return (
    <span className="flex">
      {photos.map((src, i) => (
        <img
          key={src}
          src={src}
          alt=""
          className={`${size} shrink-0 rounded-full object-cover ${i < photos.length - 1 ? overlap : ""}`}
        />
      ))}
    </span>
  );
}

// Lays out children at a fixed design size and scales them down to fit narrower screens.
export function ScaledCanvas({
  width,
  height,
  className = "",
  children,
}: {
  width: number;
  height: number;
  className?: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => setScale(Math.min(1, entry.contentRect.width / width)));
    observer.observe(el);
    return () => observer.disconnect();
  }, [width]);

  return (
    <div ref={ref} className={`w-full ${className}`} style={{ maxWidth: width, height: height * scale }}>
      <div className="relative origin-top-left" style={{ width, height, transform: `scale(${scale})` }}>
        {children}
      </div>
    </div>
  );
}
