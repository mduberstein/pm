import { afterAll, afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  fetchBoard,
  loginRequest,
  sendChatMessage,
  updateBoard,
} from "@/lib/api";
import { initialData } from "@/lib/kanban";

const mockedFetch = vi.fn<typeof fetch>();

const jsonResponse = (payload: unknown, status = 200) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });

vi.stubGlobal("fetch", mockedFetch);

afterEach(() => {
  mockedFetch.mockReset();
});

afterAll(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("logs in and returns bearer token payload", async () => {
    mockedFetch.mockResolvedValueOnce(
      jsonResponse({ access_token: "token-123", token_type: "bearer" })
    );

    const response = await loginRequest("user", "password");

    expect(response.access_token).toBe("token-123");
    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("fetches board data for authenticated user", async () => {
    mockedFetch.mockResolvedValueOnce(jsonResponse(initialData));

    const board = await fetchBoard("token-123");

    expect(board.columns).toHaveLength(5);
    expect(board.cards["card-1"].title).toBe("Align roadmap themes");
  });

  it("updates board and sends payload to backend", async () => {
    const updatedBoard = {
      columns: [
        {
          id: "col-backlog",
          title: "Backlog",
          cardIds: ["card-1"],
        },
      ],
      cards: {
        "card-1": {
          id: "card-1",
          title: "Updated title",
          details: "Updated details",
        },
      },
    };

    mockedFetch.mockResolvedValueOnce(jsonResponse(updatedBoard));

    const response = await updateBoard("token-123", updatedBoard);

    expect(response.cards["card-1"].title).toBe("Updated title");
    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/board",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify(updatedBoard),
      })
    );
  });

  it("sends chat request with prompt and history", async () => {
    mockedFetch.mockResolvedValueOnce(
      jsonResponse({ assistant: "Done.", board: null })
    );

    const response = await sendChatMessage("token-123", "Move card-1", [
      { role: "user", content: "Earlier prompt" },
      { role: "assistant", content: "Earlier answer" },
    ]);

    expect(response).toEqual({ assistant: "Done.", board: null });
    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          prompt: "Move card-1",
          history: [
            { role: "user", content: "Earlier prompt" },
            { role: "assistant", content: "Earlier answer" },
          ],
        }),
      })
    );
  });

  it("surfaces backend detail text from failed responses", async () => {
    mockedFetch.mockResolvedValueOnce(
      jsonResponse({ detail: "OpenRouter returned schema-invalid response." }, 502)
    );

    await expect(
      sendChatMessage("token-123", "Move card-1", [])
    ).rejects.toEqual(
      expect.objectContaining<ApiError>({
        status: 502,
        message: "OpenRouter returned schema-invalid response.",
      })
    );
  });
});
