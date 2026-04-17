# Database Model (Part 5)

## Scope

This document defines the MVP database model for persistent Kanban storage.

Goals:
- Support a future user -> board(s) relationship.
- Keep MVP persistence simple by storing the full board as one JSON blob.
- Keep the schema ready for a later normalized conversion.

Non-goals for MVP:
- No normalized card/column tables yet.
- No DB-backed authentication yet (login remains hardcoded for MVP).

## Engine

- SQLite local file database.
- Database file is created automatically if missing during backend startup (implemented in Part 6).

## MVP Tables

### users

Purpose:
- Represents user accounts that can own boards.

Columns:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT NOT NULL UNIQUE
- `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

Notes:
- For MVP login, credentials are still hardcoded in app code.
- This table exists so board ownership can be modeled correctly now.

### boards

Purpose:
- Stores each board owned by a user.
- In MVP, full board state is stored in `board_state_json`.

Columns:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
- `name` TEXT NOT NULL DEFAULT 'Main Board'
- `is_active` INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
- `board_state_json` TEXT NOT NULL CHECK (json_valid(board_state_json))
- `schema_version` INTEGER NOT NULL DEFAULT 1
- `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

Indexes and constraints:
- `CREATE INDEX idx_boards_user_id ON boards(user_id);`
- `CREATE UNIQUE INDEX idx_boards_user_active ON boards(user_id) WHERE is_active = 1;`

Why this shape:
- Supports many boards per user in the future.
- Enforces exactly one active board per user in MVP.
- Keeps reads/writes simple for Part 6 (single JSON payload round-trip).

## Reference DDL

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL DEFAULT 'Main Board',
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  board_state_json TEXT NOT NULL CHECK (json_valid(board_state_json)),
  schema_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_boards_user_active
  ON boards(user_id)
  WHERE is_active = 1;
```

## JSON Shape Stored in board_state_json

The payload mirrors the existing frontend board shape.

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"] }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Example card",
      "details": "Example details"
    }
  }
}
```

Rules:
- Full-board replace writes for MVP.
- The server validates payload structure before save (Part 6).
- `schema_version` tracks format evolution.

## Operational Notes for Part 6

Expected backend operations:
- Get active board for authenticated user.
- Create default user/board row on first access if not present.
- Update active board with full JSON payload.
- Update `updated_at` on every board write.

## Why JSON Blob First

This reduces complexity for MVP:
- Minimal mapping logic.
- Fast path to persistence.
- Direct compatibility with current frontend state shape.

Normalized design is intentionally deferred and documented in [backend/DatabaseNormalization.md](../backend/DatabaseNormalization.md).
