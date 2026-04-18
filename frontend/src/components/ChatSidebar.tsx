"use client";

import { FormEvent, useState } from "react";
import type { ChatMessage } from "@/lib/chat";

type ChatSidebarProps = {
  messages: ChatMessage[];
  isSending: boolean;
  errorMessage: string | null;
  onSend: (prompt: string) => Promise<void>;
};

export const ChatSidebar = ({
  messages,
  isSending,
  errorMessage,
  onSend,
}: ChatSidebarProps) => {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed || isSending) {
      return;
    }

    setPrompt("");
    await onSend(trimmed);
  };

  return (
    <aside className="h-fit rounded-[28px] border border-[var(--stroke)] bg-white/90 p-5 shadow-[var(--shadow)] backdrop-blur xl:sticky xl:top-6" aria-label="AI assistant sidebar">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            AI Assistant
          </p>
          <h2 className="mt-1 font-display text-xl font-semibold text-[var(--navy-dark)]">
            Board Co-Pilot
          </h2>
        </div>
        <span className="rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--primary-blue)]">
          Part 10
        </span>
      </div>

      <div className="mt-4 h-[360px] overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3">
        {messages.length === 0 ? (
          <p className="rounded-xl border border-dashed border-[var(--stroke)] bg-white px-3 py-3 text-sm leading-6 text-[var(--gray-text)]">
            Ask me to create, edit, or move cards. I can return updates and apply
            them to your board automatically.
          </p>
        ) : (
          <ul className="space-y-3" aria-live="polite">
            {messages.map((message) => (
              <li
                key={message.id}
                className={
                  message.role === "user"
                    ? "ml-8 rounded-2xl bg-[var(--primary-blue)]/12 px-3 py-2 text-sm text-[var(--navy-dark)]"
                    : "mr-8 rounded-2xl bg-white px-3 py-2 text-sm text-[var(--navy-dark)] shadow-sm"
                }
              >
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--gray-text)]">
                  {message.role === "user" ? "You" : "Assistant"}
                </p>
                <p className="whitespace-pre-wrap leading-6">{message.content}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      {errorMessage ? (
        <div className="mt-3 rounded-xl border border-[#f2c0c0] bg-[#fff5f5] px-3 py-2 text-sm text-[#962626]">
          {errorMessage}
        </div>
      ) : null}

      <form className="mt-4" onSubmit={handleSubmit}>
        <label className="block text-xs font-semibold uppercase tracking-[0.14em] text-[var(--gray-text)]">
          Message
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Ask AI to update the board..."
            rows={4}
            className="mt-2 w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            disabled={isSending}
          />
        </label>

        <button
          type="submit"
          disabled={isSending || !prompt.trim()}
          className="mt-3 w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isSending ? "Sending..." : "Send to AI"}
        </button>
      </form>
    </aside>
  );
};
