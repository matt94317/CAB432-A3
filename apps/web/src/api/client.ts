import createClient from "openapi-fetch";
import type { paths } from "./schema";

// Typed API client. TODO: add middleware that attaches the Cognito JWT.
export const api = createClient<paths>({ baseUrl: import.meta.env.VITE_API_URL ?? "" });
