import type { Campaign } from "@/api/queries/campaigns";
import Badge from "@/components/ui/Badge";

// Archived wins; otherwise show where the campaign is in its date range.
export default function CampaignStatusBadge({ campaign }: { campaign: Pick<Campaign, "status" | "phase"> }) {
  if (campaign.status === "archived") return <Badge>Archived</Badge>;
  if (campaign.phase === "live") return <Badge tone="success">Live</Badge>;
  if (campaign.phase === "upcoming") return <Badge tone="brand">Upcoming</Badge>;
  return <Badge>Ended</Badge>;
}
