import type { ReactNode } from "react";

const TONES = {
  error: "border-danger/20 bg-danger-soft text-danger",
  success: "border-on-target/20 bg-on-target-soft text-on-target",
};

export default function Alert({
  tone = "error",
  children,
}: {
  tone?: keyof typeof TONES;
  children: ReactNode;
}) {
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`rounded-lg border px-3 py-2.5 text-[13px] ${TONES[tone]}`}>
      {children}
    </div>
  );
}
