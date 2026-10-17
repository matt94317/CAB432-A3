import { fetchAuthSession } from "aws-amplify/auth";
import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "./schema";

// Attaches the Cognito access token. fetchAuthSession refreshes it first if it has expired.
const authMiddleware: Middleware = {
  async onRequest({ request }) {
    const { tokens } = await fetchAuthSession();
    const accessToken = tokens?.accessToken?.toString();
    if (accessToken) request.headers.set("Authorization", `Bearer ${accessToken}`);
    return request;
  },
};

export const api = createClient<paths>({ baseUrl: import.meta.env.VITE_API_URL ?? "" });
api.use(authMiddleware);
