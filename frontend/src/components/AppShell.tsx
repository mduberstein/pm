"use client";

import { FormEvent, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const AUTH_TOKEN_KEY = "pm_auth_token";

type AuthStatus = "checking" | "authenticated" | "unauthenticated";

type LoginResponse = {
  access_token: string;
  token_type: string;
};

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
  const [username, setUsername] = useState("user");
  const [password, setPassword] = useState("password");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const verifySession = async () => {
      const token = getToken();
      if (!token) {
        setAuthStatus("unauthenticated");
        return;
      }

      try {
        const response = await fetch("/api/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          clearToken();
          setAuthStatus("unauthenticated");
          return;
        }

        setAuthStatus("authenticated");
      } catch {
        clearToken();
        setAuthStatus("unauthenticated");
      }
    };

    void verifySession();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      if (!response.ok) {
        setErrorMessage("Invalid username or password.");
        setIsSubmitting(false);
        return;
      }

      const data = (await response.json()) as LoginResponse;
      if (!data.access_token) {
        setErrorMessage("Unable to start session.");
        setIsSubmitting(false);
        return;
      }

      window.localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
      setAuthStatus("authenticated");
      setIsSubmitting(false);
    } catch {
      setErrorMessage("Login failed. Please try again.");
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    setAuthStatus("unauthenticated");
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
      <KanbanBoard />
    </div>
  );
};
