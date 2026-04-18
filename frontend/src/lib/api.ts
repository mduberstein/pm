import type { BoardData } from "@/lib/kanban";

export type ChatRole = "user" | "assistant";

export type ChatHistoryMessage = {
  role: ChatRole;
  content: string;
};

export type ChatResponse = {
  assistant: string;
  board: BoardData | null;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const parseJsonResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string" && payload.detail.trim()) {
        message = payload.detail;
      }
    } catch {
      // Ignore JSON parsing issues and fall back to default message.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
};

export const loginRequest = async (
  username: string,
  password: string
): Promise<LoginResponse> => {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  return parseJsonResponse<LoginResponse>(response);
};

export const fetchCurrentUser = async (
  token: string
): Promise<{ username: string }> => {
  const response = await fetch("/api/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return parseJsonResponse<{ username: string }>(response);
};

export const fetchBoard = async (token: string): Promise<BoardData> => {
  const response = await fetch("/api/board", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return parseJsonResponse<BoardData>(response);
};

export const updateBoard = async (
  token: string,
  board: BoardData
): Promise<BoardData> => {
  const response = await fetch("/api/board", {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(board),
  });

  return parseJsonResponse<BoardData>(response);
};

export const sendChatMessage = async (
  token: string,
  prompt: string,
  history: ChatHistoryMessage[]
): Promise<ChatResponse> => {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt, history }),
  });

  return parseJsonResponse<ChatResponse>(response);
};
