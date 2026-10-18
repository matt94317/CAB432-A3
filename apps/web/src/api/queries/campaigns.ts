import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../client";
import { unwrap } from "../errors";
import type { components } from "../schema";

// TanStack Query hooks for campaigns (US-03 to US-06).

export type Campaign = components["schemas"]["CampaignRead"];
export type CampaignListItem = components["schemas"]["CampaignListItem"];
export type CampaignCreate = components["schemas"]["CampaignCreate"];
export type CampaignUpdate = components["schemas"]["CampaignUpdate"];
export type CampaignStatusFilter = components["schemas"]["StatusFilter"];

const keys = {
  all: ["campaigns"] as const,
  list: (status: CampaignStatusFilter) => ["campaigns", "list", status] as const,
  detail: (id: string) => ["campaigns", "detail", id] as const,
};

const path = (campaignId: string) => ({ params: { path: { campaign_id: campaignId } } });

export function useCampaigns(status: CampaignStatusFilter = "active") {
  return useQuery({
    queryKey: keys.list(status),
    queryFn: () => unwrap(api.GET("/api/campaigns", { params: { query: { status } } })),
  });
}

export function useCampaign(campaignId: string) {
  return useQuery({
    queryKey: keys.detail(campaignId),
    queryFn: () => unwrap(api.GET("/api/campaigns/{campaign_id}", path(campaignId))),
  });
}

// Every change can move a campaign between lists, so refresh them all
function useCampaignMutation<TVariables, TData>(mutationFn: (variables: TVariables) => Promise<TData>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useCreateCampaign() {
  return useCampaignMutation((body: CampaignCreate) => unwrap(api.POST("/api/campaigns", { body })));
}

export function useUpdateCampaign() {
  return useCampaignMutation(({ id, changes }: { id: string; changes: CampaignUpdate }) =>
    unwrap(api.PATCH("/api/campaigns/{campaign_id}", { ...path(id), body: changes })),
  );
}

export function useArchiveCampaign() {
  return useCampaignMutation((id: string) =>
    unwrap(api.POST("/api/campaigns/{campaign_id}/archive", path(id))),
  );
}

export function useRestoreCampaign() {
  return useCampaignMutation((id: string) =>
    unwrap(api.POST("/api/campaigns/{campaign_id}/restore", path(id))),
  );
}

export function useDeleteCampaign() {
  return useCampaignMutation((id: string) =>
    unwrap(api.DELETE("/api/campaigns/{campaign_id}", path(id))),
  );
}
