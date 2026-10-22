import type { ReactNode } from "react";

// Status pill with a dot, as in the design. Always carries a word, so meaning never
// depends on colour alone.
const TONES = {
  success: { pill: "bg-on-target-soft text-on-target", dot: "bg-on-target" },
  brand: { pill: "bg-brand-soft text-brand", dot: "bg-brand" },
  neutral: { pill: "bg-canvas text-ink-muted", dot: "bg-ink-subtle" },
  warning: { pill: "bg-behind-soft text-behind", dot: "bg-behind" },
};

export type BadgeTone = keyof typeof TONES;

export default function Badge({
  tone = "neutral",
  dot = true,
  children,
}: {
  tone?: BadgeTone;
  dot?: boolean;
  children: ReactNode;
}) {
  const { pill, dot: dotColour } = TONES[tone];
  return (
    <span className={`inline-flex items-center gap-[5px] whitespace-nowrap rounded-full px-[9px] py-1 text-[11px] leading-none ${pill}`}>
      {dot && <span aria-hidden="true" className={`size-[5px] rounded-full ${dotColour}`} />}
      {children}
    </span>
  );
}
