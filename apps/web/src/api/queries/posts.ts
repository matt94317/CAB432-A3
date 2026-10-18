import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../client";
import { unwrap } from "../errors";
import type { components } from "../schema";

// TanStack Query hooks for a campaign's posts and syncing (US-13 to US-18).

export type Post = components["schemas"]["PostRead"];
export type PostCreate = components["schemas"]["PostCreate"];
export type SyncRun = components["schemas"]["SyncRun"];

export const postKeys = {
  all: ["posts"] as const,
  campaign: (campaignId: string) => ["posts", campaignId] as const,
};

const campaignPath = (campaignId: string) => ({ params: { path: { campaign_id: campaignId } } });
const postPath = (postId: string) => ({ params: { path: { post_id: postId } } });

export function useCampaignPosts(campaignId: string) {
  return useQuery({
    queryKey: postKeys.campaign(campaignId),
    queryFn: () => unwrap(api.GET("/api/campaigns/{campaign_id}/posts", campaignPath(campaignId))),
  });
}

// Posts change campaign progress, dashboards and creator performance; syncing also
// updates creators' last-synced times
function usePostMutation<TVariables, TData>(mutationFn: (variables: TVariables) => Promise<TData>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () =>
      Promise.all(
        [postKeys.all, ["campaigns"], ["assignments"], ["creators"]].map((queryKey) =>
          queryClient.invalidateQueries({ queryKey }),
        ),
      ),
  });
}

export function useAddPost(campaignId: string) {
  return usePostMutation((body: PostCreate) =>
    unwrap(api.POST("/api/campaigns/{campaign_id}/posts", { ...campaignPath(campaignId), body })),
  );
}

export function useMovePost() {
  return usePostMutation(({ postId, campaignId }: { postId: string; campaignId: string }) =>
    unwrap(api.PATCH("/api/posts/{post_id}", { ...postPath(postId), body: { campaign_id: campaignId } })),
  );
}

export function useRemovePost() {
  return usePostMutation((postId: string) => unwrap(api.DELETE("/api/posts/{post_id}", postPath(postId))));
}

export function useSyncCampaign(campaignId: string) {
  return usePostMutation(() => unwrap(api.POST("/api/campaigns/{campaign_id}/sync", campaignPath(campaignId))));
}
