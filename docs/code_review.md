# Code Review

Reviewed: 2026-04-20. Covers all backend, frontend, test, and infrastructure files.
Remediation pass: 2026-04-21. All Critical, High, and Medium items resolved unless noted.

---

## Critical Actions (Fix Before Production)

1. ~~**Fix the board update race condition**~~ — **FIXED** — `board_repository.py` refactored to use a single connection per operation; all helpers now accept the connection so read and write happen within one transaction.
2. **Replace hardcoded credentials** — `user`/`password` must be replaced with a real auth mechanism before any non-demo deployment. Marked in code; deferred by design for MVP.
3. ~~**Add CORS policy**~~ — **FIXED** — `CORSMiddleware` added to `main.py` with `allow_origins=["*"]`; restrict to a specific origin before production.
4. ~~**Add rate limiting to the login endpoint**~~ — **FIXED** — `slowapi==0.1.9` added; login endpoint limited to 60 requests/minute per IP.

---

## Security

### HIGH

**`backend/app/auth.py:11` — Hardcoded JWT secret fallback**
`DEFAULT_JWT_SECRET = "pm-dev-jwt-secret"` is used when `JWT_SECRET` is not set.
Action: Remove the default and fail fast on startup. Deferred — `.env` is gitignored and the secret is set there; acceptable for current MVP deployment model.

~~**No `.env.example` file exists**~~ — **FIXED** — `.env.example` created with placeholders for all required variables.

~~**`backend/app/auth.py:36–37` — Hardcoded MVP credentials not marked**~~ — **FIXED** — Comment added: "MVP only — replace with DB-backed auth + bcrypt before production."

### MEDIUM

~~**`backend/app/main.py` — No CORS configuration**~~ — **FIXED** — `CORSMiddleware` added.

~~**`backend/app/main.py` — No rate limiting on `POST /api/auth/login`**~~ — **FIXED** — `slowapi` added; 60/minute limit per IP.

**`backend/app/ai_client.py:40–46` — History items silently dropped**
Invalid history entries are filtered without raising an error.
Note: by the time history reaches `ai_client.py` it has already passed Pydantic validation in `ChatMessage`; the filter is defence-in-depth. Acceptable for MVP.

### LOW

**`frontend/src/components/AppShell.tsx:101` — JWT in `localStorage`**
Longer-term: migrate to `HttpOnly` cookies and add a Content Security Policy.

---

## Correctness

### HIGH

~~**`backend/app/board_repository.py` — Race condition on board update**~~ — **FIXED** — `_get_or_create_user_id` and `_get_or_create_active_board_id` are now private helpers that accept an open connection; both `get_active_board` and `update_active_board` execute all work inside a single `with connect() as conn:` block.

### MEDIUM

~~**`backend/app/board_repository.py` — Missing explicit commit / multiple connections**~~ — **FIXED** — Each public method now uses a single `with connect() as conn:` block; `deepcopy` replaced with `json.loads(json.dumps(...))`.

~~**`backend/app/main.py:169–207` — All AI parse errors return the same 502 message**~~ — **FIXED** — Three distinct messages now returned:
- `"AI service returned invalid JSON."` (JSONDecodeError)
- `"AI service returned unexpected response format."` (non-dict)
- `"AI response did not match expected schema."` (ValidationError)

~~**`frontend/src/lib/kanban.ts` — `createId()` uses `Math.random()`**~~ — **FIXED** — Replaced with `crypto.getRandomValues()` + timestamp suffix.

### LOW

~~**`backend/app/board_repository.py:63` — `deepcopy` on fallback**~~ — **FIXED** as part of the race condition fix.

---

## Code Quality

### MEDIUM

**`backend/app/main.py` — Chat endpoint does too much**
Extract into a `ChatService` class. Deferred — scope is appropriate for MVP; refactor when adding multi-board or multi-user features.

**`backend/app/main.py` — `get_board()` return type annotation says `dict`**
Should return `BoardStateModel` and annotate accordingly. Low risk since FastAPI validates via `response_model`. Deferred.

**`frontend/src/components/AppShell.tsx` — Implicit auth/board state machine**
Multiple `useState` hooks; invalid state combinations are possible. Deferred — add `useReducer` or a discriminated union when extending auth flows.

### LOW

**`backend/app/main.py:126–128` — `/api/hello` scaffold endpoint**
Remove or replace with a proper `/api/health` liveness endpoint.

**`frontend/src/lib/api.ts:29–44` — Unvalidated API response casting**
Use `zod` to validate at the API boundary.

**Backend — No logging**
Add `logging.getLogger(__name__)` at minimum to auth failures and AI client errors.

---

## Test Coverage

### MEDIUM

~~**No test for concurrent board updates**~~ — **FIXED** — `test_concurrent_board_updates_are_safe` added to `test_board_repository.py`; 10 concurrent updates via `ThreadPoolExecutor`.

~~**No test for expired token on protected API routes**~~ — **FIXED** — `test_expired_token_rejected` added to `test_board_api.py`.

~~**Frontend: no test for board sync failure**~~ — **FIXED** — `shows sync error banner when board save fails` added to `AppShell.test.tsx`.

### LOW

**No tests for board validation edge cases**
Empty titles, very long strings, special characters. Add parameterised tests.

**No test for AI response missing the `board` field entirely**
Add a test that returns `{"assistant": "ok"}` (no `board` key) and verifies safe handling.

---

## Performance

### MEDIUM

~~**`frontend/src/components/KanbanBoard.tsx:164` — Inline card lookup not using memoized reference**~~ — **FIXED** — Changed to use `cardsById` (already memoized via `useMemo`) instead of `board.cards` directly.

### LOW

**`frontend/src/components/AppShell.tsx` — Full message list re-renders on every chat reply**
Virtualise with `react-window` or cap visible history for long conversations.

**`frontend/src/lib/api.ts` — No board fetch caching**
Add a short TTL cache to avoid redundant fetches after AI-triggered board refreshes.

---

## Architecture

### MEDIUM

**Board defaults duplicated across frontend and backend**
`board_defaults.py` and `kanban.ts` both define the default board. Make the backend the single source of truth; frontend should always receive its initial state from `GET /api/board`.

**No schema migration path**
`db.py` embeds DDL directly. Introduce `alembic` or versioned migration scripts for the next schema change.

### LOW

**No OpenAPI documentation URL documented**
Swagger is available at `/docs` by default. Note the URL in CLAUDE.md and README.
