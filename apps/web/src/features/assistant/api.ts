import { fetchAuthSession } from "aws-amplify/auth";
import { ApiError } from "@/api/errors";

// The in-app assistant runs in the MCP service (POST /mcp/chat). It keeps no state:
// we send the whole conversation in Bedrock's message format and get it back with the
// new turns appended.

export interface ToolUse {
  toolUseId: string;
  name: string;
  input: Record<string, unknown>;
}

export type ContentBlock =
  | { text: string }
  | { toolUse: ToolUse }
  | { toolResult: { toolUseId: string; status?: "error"; content: { text: string }[] } };

export interface ChatMessage {
  role: "user" | "assistant";
  content: ContentBlock[];
}

export interface ChatReply {
  messages: ChatMessage[];
  /** Changes the model wants to make; they only run after the user confirms. */
  pending: ToolUse[] | null;
  /** A change was made, so cached app data is stale. */
  changed: boolean;
}

export async function sendChat(
  messages: ChatMessage[],
  decision?: "confirm" | "cancel",
): Promise<ChatReply> {
  const { tokens } = await fetchAuthSession();
  const response = await fetch(`${import.meta.env.VITE_API_URL ?? ""}/mcp/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${tokens?.accessToken?.toString() ?? ""}`,
    },
    body: JSON.stringify({ messages, decision }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = typeof body?.detail === "string" ? body.detail : null;
    throw new ApiError(detail ?? `The assistant failed (${response.status}). Try again.`, response.status);
  }
  return (await response.json()) as ChatReply;
}
