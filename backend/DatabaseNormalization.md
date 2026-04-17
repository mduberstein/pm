# Database Normalization Plan

This document defines the phased path from MVP JSON blob board storage to normalized relational tables.

## Current State (MVP)

- Board state is stored as one JSON blob per active board in `boards.board_state_json`.
- User to board ownership is already modeled (`boards.user_id`).

## Target State

Move board structure into relational tables while keeping API behavior stable.

Target tables:
- `boards` (metadata only)
- `columns`
- `cards`
- `column_cards` (ordering and placement)

## Phased Migration

### Phase 0: Prepare (No behavior changes)

- Keep existing `boards.board_state_json` as source of truth.
- Ensure every board row has `schema_version`.
- Add migration bookkeeping table if needed (`schema_migrations`).

Exit criteria:
- MVP behavior unchanged.
- Schema versioning in place.

### Phase 1: Introduce Normalized Tables

Create tables:

- `columns`
  - `id` TEXT PRIMARY KEY
  - `board_id` INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE
  - `title` TEXT NOT NULL
  - `position` INTEGER NOT NULL

- `cards`
  - `id` TEXT PRIMARY KEY
  - `board_id` INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE
  - `title` TEXT NOT NULL
  - `details` TEXT NOT NULL
  - `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  - `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

- `column_cards`
  - `board_id` INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE
  - `column_id` TEXT NOT NULL REFERENCES columns(id) ON DELETE CASCADE
  - `card_id` TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE
  - `position` INTEGER NOT NULL
  - PRIMARY KEY (`column_id`, `card_id`)

Indexes:
- `idx_columns_board_position`
- `idx_cards_board_id`
- `idx_column_cards_column_position`

Exit criteria:
- New tables created.
- Existing API still reads/writes JSON blob only.

### Phase 2: Backfill Data

- Parse each board JSON blob.
- Insert columns/cards/ordering rows into normalized tables.
- Keep `boards.board_state_json` unchanged.

Data validation checks:
- Column count and IDs match JSON.
- Card count and IDs match JSON.
- Column ordering and card ordering match JSON.

Exit criteria:
- Every existing board has a complete normalized copy.

### Phase 3: Dual Write and Read Verification

- Write path updates both JSON blob and normalized tables in one transaction.
- Read path continues serving JSON blob responses for API compatibility.
- Add consistency checker job/test comparing normalized reconstruction against JSON blob.

Exit criteria:
- Dual-write is stable.
- No consistency mismatches in repeated verification runs.

### Phase 4: Switch Primary Read Path

- Read board state from normalized tables.
- Reconstruct API response in existing board JSON shape.
- Keep JSON blob as fallback for one release window.

Exit criteria:
- API responses unchanged.
- Performance and correctness accepted.

### Phase 5: Decommission JSON Blob (Optional)

- Remove dual-write path.
- Keep backup migration/export strategy.
- Optionally keep `board_state_json` as cached snapshot if useful.

Exit criteria:
- Normalized model is sole source of truth.

## Risk Controls

- Always migrate in transactions.
- Add rollback scripts for each migration step.
- Run backup before backfill and before read-path cutover.
- Keep strict parity tests between old and new representations.

## API Compatibility Rule

The external API contract should stay stable during all phases:
- Request/response shape for board operations remains the current board JSON structure.
