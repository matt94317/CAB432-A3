import type { ProgressStatus } from "@/api/queries/dashboard";
import Badge, { type BadgeTone } from "@/components/ui/Badge";

// Status always comes with a word, never colour alone.
const STATUS: Record<ProgressStatus, { tone: BadgeTone; label: string }> = {
  behind: { tone: "warning", label: "Behind" },
  on_track: { tone: "brand", label: "On track" },
  met: { tone: "success", label: "Target met" },
  upcoming: { tone: "neutral", label: "Not started" },
};

export default function ProgressStatusBadge({ status }: { status: ProgressStatus }) {
  const { tone, label } = STATUS[status];
  return <Badge tone={tone}>{label}</Badge>;
}
