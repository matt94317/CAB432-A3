import type { ProgressStatus } from "@/api/queries/dashboard";
import Badge from "@/components/ui/Badge";

// Status always comes with an icon and a word, never colour alone.
const STATUS: Record<ProgressStatus, { tone: "green" | "blue" | "gray" | "red"; icon: string; label: string }> = {
  behind: { tone: "red", icon: "!", label: "Behind" },
  on_track: { tone: "blue", icon: "→", label: "On track" },
  met: { tone: "green", icon: "✓", label: "Target met" },
  upcoming: { tone: "gray", icon: "·", label: "Not started" },
};

export default function ProgressStatusBadge({ status }: { status: ProgressStatus }) {
  const { tone, icon, label } = STATUS[status];
  return (
    <Badge tone={tone}>
      <span aria-hidden="true" className="mr-1">
        {icon}
      </span>
      {label}
    </Badge>
  );
}
