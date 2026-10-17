import type { ReactNode } from "react";

// Holds the signed-in user and session. TODO: wire up Cognito (US-01, US-02).
export function AuthProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
