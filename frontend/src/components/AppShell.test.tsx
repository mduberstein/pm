import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";
import { AppShell } from "@/components/AppShell";
import { initialData } from "@/lib/kanban";

const mockedFetch = vi.fn<
  (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
>();

const jsonResponse = (payload: unknown, status = 200) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });

vi.stubGlobal("fetch", mockedFetch);

const getUrl = (input: RequestInfo | URL) =>
  typeof input === "string"
    ? input
    : input instanceof URL
      ? input.toString()
      : input.url;

describe("AppShell", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedFetch.mockReset();
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });

  it("shows sign in when no auth token exists", async () => {
    render(<AppShell />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Sign in to Kanban Studio" })
      ).toBeInTheDocument();
    });
  });

  it("loads board data for authenticated session", async () => {
    window.localStorage.setItem("pm_auth_token", "token-123");

    mockedFetch.mockImplementation((input, init) => {
      const url = getUrl(input);
      const method = init?.method ?? "GET";

      if (url === "/api/auth/me") {
        return Promise.resolve(jsonResponse({ username: "user" }));
      }

      if (url === "/api/board" && method === "GET") {
        return Promise.resolve(jsonResponse(initialData));
      }

      if (url === "/api/board" && method === "PUT") {
        return Promise.resolve(jsonResponse(JSON.parse(String(init?.body ?? "{}"))));
      }

      return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
    });

    render(<AppShell />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    });
  });

  it("syncs board changes to backend", async () => {
    window.localStorage.setItem("pm_auth_token", "token-123");

    mockedFetch.mockImplementation((input, init) => {
      const url = getUrl(input);
      const method = init?.method ?? "GET";

      if (url === "/api/auth/me") {
        return Promise.resolve(jsonResponse({ username: "user" }));
      }

      if (url === "/api/board" && method === "GET") {
        return Promise.resolve(jsonResponse(initialData));
      }

      if (url === "/api/board" && method === "PUT") {
        return Promise.resolve(jsonResponse(JSON.parse(String(init?.body ?? "{}"))));
      }

      return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
    });

    render(<AppShell />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    });

    const firstColumnTitle = screen.getAllByLabelText("Column title")[0];
    await userEvent.clear(firstColumnTitle);
    await userEvent.type(firstColumnTitle, "Renamed");

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        "/api/board",
        expect.objectContaining({ method: "PUT" })
      );
    });
  });

  it("sends chat prompts and renders assistant response", async () => {
    window.localStorage.setItem("pm_auth_token", "token-123");

    mockedFetch.mockImplementation((input, init) => {
      const url = getUrl(input);
      const method = init?.method ?? "GET";

      if (url === "/api/auth/me") {
        return Promise.resolve(jsonResponse({ username: "user" }));
      }

      if (url === "/api/board" && method === "GET") {
        return Promise.resolve(jsonResponse(initialData));
      }

      if (url === "/api/board" && method === "PUT") {
        return Promise.resolve(jsonResponse(JSON.parse(String(init?.body ?? "{}"))));
      }

      if (url === "/api/chat" && method === "POST") {
        return Promise.resolve(
          jsonResponse({
            assistant: "I moved the card.",
            board: null,
          })
        );
      }

      return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
    });

    render(<AppShell />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText("Message"), "Move card-1 to review");
    await userEvent.click(screen.getByRole("button", { name: "Send to AI" }));

    await waitFor(() => {
      expect(screen.getByText("I moved the card.")).toBeInTheDocument();
    });

    expect(mockedFetch).toHaveBeenCalledWith(
      "/api/chat",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("applies board updates returned by chat endpoint", async () => {
    window.localStorage.setItem("pm_auth_token", "token-123");

    const aiBoard = {
      columns: [{ id: "col-backlog", title: "Backlog", cardIds: ["card-1"] }],
      cards: {
        "card-1": {
          id: "card-1",
          title: "AI Updated Card",
          details: "Updated by assistant.",
        },
      },
    };

    mockedFetch.mockImplementation((input, init) => {
      const url = getUrl(input);
      const method = init?.method ?? "GET";

      if (url === "/api/auth/me") {
        return Promise.resolve(jsonResponse({ username: "user" }));
      }

      if (url === "/api/board" && method === "GET") {
        return Promise.resolve(jsonResponse(initialData));
      }

      if (url === "/api/chat" && method === "POST") {
        return Promise.resolve(
          jsonResponse({
            assistant: "Applied board update.",
            board: aiBoard,
          })
        );
      }

      if (url === "/api/board" && method === "PUT") {
        return Promise.resolve(jsonResponse(JSON.parse(String(init?.body ?? "{}"))));
      }

      return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
    });

    render(<AppShell />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText("Message"), "Update board");
    await userEvent.click(screen.getByRole("button", { name: "Send to AI" }));

    await waitFor(() => {
      expect(screen.getByText("AI Updated Card")).toBeInTheDocument();
    });
  });

  it("shows chat error when AI request fails", async () => {
    window.localStorage.setItem("pm_auth_token", "token-123");

    mockedFetch.mockImplementation((input, init) => {
      const url = getUrl(input);
      const method = init?.method ?? "GET";

      if (url === "/api/auth/me") {
        return Promise.resolve(jsonResponse({ username: "user" }));
      }

      if (url === "/api/board" && method === "GET") {
        return Promise.resolve(jsonResponse(initialData));
      }

      if (url === "/api/chat" && method === "POST") {
        return Promise.resolve(
          jsonResponse({ detail: "AI service returned invalid JSON." }, 502)
        );
      }

      if (url === "/api/board" && method === "PUT") {
        return Promise.resolve(jsonResponse(JSON.parse(String(init?.body ?? "{}"))));
      }

      return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
    });

    render(<AppShell />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText("Message"), "Update board");
    await userEvent.click(screen.getByRole("button", { name: "Send to AI" }));

    await waitFor(() => {
      expect(
        screen.getByText("AI service returned invalid JSON.")
      ).toBeInTheDocument();
    });
  });

  it("shows sync error banner when board save fails", async () => {
    window.localStorage.setItem("pm_auth_token", "token-123");

    mockedFetch.mockImplementation((input, init) => {
      const url = getUrl(input);
      const method = init?.method ?? "GET";

      if (url === "/api/auth/me") {
        return Promise.resolve(jsonResponse({ username: "user" }));
      }

      if (url === "/api/board" && method === "GET") {
        return Promise.resolve(jsonResponse(initialData));
      }

      if (url === "/api/board" && method === "PUT") {
        return Promise.resolve(jsonResponse({ detail: "Internal server error" }, 500));
      }

      return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
    });

    render(<AppShell />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    });

    const firstColumnTitle = screen.getAllByLabelText("Column title")[0];
    await userEvent.clear(firstColumnTitle);
    await userEvent.type(firstColumnTitle, "Renamed");

    await waitFor(() => {
      expect(
        screen.getByText("Could not sync board changes to the server.")
      ).toBeInTheDocument();
    });
  });
});
