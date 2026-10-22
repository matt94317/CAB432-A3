import { useQueryClient } from "@tanstack/react-query";
import { type AuthUser, getCurrentUser, signOut as amplifySignOut } from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";

// Holds the signed-in Cognito user and keeps it in sync with Amplify's auth events.

type AuthState =
  | { status: "loading"; user: null }
  | { status: "signedIn"; user: AuthUser }
  | { status: "signedOut"; user: null };

interface AuthContextValue {
  status: AuthState["status"];
  user: AuthUser | null;
  /** Re-read the session, e.g. right after signing in. */
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const SIGNED_OUT: AuthState = { status: "signedOut", user: null };

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<AuthState>({ status: "loading", user: null });

  const refresh = useCallback(async () => {
    try {
      setState({ status: "signedIn", user: await getCurrentUser() });
    } catch {
      setState(SIGNED_OUT);
    }
  }, []);

  const clearSession = useCallback(() => {
    // Drop cached API data so the next person on this browser never sees it
    queryClient.clear();
    setState(SIGNED_OUT);
  }, [queryClient]);

  useEffect(() => {
    void refresh();
    return Hub.listen("auth", ({ payload }) => {
      switch (payload.event) {
        case "signedIn":
          void refresh();
          break;
        case "signedOut":
          clearSession();
          break;
        case "tokenRefresh_failure":
          // Refresh token expired or revoked: end the session locally too
          void amplifySignOut().finally(clearSession);
          break;
      }
    });
  }, [refresh, clearSession]);

  const signOut = useCallback(async () => {
    // Revokes this device's refresh token in Cognito and clears stored tokens
    await amplifySignOut();
    clearSession();
  }, [clearSession]);

  return (
    <AuthContext.Provider value={{ ...state, refresh, signOut }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
