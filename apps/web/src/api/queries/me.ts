import { useQuery } from "@tanstack/react-query";
import { api } from "../client";

// The signed-in manager. The first call after sign-up creates their account and organisation.
export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data, response } = await api.GET("/api/me");
      if (!data) throw new Error(`Couldn't load your profile (${response.status})`);
      return data;
    },
  });
}
