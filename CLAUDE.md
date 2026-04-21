# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Kanban board web app with an AI chat assistant. Single Docker container serves both the Next.js frontend (static export) and the FastAPI backend. SQLite stores board state per user. The AI integration uses OpenRouter to let users manipulate the board via natural language.

## Commands

### Frontend (`frontend/`)

```bash
npm run dev             # dev server
npm run build           # production build
npm run lint            # ESLint
npm run test:unit       # Vitest unit tests
npm run test:unit:watch # watch mode
npm run test:e2e        # Playwright E2E tests
npm run test:all        # unit + E2E
```

### Backend (`backend/`)

```bash
pytest                       # all tests
pytest tests/unit/           # unit tests
pytest tests/integration/    # integration tests
pytest tests/e2e/            # E2E tests
pytest -v                    # verbose
```

### Docker

```bash
scripts/start-mac.sh   # build + run container (port 8000)
scripts/stop-mac.sh    # stop + remove container
```

Environment variables go in `.env` at the repo root:
- `OPENROUTER_API_KEY` — required for chat
- `JWT_SECRET` — defaults to `pm-dev-jwt-secret`
- `JWT_EXPIRE_MINUTES` — defaults to 480
- `DB_PATH` — defaults to `backend/data/pm.db`

## Architecture

### Request flow

1. Browser loads `/` → FastAPI serves static Next.js export from `backend/static/frontend/`
2. Login → `POST /api/auth/login` → JWT stored in `localStorage` as `pm_auth_token`
3. Board load/save → `GET/PUT /api/board` with Bearer token
4. Chat → `POST /api/chat` with prompt + board state + history → returns `{ assistant, board | null }`; if board is non-null, the frontend applies mutations and saves

### Backend (`backend/app/`)

| File | Role |
|------|------|
| `main.py` | FastAPI app, all route handlers |
| `auth.py` | JWT create/validate, hardcoded MVP credentials (`user`/`password`) |
| `db.py` | SQLite init, schema (`users`, `boards` tables) |
| `board_repository.py` | Board CRUD; active-board lookup per user |
| `ai_client.py` | OpenRouter client; sends prompt + full board JSON; expects `{ assistant, board }` JSON response |
| `board_defaults.py` | Default board template on first login |

Board state is stored as a JSON blob in `boards.board_state_json`. No partial updates — the full board is replaced on every save.

### Frontend (`frontend/src/`)

| File | Role |
|------|------|
| `app/page.tsx` | Entry point |
| `components/AppShell.tsx` | Auth wrapper, board load/logout, top-level state |
| `components/KanbanBoard.tsx` | Columns + drag-and-drop |
| `components/ChatSidebar.tsx` | Chat UI |
| `lib/api.ts` | All HTTP calls to backend |
| `lib/kanban.ts` | Pure board-state mutations (`moveCard`, etc.) |
| `lib/chat.ts` | Chat history management |

State lives in `AppShell` via `useState`; passed down as props. Board updates are optimistic — UI updates immediately, then async `PUT /api/board`.

### Board data model

```ts
{
  columns: [{ id, title, cardIds: string[] }],
  cards: { [id]: { id, title, details } }
}
```

Five fixed columns: Backlog, Discovery, In Progress, Review, Done.

### Docker build (multi-stage)

1. Node 22 builds Next.js → `frontend/out/`
2. Python 3.12 runs FastAPI, copies built frontend to `backend/static/frontend/`

## Coding Standards (from AGENTS.md)

- Keep it simple — never over-engineer, always simplify
- Identify root cause before trying fixes; prove with evidence
- Use latest library versions and idiomatic approaches

## Color Palette

Accent Yellow `#ecad0a` · Blue Primary `#209dd7` · Purple Secondary `#753991` · Dark Navy `#032147` · Gray Text `#888888`
