import { useQuery } from "@tanstack/react-query";
import { api } from "../client";
import { unwrap } from "../errors";
import type { components } from "../schema";

// TanStack Query hooks for dashboards (US-19 to US-22). Keys sit under "campaigns" and
// "creators", so every mutation that refreshes those also refreshes these.

export type CampaignDashboard = components["schemas"]["CampaignDashboard"];
export type CreatorProgressRow = components["schemas"]["CreatorProgressRow"];
export type Metrics = components["schemas"]["Metrics"];
export type DailyMetrics = components["schemas"]["DailyMetrics"];
export type BehindTargetItem = components["schemas"]["BehindTargetItem"];
export type CreatorPerformance = components["schemas"]["CreatorPerformance"];
export type ProgressStatus = components["schemas"]["ProgressStatus"];

export function useCampaignDashboard(campaignId: string) {
  return useQuery({
    queryKey: ["campaigns", "dashboard", campaignId],
    queryFn: () =>
      unwrap(api.GET("/api/campaigns/{campaign_id}/dashboard", { params: { path: { campaign_id: campaignId } } })),
  });
}

export function useBehindTarget() {
  return useQuery({
    queryKey: ["campaigns", "behind-target"],
    queryFn: () => unwrap(api.GET("/api/behind-target")),
  });
}

export function useCreatorPerformance(creatorId: string) {
  return useQuery({
    queryKey: ["creators", "performance", creatorId],
    queryFn: () =>
      unwrap(api.GET("/api/creators/{creator_id}/performance", { params: { path: { creator_id: creatorId } } })),
  });
}
