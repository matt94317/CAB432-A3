import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../client";
import { unwrap } from "../errors";
import type { components } from "../schema";

// TanStack Query hooks for the creator roster (US-07, US-08).

export type Creator = components["schemas"]["CreatorRead"];
export type CreatorCreate = components["schemas"]["CreatorCreate"];
export type CreatorUpdate = components["schemas"]["CreatorUpdate"];
export type CreatorCampaign = components["schemas"]["CreatorCampaign"];

export const creatorKeys = {
  all: ["creators"] as const,
  list: ["creators", "list"] as const,
  detail: (id: string) => ["creators", "detail", id] as const,
  campaigns: (id: string) => ["creators", "campaigns", id] as const,
};

const path = (creatorId: string) => ({ params: { path: { creator_id: creatorId } } });

// The whole roster; pages filter it locally so search is instant
export function useCreators() {
  return useQuery({
    queryKey: creatorKeys.list,
    queryFn: () => unwrap(api.GET("/api/creators")),
  });
}

export function useCreator(creatorId: string) {
  return useQuery({
    queryKey: creatorKeys.detail(creatorId),
    queryFn: () => unwrap(api.GET("/api/creators/{creator_id}", path(creatorId))),
  });
}

export function useCreatorCampaigns(creatorId: string) {
  return useQuery({
    queryKey: creatorKeys.campaigns(creatorId),
    queryFn: () => unwrap(api.GET("/api/creators/{creator_id}/campaigns", path(creatorId))),
  });
}

// Creator names and handles also show on campaign pages, and removing a creator
// changes campaign progress, so refresh those too. The refresh isn't awaited: after a
// delete, the creator's own page navigates away instead of refetching a 404 first.
function useCreatorMutation<TVariables, TData>(mutationFn: (variables: TVariables) => Promise<TData>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      for (const queryKey of [creatorKeys.all, ["assignments"], ["campaigns"]]) {
        void queryClient.invalidateQueries({ queryKey });
      }
    },
  });
}

export function useCreateCreator() {
  return useCreatorMutation((body: CreatorCreate) => unwrap(api.POST("/api/creators", { body })));
}

export function useUpdateCreator() {
  return useCreatorMutation(({ id, changes }: { id: string; changes: CreatorUpdate }) =>
    unwrap(api.PATCH("/api/creators/{creator_id}", { ...path(id), body: changes })),
  );
}

export function useDeleteCreator() {
  return useCreatorMutation((id: string) => unwrap(api.DELETE("/api/creators/{creator_id}", path(id))));
}
