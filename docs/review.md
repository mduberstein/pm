# Code Review — PM Kanban App

**Date:** 2026-04-23  
**Scope:** Full codebase (no open PRs; general review)

---

## Overview

Solid MVP. The architecture is clean and well-layered: FastAPI routers → repository → DB, and a React component tree with state living in `AppShell`. The board data model is simple and consistent end-to-end (same shape in DB, API, and frontend types). Pydantic validation is thorough. Test files exist for all major modules.

The issues below are organized by severity.

---

## Critical

### 1. Synchronous `httpx` blocks the event loop (`ai_client.py:122`)

`fetch_assistant_reply` uses `httpx.post` (synchronous) inside a FastAPI async route handler. This blocks the entire event loop for the 20-second AI timeout, freezing all other requests during that time.

**Fix:** Use `httpx.AsyncClient` and make `fetch_assistant_reply` async, or wrap in `asyncio.to_thread`.

```python
async with httpx.AsyncClient() as client:
    response = await client.post(...)
```

### 2. Board overwrite race condition (`routers/chat.py:19` vs `routers/board.py:18`)

The chat endpoint fetches the board from the DB, sends it to the AI, and then saves the AI's result. If the user drags a card while waiting for the AI response, the frontend fires `PUT /api/board` concurrently. The AI response will then overwrite those drag changes silently — **data loss**.

The chat endpoint should either (a) accept the current board state from the client in `ChatRequest` instead of fetching from DB, or (b) use optimistic locking (e.g., a `updated_at` version check before saving the AI result).

---

## High

### 3. Hardcoded JWT secret (`auth.py:11`)

`DEFAULT_JWT_SECRET = "pm-dev-jwt-secret"` is used when `JWT_SECRET` isn't set. Deployed without the env var, every JWT is signed with a known public string — anyone can forge tokens. The app should refuse to start if `JWT_SECRET` is unset in non-dev environments, or at minimum log a loud warning.

### 4. No rate limiting on `/api/chat` (`routers/chat.py`)

Login is rate-limited (60/min), but the chat endpoint has no limit. Each chat call hits the OpenRouter API (potentially expensive) and does two DB writes. A user or attacker can exhaust the API key budget or lock the DB under load.

### 5. CORS wildcard (`main.py:31`)

`allow_origins=["*"]` allows any origin to make credentialed requests. For a single-container app that serves its own frontend, this should be locked to the known origin (or `localhost` in dev).

---

## Medium

### 6. `fetchCurrentUser` double-request on session restore (`AppShell.tsx:72-76`)

On load, the app calls `/api/auth/me` to verify the token, then immediately calls `/api/board`. The board request would return 401 on an expired token anyway, so `fetchCurrentUser` only adds latency. Drop it and let `loadBoard` handle the 401 → logout path.

### 7. `handleBoardChange` can clobber rapid changes (`AppShell.tsx:117-133`)

The function does `setBoard(nextBoard)` optimistically, fires `updateBoard(token, nextBoard)` async, and then calls `setBoard(persisted)` on success. If two drag events fire quickly, the slower network response from the first can overwrite the second drag's result. A request-in-flight guard (abort on new request) or debounce would fix this.

### 8. AI board updates bypass `onBoardChange` (`AppShell.tsx:163-165`)

When the AI returns a new board, `handleChatSend` calls `setBoard(response.board)` but never calls `handleBoardChange`. The server already saved the AI board, but `KanbanBoard`'s internal state is now out of sync with `AppShell`'s board — it only re-syncs via the `useEffect` on `initialBoard` prop change. This works today, but is fragile: any code that needs to react to AI-triggered board changes via `onBoardChange` would be silently skipped.

### 9. Duplicate `cardId` not validated (`models.py:30-45`)

`BoardStateModel.validate_board_references` checks that `cardIds` reference existing cards but doesn't catch the same card appearing in multiple columns, or twice in the same column. The AI could produce such a state and it would pass validation and be persisted.

### 10. `connect()` missing `check_same_thread=False` (`db.py:43-47`)

SQLite connections require `check_same_thread=False` when shared across threads. With uvicorn's default single-worker async mode this is fine, but running with `--workers > 1` or in tests that spin up threads would cause `ProgrammingError`. Low risk now, but worth adding defensively.

---

## Low / Style

### 11. Module-level `messageCounter` resets on reload (`chat.ts:9`)

`let messageCounter = 0` is a module-level counter. It resets to 0 on every HMR reload in dev, generating duplicate `msg-1`, `msg-2` IDs. Since these are only React list keys they won't cause real bugs, but using `crypto.randomUUID()` (or the same `createId` pattern from `kanban.ts`) would be cleaner.

### 12. Login form pre-fills credentials (`AppShell.tsx:45-46`)

```ts
const [username, setUsername] = useState("user");
const [password, setPassword] = useState("password");
```

Credentials are pre-filled in state. Fine for an MVP demo, but should be cleared before any wider deployment, and the UI hint "Use the MVP credentials" already tells users what to type.

### 13. `"No details yet."` default for empty card details (`KanbanBoard.tsx:84`)

`details: details || "No details yet."` substitutes a placeholder string when the user leaves details blank. This makes it impossible to distinguish "user intentionally left blank" from "default." An empty string is a cleaner default; display the placeholder in the UI via CSS `::placeholder` or conditional rendering instead.

### 14. `/api/hello` defined in `main.py` (`main.py:41-43`)

A one-liner health check endpoint is fine, but it breaks the pattern of all other routes living in routers. Move it to a router or rename it `/api/health` for consistency with standard conventions.

### 15. `isSubmitting` cleanup on login not in `finally` (`AppShell.tsx:87-115`)

`setIsSubmitting(false)` is repeated in three places (success path, 401 path, generic error path). A `finally` block would be cleaner and more robust if the try body is extended.

---

## Testing Gaps

- No integration test for the chat → concurrent board update race (issue #2).
- No test for `BoardStateModel` rejecting duplicate `cardId` across columns (issue #9).
- No frontend test for the AI board update path (`handleChatSend` with `response.board` non-null).
- The `fetch_assistant_reply` tests likely use synchronous `httpx` mocks; those will need updating when moved to async (issue #1).

---

## Summary

| Priority | Count | Top item |
|----------|-------|----------|
| Critical | 2 | Sync httpx blocks event loop; board overwrite race |
| High | 3 | Hardcoded JWT default; no chat rate limit; CORS wildcard |
| Medium | 5 | Double request on load; rapid-drag clobber; duplicate cardId |
| Low | 5 | Style and UX nits |
