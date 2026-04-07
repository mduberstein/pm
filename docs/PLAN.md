# Project Plan

This plan is the execution checklist for the MVP.

## Locked Decisions

- Single container runtime: FastAPI serves API routes and static Next.js build output.
- Auth approach: lightweight JWT tokens.
- Data model direction: user -> board(s), with MVP persistence storing each board as one JSON blob.
- AI output handling: strict JSON schema validation on backend responses.
- Test bar: unit + integration + end-to-end where applicable.
- Script names will be defined in this plan and implemented later.

## Part 1: Plan (Current Step)

### Checklist

- [x] Expand this plan with detailed checklists, tests, and success criteria for every phase.
- [x] Capture all confirmed architecture and product decisions.
- [x] Create `frontend/AGENTS.md` describing the current frontend codebase.
- [x] User reviews and approves this plan before Part 2 starts.

### Tests

- [x] Documentation quality check: verify every part contains tasks, tests, and success criteria.
- [x] Scope check: verify plan includes Docker, backend, frontend integration, auth, DB, AI, and scripts.

### Success Criteria

- [x] Plan is actionable without ambiguity for Parts 2-10.
- [x] User explicitly signs off on plan contents.

## Part 2: Scaffolding

### Checklist

- [x] Add Docker setup at repository root to run the app locally in one container.
- [x] Create FastAPI app structure in `backend/`.
- [x] Add a hello-world HTML response to verify static serving.
- [x] Add a hello-world API route to verify backend routing.
- [x] Define and scaffold start/stop scripts in `scripts/`:
- [x] `scripts/start-mac.sh`
- [x] `scripts/stop-mac.sh`
- [x] `scripts/start-linux.sh`
- [x] `scripts/stop-linux.sh`
- [x] `scripts/start-windows.ps1`
- [x] `scripts/stop-windows.ps1`
- [x] Ensure scripts are minimal and only support local MVP run/stop workflow.

### Tests

- [x] Unit: backend app boots and root/api routes return expected payloads.
- [x] Integration: container starts and both HTML + API endpoints are reachable.
- [x] End-to-end: run start script, load page, call API, run stop script cleanly.

### Success Criteria

- [x] `docker` startup serves hello-world HTML and API.
- [x] Start/stop scripts work on macOS, Linux, and Windows PowerShell.
- [x] No manual setup beyond `.env` and documented commands.

Note: scripts were implemented for all three platforms and validated on macOS. Linux/Windows runtime execution was explicitly accepted as skipped by user approval.

## Part 3: Add Frontend

### Checklist

- [ ] Build Next.js frontend into static assets.
- [ ] Configure FastAPI static file serving for the built frontend at `/`.
- [ ] Preserve existing Kanban interactions in served production build.
- [ ] Keep architecture single-container with no separate frontend runtime.

### Tests

- [ ] Unit: existing frontend unit suite passes.
- [ ] Integration: backend serves built frontend files correctly.
- [ ] End-to-end: browser test validates board rendering at `/` in containerized app.

### Success Criteria

- [ ] Visiting `/` shows the current Kanban UI from built frontend.
- [ ] Existing drag/add/remove/rename behavior remains functional.
- [ ] Test suites pass in CI-local command flow.

## Part 4: Fake Sign In (JWT)

### Checklist

- [ ] Add login screen at `/` when no valid token exists.
- [ ] Validate only MVP credentials: `user` / `password`.
- [ ] On success, issue lightweight JWT with minimal claims.
- [ ] Persist token in a simple client-safe MVP storage approach.
- [ ] Add logout flow that clears token and returns to login.
- [ ] Protect board access so unauthenticated sessions cannot view it.

### Tests

- [ ] Unit: credential validation and token utility behavior.
- [ ] Integration: auth middleware/dependency enforces protected access.
- [ ] End-to-end: login success, login failure, logout behavior, guarded routes.

### Success Criteria

- [ ] Unauthenticated user sees login screen, not board.
- [ ] Authenticated user sees board until logout/token expiry.
- [ ] Invalid credentials never create a valid session.

## Part 5: Database Modeling

### Checklist

- [ ] Define SQLite schema for users and boards (user -> board(s)).
- [ ] For MVP persistence, store each board state as a JSON blob column.
- [ ] Document schema and rationale in `docs/`.
- [ ] Add future normalization plan in `backend/DatabaseNormalization.md`.
- [ ] Include phased migration path from JSON blob to normalized tables.
- [ ] Request and obtain user sign-off before implementing data access layer.

### Tests

- [ ] Unit: schema creation helpers generate expected tables/constraints.
- [ ] Integration: startup creates DB file and schema when missing.
- [ ] End-to-end: initial app run creates usable DB and persists sample board.

### Success Criteria

- [ ] MVP schema supports one active board per user while allowing future many-board model.
- [ ] Documentation is clear enough to implement Part 6 directly.
- [ ] User approves schema docs before moving forward.

## Part 6: Backend API

### Checklist

- [ ] Implement board read endpoint(s) for authenticated user context.
- [ ] Implement board update endpoint(s) with full-board JSON replacement for MVP.
- [ ] Validate request payload shape and reject invalid updates.
- [ ] Ensure DB auto-creates on first run if file is absent.
- [ ] Keep backend modules simple and narrowly scoped.

### Tests

- [ ] Unit: service/repository functions for read/write and validation.
- [ ] Integration: API endpoints interact with SQLite correctly.
- [ ] End-to-end: authenticated user updates board and reload returns persisted state.

### Success Criteria

- [ ] Backend provides reliable CRUD operations needed by frontend MVP.
- [ ] Data persists across server restarts.
- [ ] Invalid payloads return clear 4xx responses.

## Part 7: Frontend + Backend Integration

### Checklist

- [ ] Replace frontend in-memory board source with backend API calls.
- [ ] Load board on sign-in and render state from API.
- [ ] Persist card/column changes by calling backend update route.
- [ ] Add minimal loading and error states for network boundaries.
- [ ] Preserve current UX behavior where practical.

### Tests

- [ ] Unit: API client helpers and state update adapters.
- [ ] Integration: component tests with mocked backend responses.
- [ ] End-to-end: real container flow verifies persistent board edits across refresh.

### Success Criteria

- [ ] Board state is no longer ephemeral in browser memory.
- [ ] Refresh and restart preserve latest saved board state.
- [ ] Frontend behavior remains responsive and predictable.

## Part 8: AI Connectivity

### Checklist

- [ ] Add backend OpenRouter client wiring using `OPENROUTER_API_KEY` from `.env`.
- [ ] Configure model `openai/gpt-oss-120b`.
- [ ] Add a minimal backend route/service to test AI call plumbing.
- [ ] Implement deterministic connectivity probe prompt (`2+2`).
- [ ] Handle network/auth/provider errors with clear responses.

### Tests

- [ ] Unit: request builder and response parser behavior.
- [ ] Integration: mocked OpenRouter client success/failure paths.
- [ ] End-to-end: optional live connectivity check gated by env key presence.

### Success Criteria

- [ ] Backend can successfully call OpenRouter from containerized app.
- [ ] Probe route reliably returns expected response structure.
- [ ] Failure modes are visible and debuggable.

## Part 9: Structured AI Board Updates

### Checklist

- [ ] Define strict JSON schema for AI response payload:
- [ ] User-facing assistant message.
- [ ] Optional board update object (full board JSON for MVP).
- [ ] Include board JSON, user prompt, and conversation history in AI request context.
- [ ] Enforce strict backend schema validation before using AI output.
- [ ] Reject or surface schema-invalid responses without mutating persisted board.
- [ ] Persist valid board updates through existing backend board API/service layer.

### Tests

- [ ] Unit: schema validator accepts valid payloads and rejects invalid payloads.
- [ ] Integration: AI service with mocked model outputs (valid/invalid/no-update).
- [ ] End-to-end: user prompt can trigger valid board mutation and persisted reload.

### Success Criteria

- [ ] No non-conforming AI output can update board state.
- [ ] Valid AI updates are persisted and reflected in subsequent reads.
- [ ] Assistant response always returns safely, even when update is rejected.

## Part 10: Frontend AI Sidebar

### Checklist

- [ ] Add sidebar chat UI integrated into existing board layout.
- [ ] Support conversation history in UI and backend request payload.
- [ ] Send prompts to backend AI endpoint and render assistant replies.
- [ ] When backend returns a board update, refresh board state automatically.
- [ ] Keep visual design aligned with project color scheme and current UI language.

### Tests

- [ ] Unit: chat state reducers/helpers and message rendering behavior.
- [ ] Integration: component tests for send, loading, error, and update application flows.
- [ ] End-to-end: user chats, receives response, and sees board auto-refresh on AI update.

### Success Criteria

- [ ] Sidebar supports stable multi-message chat flow.
- [ ] AI-driven board updates appear without manual page reload.
- [ ] Full MVP scenario works in single-container local runtime.

## Execution Rules

- Complete parts in order.
- Do not begin Part 2 until the user approves this plan.
- Keep implementation minimal and focused on MVP requirements only.