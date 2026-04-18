import type { ChatHistoryMessage, ChatRole } from "@/lib/api";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

let messageCounter = 0;

export const createChatMessage = (role: ChatRole, content: string): ChatMessage => {
  messageCounter += 1;
  return {
    id: `msg-${messageCounter}`,
    role,
    content,
  };
};

export const toChatHistory = (messages: ChatMessage[]): ChatHistoryMessage[] =>
  messages.map((message) => ({
    role: message.role,
    content: message.content,
  }));

export const appendChatExchange = (
  messages: ChatMessage[],
  prompt: string,
  assistant: string
): ChatMessage[] => [
  ...messages,
  createChatMessage("user", prompt),
  createChatMessage("assistant", assistant),
];
