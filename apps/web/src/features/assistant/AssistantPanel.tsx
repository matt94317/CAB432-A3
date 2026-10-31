import { type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import { formatRelative } from "@/lib/format";
import type { ChatMessage, ToolUse } from "./api";
import type { Assistant } from "./useAssistant";

const SUGGESTIONS = [
  "Who needs attention this period?",
  "How are my live campaigns doing?",
  "Which creator has the most views?",
];

const TOOL_LABELS: Record<string, string> = {
  list_campaigns: "Looked up campaigns",
  get_campaign_progress: "Checked campaign progress",
  list_behind_target_creators: "Checked who's behind target",
  list_creators: "Looked up creators",
  get_creator_performance: "Checked creator performance",
  update_creator_target: "Target change",
};

type Item = { kind: "user" | "assistant"; text: string } | { kind: "tool"; name: string };

// Questions, answers and the data each answer used. Tool results stay hidden.
function toItems(messages: ChatMessage[]): Item[] {
  return messages.flatMap((message) =>
    message.content.flatMap((block): Item[] => {
      if ("text" in block) return block.text.trim() ? [{ kind: message.role, text: block.text.trim() }] : [];
      if ("toolUse" in block) return [{ kind: "tool", name: block.toolUse.name }];
      return [];
    }),
  );
}

function describeChange(use: ToolUse): string {
  const { target_posts: posts, target_period: period } = use.input as {
    target_posts?: number;
    target_period?: string;
  };
  if (posts && period) return `${posts} posts per ${period}`;
  if (posts) return `${posts} posts per period`;
  return period ? `a ${period}ly target` : "a new target";
}

interface AssistantPanelProps {
  assistant: Assistant;
  onClose: () => void;
}

// The assistant never covers the page on big screens: from xl it docks as a column on the
// right (AppLayout pads the page to make room); from sm it floats as a chat window in the
// bottom-right corner; on phones it's full screen. Answers come from the chat model using
// the same MCP tools an external AI assistant gets; changes wait for the user to confirm.
// Past chats are listed under History.
export default function AssistantPanel({ assistant, onClose }: AssistantPanelProps) {
  const { chats, chatId, messages, pending, busy, error, ask, decide, newChat, openChat, deleteChat } =
    assistant;
  const [view, setView] = useState<"chat" | "history">("chat");
  const [draft, setDraft] = useState("");
  const panelRef = useRef<HTMLElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const items = toItems(messages);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [items.length, busy, pending, chatId, view]);

  // Escape closes the panel only while it has focus, so it doesn't also close with a
  // dialog opened from the page beside it
  useEffect(() => {
    const onKeyDown = (event: globalThis.KeyboardEvent) =>
      event.key === "Escape" && panelRef.current?.contains(document.activeElement) && onClose();
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy || pending) return;
    setDraft("");
    if (!(await ask(question))) setDraft(question);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send(draft);
    }
  }

  return (
    <aside
      ref={panelRef}
      aria-label="Hookd assistant"
      className="fixed inset-0 z-50 flex flex-col bg-surface sm:inset-auto sm:right-6 sm:bottom-6 sm:z-40 sm:h-[min(640px,calc(100dvh_-_3rem))] sm:w-[400px] sm:overflow-hidden sm:rounded-card sm:border sm:border-line sm:shadow-2xl xl:top-0 xl:right-0 xl:bottom-0 xl:z-30 xl:h-auto xl:rounded-none xl:border-y-0 xl:border-r-0 xl:shadow-none"
    >
      <header className="flex h-16 shrink-0 items-center gap-2 border-b border-line px-4 xl:h-[76px]">
        <span className="flex size-8 items-center justify-center rounded-lg bg-brand-soft text-brand">
          <Icon name="sparkles" />
        </span>
        <div className="mr-auto">
          <h2 className="text-sm font-semibold text-ink">Ask Hookd</h2>
          <p className="text-[11px] text-ink-muted">Answers from your live campaign data</p>
        </div>
        {chats.length > 0 && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setView(view === "history" ? "chat" : "history")}
            disabled={busy}
            aria-pressed={view === "history"}
          >
            {view === "history" ? "Back" : "History"}
          </Button>
        )}
        {(messages.length > 0 || view === "history") && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              newChat();
              setView("chat");
            }}
            disabled={busy}
          >
            New chat
          </Button>
        )}
        <button
          type="button"
          aria-label="Close assistant"
          onClick={onClose}
          className="flex size-9 items-center justify-center rounded-lg text-ink-muted hover:bg-canvas hover:text-ink"
        >
          <Icon name="close" />
        </button>
      </header>

      {view === "history" && (
        <ul className="flex-1 divide-y divide-line overflow-y-auto" aria-label="Past chats">
          {chats.map((chat) => (
            <li key={chat.id} className={`flex items-center gap-2 px-4 ${chat.id === chatId ? "bg-brand-soft" : ""}`}>
              <button
                type="button"
                onClick={() => {
                  openChat(chat.id);
                  setView("chat");
                }}
                className="min-w-0 flex-1 py-3 text-left"
              >
                <span className="block truncate text-[13px] font-medium text-ink">{chat.title}</span>
                <span className="block text-[11px] text-ink-muted">
                  {formatRelative(chat.updatedAt)}
                  {chat.pending && " · change waiting for you"}
                </span>
              </button>
              <button
                type="button"
                aria-label={`Delete chat: ${chat.title}`}
                onClick={() => deleteChat(chat.id)}
                className="flex size-8 shrink-0 items-center justify-center rounded-lg text-ink-muted hover:bg-canvas hover:text-danger"
              >
                <Icon name="close" className="size-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {view === "chat" && (
        <>
          <div className="flex-1 space-y-3 overflow-y-auto px-4 py-5" aria-live="polite">
            {items.length === 0 && (
              <div className="space-y-3">
                <p className="text-[13px] text-ink-muted">
                  Ask about progress, performance or who needs a nudge. You can also change a
                  creator's target; I'll ask you to confirm first.
                </p>
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => void send(suggestion)}
                    disabled={busy}
                    className="block w-full rounded-lg border border-line px-3 py-2.5 text-left text-[13px] text-ink hover:border-brand hover:bg-brand-soft"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}

            {items.map((item, i) =>
              item.kind === "tool" ? (
                <p key={i} className="flex items-center gap-1.5 text-[11px] text-ink-muted">
                  <Icon name="check" className="size-3" />
                  {TOOL_LABELS[item.name] ?? item.name}
                </p>
              ) : (
                <p
                  key={i}
                  className={`max-w-[88%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
                    item.kind === "user" ? "ml-auto bg-brand text-white" : "bg-canvas text-ink"
                  }`}
                >
                  {item.text}
                </p>
              ),
            )}

            {pending && (
              <div className="rounded-card border border-brand-muted bg-brand-soft p-4">
                <p className="text-[13px] font-semibold text-ink">Confirm this change</p>
                <ul className="mt-1 text-[13px] text-ink">
                  {pending.map((use) => (
                    <li key={use.toolUseId}>
                      {TOOL_LABELS[use.name] ?? use.name}: {describeChange(use)}
                    </li>
                  ))}
                </ul>
                <div className="mt-3 flex gap-2">
                  <Button size="sm" onClick={() => void decide("confirm")} loading={busy}>
                    Confirm
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => void decide("cancel")} disabled={busy}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {busy && !pending && <p className="text-[13px] text-ink-muted">Thinking…</p>}
            {error && (
              <p role="alert" className="text-[13px] text-danger">
                {error}
              </p>
            )}
            <div ref={endRef} />
          </div>

          <form onSubmit={onSubmit} className="flex items-end gap-2 border-t border-line p-3">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={onKeyDown}
              rows={2}
              maxLength={2000}
              placeholder={pending ? "Confirm or cancel the change first" : "Ask about your campaigns…"}
              disabled={Boolean(pending)}
              aria-label="Message"
              className="min-h-11 flex-1 resize-none rounded-lg border border-line bg-surface px-3 py-2.5 text-[13px] text-ink outline-none placeholder:text-ink-subtle focus:border-brand"
            />
            <button
              type="submit"
              aria-label="Send"
              disabled={busy || Boolean(pending) || !draft.trim()}
              className="flex size-11 items-center justify-center rounded-lg bg-brand text-white hover:bg-brand/90 disabled:opacity-50"
            >
              <Icon name="send" />
            </button>
          </form>
        </>
      )}
    </aside>
  );
}
