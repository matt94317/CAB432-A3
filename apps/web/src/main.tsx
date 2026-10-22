import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./auth/AuthProvider";
import { authConfigured, configureAuth } from "./auth/cognito";
import "./index.css";

configureAuth();

const queryClient = new QueryClient();

function MissingAuthConfig() {
  return (
    <p className="p-6 text-sm">
      Cognito is not configured. Copy <code>apps/web/.env.example</code> to{" "}
      <code>apps/web/.env</code> and set the user pool and app client IDs.
    </p>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {authConfigured ? (
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    ) : (
      <MissingAuthConfig />
    )}
  </StrictMode>,
);
