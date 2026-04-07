# Frontend Overview

This document describes the current frontend implementation in `frontend/`.

## Stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS v4
- Drag and drop: `@dnd-kit/core` + `@dnd-kit/sortable`
- Unit/integration tests: Vitest + Testing Library
- End-to-end tests: Playwright

## Current App Behavior

- App entrypoint is `src/app/page.tsx` and renders `KanbanBoard`.
- The board is currently frontend-only (in-memory state).
- Features currently implemented:
- Rename fixed columns
- Add card
- Delete card
- Drag-and-drop card reorder within a column
- Drag-and-drop card move across columns

## File Map

- `src/app/layout.tsx`
- Sets global metadata and fonts (`Space_Grotesk`, `Manrope`).
- `src/app/globals.css`
- Defines CSS variables and global theme values, including project palette.
- `src/app/page.tsx`
- Renders the main `KanbanBoard` component.
- `src/components/KanbanBoard.tsx`
- Owns board state and drag lifecycle handlers.
- Wires rename/add/delete card callbacks.
- Renders columns and drag overlay preview.
- `src/components/KanbanColumn.tsx`
- Renders one column, editable title, sortable card list, and new-card form.
- `src/components/KanbanCard.tsx`
- Renders sortable card with remove action.
- `src/components/KanbanCardPreview.tsx`
- Preview card shown in drag overlay.
- `src/components/NewCardForm.tsx`
- Toggleable form for adding a card to a column.
- `src/lib/kanban.ts`
- Board/card/column types.
- Seed data (`initialData`).
- Helpers: `moveCard`, `createId`.

## Tests

- `src/components/KanbanBoard.test.tsx`
- Component behavior tests (render, rename, add/remove card).
- `src/lib/kanban.test.ts`
- Unit tests for `moveCard` behavior.
- `tests/kanban.spec.ts`
- Playwright e2e flow (load board, add card, drag card).

## Commands

- `npm run dev`: start Next.js dev server.
- `npm run build`: production build.
- `npm run start`: run production server.
- `npm run test:unit`: run Vitest tests.
- `npm run test:e2e`: run Playwright tests.
- `npm run test:all`: run unit then e2e tests.

## Notes for Future Phases

- Current board state is local in `KanbanBoard` and should be replaced with backend API state in later phases.
- Existing tests provide baseline UX coverage and should be expanded as auth, persistence, and AI features are added.
