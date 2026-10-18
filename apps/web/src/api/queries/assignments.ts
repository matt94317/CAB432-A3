import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../client";
import { unwrap } from "../errors";
import type { components } from "../schema";

// TanStack Query hooks for creators on a campaign and their targets (US-09 to US-12).

export type Assignment = components["schemas"]["AssignmentRead"];
export type AssignmentCreate = components["schemas"]["AssignmentCreate"];
export type AssignmentUpdate = components["schemas"]["AssignmentUpdate"];
export type TargetPeriod = components["schemas"]["TargetPeriod"];

export const assignmentKeys = {
  all: ["assignments"] as const,
  campaign: (campaignId: string) => ["assignments", campaignId] as const,
};

const campaignPath = (campaignId: string) => ({ params: { path: { campaign_id: campaignId } } });
const creatorPath = (campaignId: string, creatorId: string) => ({
  params: { path: { campaign_id: campaignId, creator_id: creatorId } },
});

export function useAssignments(campaignId: string) {
  return useQuery({
    queryKey: assignmentKeys.campaign(campaignId),
    queryFn: () => unwrap(api.GET("/api/campaigns/{campaign_id}/creators", campaignPath(campaignId))),
  });
}

// Assignments change campaign progress and each creator's campaign count
function useAssignmentMutation<TVariables, TData>(mutationFn: (variables: TVariables) => Promise<TData>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () =>
      Promise.all(
        [assignmentKeys.all, ["campaigns"], ["creators"]].map((queryKey) =>
          queryClient.invalidateQueries({ queryKey }),
        ),
      ),
  });
}

export function useAssignCreators(campaignId: string) {
  return useAssignmentMutation((body: AssignmentCreate) =>
    unwrap(api.POST("/api/campaigns/{campaign_id}/creators", { ...campaignPath(campaignId), body })),
  );
}

export function useUpdateTarget(campaignId: string) {
  return useAssignmentMutation(({ creatorId, changes }: { creatorId: string; changes: AssignmentUpdate }) =>
    unwrap(
      api.PATCH("/api/campaigns/{campaign_id}/creators/{creator_id}", {
        ...creatorPath(campaignId, creatorId),
        body: changes,
      }),
    ),
  );
}

export function useUnassignCreator(campaignId: string) {
  return useAssignmentMutation((creatorId: string) =>
    unwrap(api.DELETE("/api/campaigns/{campaign_id}/creators/{creator_id}", creatorPath(campaignId, creatorId))),
  );
}
