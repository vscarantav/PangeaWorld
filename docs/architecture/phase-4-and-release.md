# Phase 4 and Release Readiness

> Part of the [PangeaWorld architecture documentation](../../app_architecture.md).

## Phase 4 Sprint 1 (Sep 11–14, 2026) — AI Integration & Analytics

> **Goal:** Deliver a per-user Gemini AI advisor with persistent chat history, AI-usage logging and grading, an instructor analytics dashboard, post-game debrief tools, and general AI seat backfill — completing the Phase 4 roadmap items and making the product classroom-ready.

> **Sprint status (Sep 14, 2026): ✅ COMPLETE — 4/4 days complete.** The complete seven-round mixed human/AI classroom path, post-game debrief, advisor/analytics workflow, and mid-game AI-seat takeover are covered by automated acceptance tests. Production hosting and live Gemini credential validation remain release-readiness work rather than Phase 4 scope.

> **Prerequisites:** The Phase 3 closure sprint delivered the Phase 4 advisor prompt adapter, the opportunity-cost decision-review contract, the deterministic Drakmoor behavior engine, and the Gemini newsroom integration with fallback. This sprint builds the interactive, per-user advisory layer and instructor analytics on top of those foundations.

### Sprint Scope and Guardrails

- The Gemini advisor proxies through the backend. The client never holds API keys or sends prompts directly to Gemini.
- The advisor is strictly partitioned from Confidential Intel Vaults. It can access only the Global Event Ledger (public decisions, events, news, diplomacy, and Pangea Assembly messages) plus the requesting user's own game data. It must not reveal other players' secret decisions, private deployments, or unreleased intelligence.
- The advisor uses a Socratic method: it guides thinking, asks clarifying questions, and surfaces trade-offs. It must not prescribe optimal solutions or produce direct "do X" commands.
- AI-usage logging is immutable. Every prompt, response, timestamp, token count, and session context is persisted for instructor review and grading.
- AI seat backfill reuses the existing conservative auto-decision engine for unfilled seats. A human can take over a backfilled seat mid-game; the AI ceases control immediately upon assignment.
- Instructor analytics read from persisted, immutable round data and AI-usage logs. They do not modify game state.
- All new endpoints require authentication and role-based authorization. Instructor-only routes reject non-instructor access.

### Progress Tracker

- [x] **Day 1:** Gemini advisor backend — per-user chat service, system prompt engineering, guardrails, and persistent conversation history
- [x] **Day 2:** Frontend AI chat panel, real-time streaming, and AI-usage logging pipeline
- [x] **Day 3:** Instructor analytics dashboard and AI-usage grading
- [x] **Day 4:** Post-game debrief tools, AI seat backfill, end-to-end verification, and hardening

### Day 1 (Sep 11) — Gemini Advisor Backend

**Theme:** _"Give every player a private, context-aware AI strategist that teaches without giving answers."_

#### Backend

- [x] `backend/engines/advisor.py` — Gemini advisor service
  - Per-user chat session management with persistent conversation history (stored in SQLite, keyed by user + game session + role)
  - System prompt template engine with role-specific prompts:
    - **Company Executive advisor**: business strategy, supply chain optimization, finance, pricing, R&D trade-offs, market share analysis
    - **President advisor**: macroeconomics, geopolitics, military strategy, infrastructure planning, diplomacy, fiscal policy
  - Global Event Ledger query interface: the advisor can retrieve public decisions, round results, news articles, Pangea Assembly messages, market data, and event history for the current game session
  - User-context injection: the advisor receives the requesting player's current financials, decisions, results, and opportunity-cost feedback from prior rounds
  - Guardrail enforcement layer:
    - Block queries that attempt to extract other players' private data
    - Prevent direct optimal-solution prescriptions (Socratic method enforcement via system prompt)
    - Redact any Confidential Intel Vault references from the context window
    - Rate limiting per user per round (configurable, default 20 prompts per phase)

- [x] `backend/models/ai_chat.py` — AI conversation models
  - `AIConversation` — id, user_id, session_id, role, created_at, message_count
  - `AIMessage` — id, conversation_id, role (user/assistant/system), content, token_count, timestamp, round_number, phase
  - `AIUsageLog` — id, user_id, session_id, round_number, prompt_text, response_text, token_count, latency_ms, guardrail_flags, timestamp

- [x] `backend/routes/advisor.py` — AI advisor API endpoints
  - `POST /api/sessions/{id}/advisor/chat` — send a prompt, receive a streamed Gemini response
  - `GET /api/sessions/{id}/advisor/history` — retrieve the user's conversation history for the current session
  - `DELETE /api/sessions/{id}/advisor/history` — clear conversation history (user-initiated, with audit log)
  - All routes require authentication and enforce role-entity ownership

- [x] Backend tests for advisor service:
  - Guardrail rejection of cross-player data queries
  - Rate limiting enforcement
  - Conversation persistence and retrieval
  - System prompt correctness per role
  - Graceful fallback when Gemini provider is unavailable (return a structured "advisor unavailable" message)
  - Authorization rejection for unauthenticated, wrong-session, and wrong-role requests

#### Day 1 Acceptance

- [x] A Company Executive and a President can each initiate an advisory conversation; their histories are isolated and persist across browser sessions.
- [x] The advisor contextualizes responses using the player's live game data and public Global Event Ledger.
- [x] Guardrails reject attempts to extract private data or bypass Socratic guidance.
- [x] Provider unavailability returns a graceful, user-friendly fallback message.

### Day 2 (Sep 12) — Frontend AI Chat Panel & Usage Logging

**Theme:** _"Every student gets a polished, embedded AI advisor — and every interaction is recorded."_

#### Frontend

- [x] `frontend/src/components/AIAdvisor/ChatPanel.jsx` — embedded AI chat panel
  - Persistent sidebar or modal panel accessible from both President and Executive dashboards
  - Message history display with user/assistant message bubbles, timestamps, and round context
  - Streamed response rendering (tokens appear progressively as the Gemini response streams)
  - Suggested starter prompts based on current game phase and role (e.g., "What are the trade-offs of raising tariffs this round?", "Should I prioritize R&D or marketing?")
  - Rate-limit indicator showing remaining prompts for the current phase
  - Conversation clear/reset control with confirmation dialog
  - Loading, error, and provider-unavailable states with clear messaging
  - Mobile-responsive layout

- [x] `frontend/src/components/AIAdvisor/ContextBadge.jsx` — visual indicator of what context the advisor is using
  - Shows "Using: Round 3 data, your financials, public market data" to build trust and transparency
  - Highlights when the advisor is working with limited context (e.g., Round 1 with minimal history)

#### Backend — Usage Logging Pipeline

- [x] `backend/engines/ai_logger.py` — immutable AI-usage logging
  - Every prompt/response pair is logged with: user_id, session_id, round_number, phase, prompt_text, response_text, input_token_count, output_token_count, total_token_count, latency_ms, guardrail_flags (any triggered), timestamp
  - Logs are append-only and immutable — no deletion or modification permitted
  - Batch write for efficiency; flush on phase transition

- [x] `backend/routes/ai_logs.py` — instructor-only AI usage endpoints
  - `GET /api/sessions/{id}/ai-usage` — aggregated AI usage statistics per student/team
  - `GET /api/sessions/{id}/ai-usage/{user_id}` — detailed conversation log for a specific student
  - Both routes require instructor role authorization

- [x] Integration tests for usage logging:
  - Log immutability (reject deletion/modification attempts)
  - Correct token counting and latency recording
  - Instructor-only access enforcement
  - Aggregation correctness across rounds

#### Day 2 Acceptance

- [x] The AI advisor panel is embedded and functional in both President and Executive dashboards with streamed responses.
- [x] Conversation history persists after page refresh, sign-out/sign-in, and across rounds.
- [x] Every AI interaction is logged immutably with full metadata.
- [x] Instructors can retrieve per-student AI usage logs; non-instructors are rejected.

### Day 3 (Sep 13) — Instructor Analytics Dashboard & AI Grading

**Theme:** _"Give instructors the visibility they need to grade, balance, and intervene."_

#### Frontend

- [x] `frontend/src/components/InstructorDashboard/AnalyticsPanel.jsx` — instructor analytics dashboard
  - **Engagement Metrics** per student/team:
    - Decisions submitted vs. auto-decided (per round, cumulative)
    - Login frequency and session duration
    - AI advisor usage (prompt count, token consumption, rounds used vs. not used)
    - Pangea Assembly participation (messages posted, resolutions proposed)
  - **Decision Quality Tracking**:
    - Opportunity-cost reasoning quality across rounds (from the immutable reasoning receipts)
    - Trend lines: did the team's decision rationale improve over the 7 rounds?
    - Comparison of stated alternatives vs. realized outcomes
  - **Game Balance Monitoring**:
    - GDP, military index, and market-share leaderboards across all nations
    - Drakmoor threat level and engagement history
    - Early warning indicators for runaway leaders or disengaged teams
  - **AI Usage Grading Module**:
    - Per-student AI usage summary: total prompts, quality of prompts (length, specificity, follow-up depth), diversity of topics queried
    - Flagged interactions: guardrail triggers, repeated low-effort prompts, copy-paste behavior
    - Configurable rubric: instructors can weight prompt quality, usage frequency, and evidence of critical thinking
    - Suggested grade component (instructor can override)
  - **Export Functionality**:
    - CSV/JSON export of all analytics, AI usage logs, decision receipts, and scores
    - Per-round and cumulative report generation
    - Print-friendly summary for each team

#### Backend

- [x] `backend/routes/analytics.py` — instructor analytics API
  - `GET /api/sessions/{id}/analytics/engagement` — per-student engagement metrics
  - `GET /api/sessions/{id}/analytics/decisions` — decision quality and opportunity-cost reasoning summaries
  - `GET /api/sessions/{id}/analytics/balance` — game balance indicators
  - `GET /api/sessions/{id}/analytics/ai-grading` — AI usage grading with configurable rubric
  - `GET /api/sessions/{id}/analytics/export` — full data export (CSV or JSON, query-param selectable)
  - All routes require instructor role authorization

- [x] `backend/engines/grading.py` — AI-usage grading engine
  - Analyze prompt quality: length, specificity, follow-up chains, topic diversity
  - Detect low-effort patterns: single-word prompts, repeated identical queries, copy-paste detection
  - Apply configurable rubric weights and produce a suggested score per student
  - Flag notable interactions for instructor review

- [x] Backend tests for analytics and grading:
  - Engagement metric accuracy against known test data
  - Grading engine rubric application and edge cases
  - Export format correctness (CSV and JSON)
  - Instructor-only authorization enforcement

#### Day 3 Acceptance

- [x] The instructor analytics dashboard displays engagement, decision quality, game balance, and AI grading data for all students in the session.
- [x] The AI grading module produces configurable, rubric-based scores with flagged interactions.
- [x] Full data export works in both CSV and JSON formats.
- [x] All analytics routes reject non-instructor access.

### Day 4 (Sep 14) — Debrief Tools, AI Backfill & Hardening

**Theme:** _"Close the learning loop and prove the full AI layer end-to-end."_

#### Backend — Post-Game Debrief Tools

- [x] `backend/engines/debrief.py` — post-game analysis engine
  - **Historical Playback**: reconstruct the complete game timeline from the immutable decision ledger, round results, and event log; serve a round-by-round or chronological playback feed
  - **"What-If" Analysis**: for a given round and decision, re-run the deterministic engine with the recorded next-best foregone alternative and compare outcomes; clearly label the counterfactual as an estimate, not a historical fact
  - **Real-World Connections**: map game events to a curated catalog of real-world parallels (e.g., "Your nation experienced hyperinflation — here's what happened in Venezuela 2016–2020"); catalog is instructor-extensible

- [x] `backend/routes/debrief.py` — debrief API endpoints
  - `GET /api/sessions/{id}/debrief/timeline` — full game timeline playback data
  - `POST /api/sessions/{id}/debrief/what-if` — submit a decision + alternative for counterfactual comparison
  - `GET /api/sessions/{id}/debrief/connections` — real-world event parallels for the session's history
  - Timeline and connections are available to all session members post-game; what-if is available to instructors and the decision's owner

#### Backend — AI Seat Backfill

- [x] `backend/engines/ai_backfill.py` — general AI seat management
  - Identify unfilled seats (no human assigned) at game start and mid-game
  - Generate conservative auto-decisions using the existing engine for each unfilled seat, every round
  - When an instructor assigns a human to a previously AI-backfilled seat, immediately cease AI control; the human inherits the current nation/company state
  - Backfilled seats are visually distinguished in the lobby and dashboards (labeled "AI-controlled")
  - AI backfill decisions are logged with the same immutability as human decisions for instructor review

- [x] `backend/routes/backfill.py` — backfill management endpoints
  - `GET /api/sessions/{id}/backfill/status` — list of AI-controlled vs. human-controlled seats
  - `POST /api/sessions/{id}/backfill/{seat_id}/takeover` — instructor assigns a human to an AI seat (mid-game handover)
  - Instructor-only authorization

#### Frontend — Debrief & Backfill UI

- [x] `frontend/src/components/Debrief/DebriefPanel.jsx` — post-game timeline playback
  - Round-by-round chronological view with expandable decision details, events, and results
  - Visual indicators for major turning points (wars, disasters, market shocks)

- [x] `frontend/src/components/Debrief/DebriefPanel.jsx` — counterfactual analysis
  - Select a past decision, view the recorded alternative, and compare projected vs. actual outcomes
  - Clear labeling: "Estimated counterfactual — not a guaranteed outcome"

- [x] `frontend/src/components/Debrief/DebriefPanel.jsx` — real-world connections
  - Display curated parallels with brief descriptions and optional links to further reading

- [x] Lobby and dashboard updates for AI backfill:
  - AI-controlled seats display a distinct badge/icon
  - Instructor can initiate mid-game takeover from the lobby

#### End-to-End Verification

- [x] Full seven-round game with four human players + AI backfill for remaining seats:
  - AI advisor conversations for both President and Executive roles across multiple rounds
  - Guardrail enforcement verified (cross-player data blocked, Socratic method maintained)
  - AI usage logged and visible in instructor analytics
  - AI grading rubric produces scores for all human players
  - Backfilled seats submit conservative decisions each round; one seat is handed over to a human mid-game
  - Post-game debrief timeline, what-if, and real-world connections functional
  - Export produces valid CSV and JSON
- [x] Backend regression: all existing Phase 1–3 tests pass with no regressions
- [x] Frontend lint and production build pass
- [x] Browser acceptance test: four isolated clients complete all seven rounds with AI advisor usage, instructor analytics, AI backfill for vacant seats, reload recovery, and player/instructor debrief tools after game completion

**Final verification (Sep 14, 2026):** 86 backend tests and 3 deterministic frontend map tests pass; frontend lint completes without errors; the production build succeeds; and the isolated four-browser Phase 4 rehearsal passes (1 test, 2.3 minutes). The browser path covers all seven rounds, reviewed human decisions, conservative AI backfill for vacant seats, advisor use by both roles across multiple rounds, instructor analytics, identical authoritative results, sign-out/sign-in, map restoration, transient phase-advance reconciliation, and player/instructor post-game debrief with a labeled What-If estimate. Backend coverage separately verifies guardrails, immutable AI logs, exports, provider fallback, full AI grading, and mid-game human takeover of an AI-controlled seat.

#### Day 4 Acceptance

- [x] The post-game debrief timeline, what-if analysis, and real-world connections are functional and accessible to all session members.
- [x] AI seat backfill covers unfilled seats; mid-game human takeover works without data loss.
- [x] The full Phase 4 layer (advisor, logging, grading, analytics, debrief, backfill) is regression-tested end-to-end.
- [x] All existing Phase 1–3 tests, frontend lint, and production build pass.

### Sprint Verification Commands

```bash
# Backend regression and Phase 4 tests
cd backend
.venv/bin/python -m pytest tests -v

# Frontend regression suite
cd ../frontend
npm test
npm run lint
npm run build

# Real browser acceptance path
npm run test:e2e
```

### Definition of Done

The sprint is complete only when every Progress Tracker item is checked, the instructor analytics dashboard renders live data, the AI advisor is functional in both dashboards, AI usage is graded, the debrief tools work post-game, backfilled seats submit decisions autonomously, and the browser acceptance test passes from separate sessions.

### Release Readiness — Render, Neon, Keep-Alive, and Gemini

> **Status (Sep 16, 2026): implementation-ready; external activation and public smoke validation pending.** Repository-owned deployment configuration, the three-level account hierarchy, the role-aware dashboard, and the Neon migration are complete and regression-tested. Production completion still requires successful deployment and validation against the owner's Render, Neon, and Gemini services.

- [x] Add a Render Blueprint for the Vite Static Site, single-instance FastAPI Web Service, pre-deploy database migration, health check, and scheduled keep-alive job.
- [x] Add Neon-compatible Psycopg support and keep SQLite isolated to local development and tests.
- [x] Add an Alembic Phase 4 schema baseline and verify it upgrades and stamps a fresh disposable database.
- [x] Prevent production startup with SQLite, non-TLS PostgreSQL, insecure cookies, HTTP CORS origins, or missing Gemini configuration.
- [x] Add the read-only `GET /healthz` database readiness endpoint and a keep-alive client that accepts only an HTTPS `/healthz` URL.
- [x] Document deployment order, required secrets, initial single-instance WebSocket boundary, smoke checks, and operating constraints in `DEPLOYMENT.md`.
- [ ] Create the Neon project, copy its pooled TLS connection string into Render, and run the Alembic migration against the real database.
- [ ] Create/select the Gemini API key and advisor/news model IDs, store them on the Render backend, and verify live quota, latency, fallback, privacy, and cost behavior.
- [ ] Connect the repository to Render, supply all unsynchronized Blueprint variables, and deploy the API, static site, and cron service.
- [ ] Run the public-URL smoke test: health, secure authentication cookie, lobby, WebSocket, reviewed President/Executive decisions, Gemini advisor/history, analytics, and keep-alive logs.
- [ ] Confirm expected concurrent enrollment before increasing API instances; shared pub/sub is required before horizontal scaling.

**Repository verification (Sep 16, 2026):** 96 backend tests and 3 deterministic frontend tests pass; frontend lint completes with pre-existing non-blocking React advisory warnings; the production frontend build succeeds; a fresh database upgrades through `20260916_0002 (head)`; and the isolated seven-round four-browser Phase 4 rehearsal passes in 2.4 minutes. The production bundle reports a non-blocking main-chunk warning at approximately 550 kB.

### Explicitly Deferred Beyond Phase 4 Sprint 1

- [ ] Render production deployment: Static Site frontend, FastAPI Web Service, Neon PostgreSQL migration, secure cookies/TLS, production CORS, health endpoint, and keep-alive cron/monitor
- [ ] Live Gemini credential, quota, latency, fallback, privacy, and cost validation on the Render backend
- [ ] University SSO integration, email verification, and password recovery
- [ ] Full Pangea Assembly (UN-style forum) with live chat, resolutions, and voting
- [ ] FMI portal with lending products, conditionality, and repayment workflows
- [ ] Bilateral trade proposals, treaties, and sanctions enforcement
- [ ] Advanced logistics construction (sea-lane/airway path records, chokepoint blockades, construction timeframes, wartime destruction)
- [ ] Post-launch map improvement roadmap (3D rendering, road/city construction tools)

> [!IMPORTANT]
> When work is verified, change its checkbox from `[ ]` to `[x]` immediately. Mark a day complete in the Progress Tracker only after all of that day's acceptance checks pass; update the sprint status count at the same time.

---
