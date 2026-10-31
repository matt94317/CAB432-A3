import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import { type ChatMessage, sendChat, type ToolUse } from "./api";

export interface SavedChat {
  id: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
  /** A change waiting for Confirm/Cancel, so a reopened chat can still answer it. */
  pending: ToolUse[] | null;
}

const MAX_CHATS = 20;

// Chats are kept in this browser per signed-in user, so they survive closing the panel,
// reloading and signing back in. Storage can be unavailable (private windows), so every
// access is guarded and the assistant still works without it.
const storageKey = (userId: string) => `hookd.assistant.${userId}`;

function load(userId: string): SavedChat[] {
  try {
    const raw = localStorage.getItem(storageKey(userId));
    const chats = raw ? (JSON.parse(raw) as SavedChat[]) : [];
    return Array.isArray(chats) ? chats : [];
  } catch {
    return [];
  }
}

function save(userId: string, chats: SavedChat[]) {
  try {
    localStorage.setItem(storageKey(userId), JSON.stringify(chats));
  } catch {
    // Full or blocked: history just isn't kept
  }
}

function titleOf(messages: ChatMessage[]): string {
  const first = messages.find((m) => m.role === "user")?.content.find((b) => "text" in b);
  const text = first && "text" in first ? first.text.trim() : "New chat";
  return text.length > 60 ? `${text.slice(0, 57)}…` : text;
}

// Conversation state for the assistant panel. Lives in the app shell so the chat
// survives page changes and closing the panel.
export function useAssistant(userId: string | null) {
  const queryClient = useQueryClient();
  const [chats, setChats] = useState<SavedChat[]>([]);
  const [chatId, setChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState<ToolUse[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load this user's chats and reopen the latest one
  useEffect(() => {
    const saved = userId ? load(userId) : [];
    setChats(saved);
    setChatId(saved[0]?.id ?? null);
    setMessages(saved[0]?.messages ?? []);
    setPending(saved[0]?.pending ?? null);
    setError(null);
  }, [userId]);

  const store = useCallback(
    (id: string, next: ChatMessage[], nextPending: ToolUse[] | null) => {
      setChats((current) => {
        const chat: SavedChat = {
          id,
          title: titleOf(next),
          updatedAt: new Date().toISOString(),
          messages: next,
          pending: nextPending,
        };
        const updated = [chat, ...current.filter((c) => c.id !== id)].slice(0, MAX_CHATS);
        if (userId) save(userId, updated);
        return updated;
      });
    },
    [userId],
  );

  const run = useCallback(
    async (id: string, next: ChatMessage[], decision?: "confirm" | "cancel") => {
      setBusy(true);
      setError(null);
      try {
        const reply = await sendChat(next, decision);
        setMessages(reply.messages);
        setPending(reply.pending);
        store(id, reply.messages, reply.pending);
        // The assistant changed data the open pages show
        if (reply.changed) void queryClient.invalidateQueries();
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : "The assistant failed. Try again.");
        return false;
      } finally {
        setBusy(false);
      }
    },
    [queryClient, store],
  );

  const ask = useCallback(
    async (text: string) => {
      const id = chatId ?? crypto.randomUUID();
      setChatId(id);
      const next: ChatMessage[] = [...messages, { role: "user", content: [{ text }] }];
      setMessages(next); // show the question while the answer loads
      const ok = await run(id, next);
      if (!ok) setMessages(messages); // so the next send doesn't repeat it
      return ok;
    },
    [chatId, messages, run],
  );

  const decide = useCallback(
    (decision: "confirm" | "cancel") => (chatId ? run(chatId, messages, decision) : Promise.resolve(false)),
    [chatId, messages, run],
  );

  const newChat = useCallback(() => {
    setChatId(null);
    setMessages([]);
    setPending(null);
    setError(null);
  }, []);

  const openChat = useCallback(
    (id: string) => {
      const chat = chats.find((c) => c.id === id);
      if (!chat) return;
      setChatId(chat.id);
      setMessages(chat.messages);
      setPending(chat.pending);
      setError(null);
    },
    [chats],
  );

  const deleteChat = useCallback(
    (id: string) => {
      setChats((current) => {
        const updated = current.filter((c) => c.id !== id);
        if (userId) save(userId, updated);
        return updated;
      });
      if (id === chatId) newChat();
    },
    [userId, chatId, newChat],
  );

  return { chats, chatId, messages, pending, busy, error, ask, decide, newChat, openChat, deleteChat };
}

export type Assistant = ReturnType<typeof useAssistant>;
