import type { ReactNode } from "react";

const TONES = {
  green: "bg-green-50 text-green-700 ring-green-600/20",
  blue: "bg-blue-50 text-blue-700 ring-blue-600/20",
  gray: "bg-gray-100 text-gray-600 ring-gray-500/20",
};

export default function Badge({ tone = "gray", children }: { tone?: keyof typeof TONES; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]}`}>
      {children}
    </span>
  );
}
