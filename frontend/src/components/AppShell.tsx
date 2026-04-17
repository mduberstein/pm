"use client";

import { FormEvent, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import {
  ApiError,
  fetchBoard,
  fetchCurrentUser,
  loginRequest,
  updateBoard,
} from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

const AUTH_TOKEN_KEY = "pm_auth_token";

type AuthStatus = "checking" | "authenticated" | "unauthenticated";
type BoardStatus = "idle" | "loading" | "ready" | "error";

const getToken = () => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
};

const clearToken = () => {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
};

export const AppShell = () => {
  const [authStatus, setAuthStatus] = useState<AuthStatus>("checking");
  const [boardStatus, setBoardStatus] = useState<BoardStatus>("idle");
  const [board, setBoard] = useState<BoardData | null>(null);
  const [boardError, setBoardError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [username, setUsername] = useState("user");
  const [password, setPassword] = useState("password");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadBoard = async (token: string) => {
    setBoardStatus("loading");
    setBoardError(null);

    try {
      const data = await fetchBoard(token);
      setBoard(data);
      setBoardStatus("ready");
    } catch {
      setBoardStatus("error");
      setBoardError("Unable to load board data. Please try again.");
    }
  };

  useEffect(() => {
    const verifySession = async () => {
      const token = getToken();
      if (!token) {
        setAuthStatus("unauthenticated");
        return;
      }

      try {
        await fetchCurrentUser(token);

        setAuthStatus("authenticated");
        await loadBoard(token);
      } catch {
        clearToken();
        setAuthStatus("unauthenticated");
        setBoardStatus("idle");
      }
    };

    void verifySession();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const data = await loginRequest(username, password);

      if (!data.access_token) {
        setErrorMessage("Unable to start session.");
        setIsSubmitting(false);
        return;
      }

      window.localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
      setAuthStatus("authenticated");
      await loadBoard(data.access_token);
      setIsSubmitting(false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setErrorMessage("Invalid username or password.");
        setIsSubmitting(false);
        return;
      }

      setErrorMessage("Login failed. Please try again.");
      setIsSubmitting(false);
    }
  };

  const handleBoardChange = async (nextBoard: BoardData) => {
    setBoard(nextBoard);
    setSyncError(null);

    const token = getToken();
    if (!token) {
      handleLogout();
      return;
    }

    try {
      const persisted = await updateBoard(token, nextBoard);
      setBoard(persisted);
    } catch {
      setSyncError("Could not sync board changes to the server.");
    }
  };

  const handleLogout = () => {
    clearToken();
    setAuthStatus("unauthenticated");
    setBoardStatus("idle");
    setBoard(null);
    setBoardError(null);
    setSyncError(null);
  };

  if (authStatus === "checking") {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
        <div className="rounded-2xl border border-[var(--stroke)] bg-white px-6 py-5 text-sm font-semibold text-[var(--gray-text)] shadow-[var(--shadow)]">
          Checking session...
        </div>
      </main>
    );
  }

  if (authStatus === "unauthenticated") {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
        <section className="w-full rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Project Management MVP
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Sign in to Kanban Studio
          </h1>
          <p className="mt-2 text-sm text-[var(--gray-text)]">
            Use the MVP credentials to access the board.
          </p>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--gray-text)]">
                Username
              </span>
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="username"
                required
              />
            </label>

            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--gray-text)]">
                Password
              </span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
                required
              />
            </label>

            {errorMessage ? (
              <p className="rounded-xl border border-[#f2c0c0] bg-[#fff5f5] px-3 py-2 text-sm text-[#962626]">
                {errorMessage}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <div>
      <div className="mx-auto flex max-w-[1500px] justify-end px-6 pt-6">
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)]"
        >
          Log out
        </button>
      </div>

      {boardStatus === "loading" ? (
        <main className="mx-auto flex min-h-[40vh] max-w-[1500px] items-center justify-center px-6 pb-8">
          <div className="rounded-2xl border border-[var(--stroke)] bg-white px-6 py-5 text-sm font-semibold text-[var(--gray-text)] shadow-[var(--shadow)]">
            Loading board...
          </div>
        </main>
      ) : null}

      {boardStatus === "error" ? (
        <main className="mx-auto flex min-h-[40vh] max-w-[1500px] items-center justify-center px-6 pb-8">
          <div className="rounded-2xl border border-[#f2c0c0] bg-[#fff5f5] px-6 py-5 text-sm text-[#962626] shadow-[var(--shadow)]">
            <p>{boardError ?? "Unable to load board data."}</p>
            <button
              type="button"
              onClick={() => {
                const token = getToken();
                if (token) {
                  void loadBoard(token);
                }
              }}
              className="mt-3 rounded-full border border-[#962626] px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em]"
            >
              Retry
            </button>
          </div>
        </main>
      ) : null}

      {boardStatus === "ready" && board ? (
        <>
          {syncError ? (
            <div className="mx-auto mt-4 max-w-[1500px] px-6">
              <div className="rounded-xl border border-[#f2c0c0] bg-[#fff5f5] px-4 py-3 text-sm text-[#962626]">
                {syncError}
              </div>
            </div>
          ) : null}
          <KanbanBoard initialBoard={board} onBoardChange={handleBoardChange} />
        </>
      ) : null}
    </div>
  );
};
