import { useQuery } from "@tanstack/react-query";
import { api } from "../client";
import { unwrap } from "../errors";
import type { components } from "../schema";

// The workspace overview. Keyed under "campaigns", so every change that refreshes
// campaigns (posts, assignments, creators, syncs) refreshes it too.

export type Overview = components["schemas"]["Overview"];
export type AttentionItem = components["schemas"]["AttentionItem"];

export function useOverview(month: string) {
  return useQuery({
    queryKey: ["campaigns", "overview", month],
    queryFn: () => unwrap(api.GET("/api/overview", { params: { query: { month } } })),
    placeholderData: (previous) => previous, // keep the page while switching months
  });
}
