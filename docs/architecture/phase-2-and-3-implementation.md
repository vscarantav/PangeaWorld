# Phase 2 and Phase 3 Implementation

> Part of the [PangeaWorld architecture documentation](../../app_architecture.md).

## Phase 2 Sprint 1 (Sep 9–13, 2026) — Multiplayer Foundation

> **Goal:** Deliver a secure four-player vertical slice in which two Presidents and two Company Executives can sign in from separate browsers, join the same game, see only their assigned role, submit authorized decisions, observe synchronized phase changes, and complete one authoritative round.

> **Sprint status (Sep 10, 2026): ✅ COMPLETE — 5/5 days complete.** This is the first five-day delivery slice of the broader 4–6 week Phase 2 roadmap. Trade proposals, treaties, sanctions, FMI lending, AI backfill, and the Drakmoor antagonist remain in later Phase 2 sprints.

### Progress Tracker

- [x] **Day 1:** Authentication and multiplayer data model
- [x] **Day 2:** Session lobby, invitations, and role assignment
- [x] **Day 3:** Authorization and decision-readiness workflow
- [x] **Day 4:** Deadlines and real-time synchronization
- [x] **Day 5:** Four-player acceptance test, hardening, and documentation

### Sprint Architecture Decisions

- Use email/password authentication for the local multiplayer MVP. Store only strong password hashes and use secure, HTTP-only session cookies; university SSO remains a deployment integration.
- Keep REST commands authoritative. WebSocket messages notify clients that session state changed; clients then reload canonical state through the REST API.
- Instructors create games and assign seats. A shareable join code admits players to a lobby but never grants a role by itself.
- Preserve SQLite for local development while keeping models and migrations compatible with the planned PostgreSQL deployment.
- Enforce authorization on the server for every read and write. Hiding a control in React is not an authorization boundary.

### ✅ Day 1 (Sep 9) — Authentication & Multiplayer Data Model — Complete

**Theme:** _"Give every action an authenticated owner."_

#### Backend

- [x] Extend the backwards-compatible schema bootstrap and create `User`, `AuthSession`, and `GameMembership` models without invalidating existing Phase 1 sessions.
- [x] Define instructor, President, and Company Executive membership roles and the entity-seat reference used by the Day 2 assignment workflow.
- [x] Add `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, and `GET /api/auth/me`.
- [x] Hash passwords with PBKDF2-SHA256, rotate session identifiers on login, set cookie security attributes, and never return password fields.
- [x] Add API tests for registration, duplicate email rejection, login failure/success, logout, expired sessions, and schema compatibility.

#### Day 1 Acceptance

- [x] Two users can create accounts, sign in independently, refresh the browser without losing their login, and sign out.
- [x] The full Phase 1 regression suite remains green after the schema extension (39 backend tests currently passing, including the added multiplayer coverage).

### ✅ Day 2 (Sep 10) — Session Lobby, Invitations & Role Assignment — Complete

**Theme:** _"Turn a local session into a game people can join."_

#### Backend

- [x] Make session creation instructor-only and generate a unique, revocable lobby join code.
- [x] Add lobby endpoints to join, list members/seats, assign or remove a member, and start the game.
- [x] Validate that assignments reference entities from the same session and reject conflicting President assignments.
- [x] Permit nation/company renaming only during Round 1, with length/character validation, moderation, uniqueness checks, and an audit record.

#### Frontend

- [x] Add register/login screens and a lobby view showing unassigned players and available seats.
- [x] Add instructor assignment controls and replace the unrestricted Phase 1 role switcher with the signed-in user's assigned seat.
- [x] Show clear empty, loading, validation, unauthorized, and join-code error states.

#### Day 2 Acceptance

- [x] Four accounts can join one game; the instructor can assign two Presidents and two Company Executives across two nations.
- [x] Each player lands on the correct dashboard after assignment and cannot select an unassigned role from the UI.

### ✅ Day 3 (Sep 11) — Server Authorization & Decision Readiness — Complete

**Theme:** _"A player can act only for the seat they own."_

#### Backend

- [x] Require authentication on session, nation, company, market, map, news, and decision routes; define the intentionally public lobby response separately.
- [x] Enforce membership, session boundary, role, entity ownership, and current-phase checks on every command.
- [x] Restrict phase advancement and map mutation to the instructor; freeze the initial map when the game starts except through future validated infrastructure commands.
- [x] Add per-seat decision status (`not_started`, `draft`, `submitted`, `auto_submitted`) and a session readiness summary without exposing private decision payloads.
- [x] Preserve idempotent decision resubmission during the correct open phase and lock decisions when that phase closes.
- [x] Add negative integration tests for cross-session access, horizontal privilege escalation, wrong-role submission, closed-phase submission, and non-instructor advancement.

#### Frontend

- [x] Show the player's submission status and an instructor readiness board with counts only, not other teams' secret decisions.
- [x] Disable closed-phase forms and explain whether a decision is editable, submitted, or locked.

#### Day 3 Acceptance

- [x] Direct API calls cannot let one player read or mutate another player's protected seat.
- [x] The instructor can tell who is ready while secret decisions remain private until results make them public.

### ✅ Day 4 (Sep 12) — Phase Deadlines & Real-Time Synchronization — Complete

**Theme:** _"Every browser sees the same clock and authoritative phase."_

#### Backend

- [x] Add timezone-aware `presidential_deadline_at` and `company_deadline_at` values plus an instructor-configurable accelerated mode for local testing.
- [x] Enforce deadlines server-side and make transition processing transactional and idempotent so a round cannot process twice.
- [x] Apply the existing conservative auto-decisions to seats that miss their deadline and record why/when each automatic submission occurred.
- [x] Add a session-scoped WebSocket channel for phase, readiness, assignment, and results notifications; send identifiers and event types, not secret payloads.
- [x] Add concurrency tests for simultaneous submissions, reconnects, and duplicate phase-transition attempts.

#### Frontend

- [x] Add a server-time-based countdown and live phase/readiness updates with reconnect and periodic-refresh fallback.
- [x] Refresh canonical session data after each notification and visibly label automatic submissions.

#### Day 4 Acceptance

- [x] A phase change made in one browser appears in the other three without a manual reload.
- [x] Late writes are rejected, missing decisions are filled automatically, and concurrent transition attempts yield one stored round result.

**Verified:** the browser acceptance test waits until all four player clients report a live socket, then requires the phase update within five seconds. WebSocket is the fast path; a two-second readiness-only REST fallback closes short reconnect windows without repeatedly transferring the persisted map. Backend tests cover late writes, recorded automatic submissions, simultaneous duplicate submissions, reconnects, duplicate transitions, and exactly one completed round result.

### ✅ Day 5 (Sep 13) — Four-Player Vertical Slice & Hardening — Complete

**Theme:** _"Prove the multiplayer loop from four independent clients."_

#### End-to-End Scenario

- [x] Instructor creates a game, shares the join code, assigns four players, and starts the session.
- [x] Both Presidents submit macro decisions during the Presidential phase; both Company Executives remain unable to submit early.
- [x] The Company phase opens and both executives submit pricing, production, R&D, and sourcing decisions.
- [x] One test seat intentionally misses a deadline and receives the recorded conservative auto-decision.
- [x] The engine processes exactly once; all four clients receive the update and see consistent Round 1 results and news.
- [x] Refresh and sign-out/sign-in tests restore the same membership, session, role, phase, and persisted map snapshot.

#### Quality Gate

- [x] Backend authentication, authorization, deadline, concurrency, and four-player API tests pass.
- [x] Existing Phase 1 backend and deterministic map tests pass with no regressions.
- [x] Frontend lint and production build pass.
- [x] `RUNNING.md` documents account creation, instructor setup, four-client testing, accelerated deadlines, and recovery from a disconnected client.
- [x] Security review confirms no password leakage, cross-session access, secret-decision exposure, or client-authoritative phase transition.

**Verified (Sep 10, 2026):** 39 backend tests and 3 deterministic frontend map tests pass; frontend lint completes without errors; the production build succeeds; and the isolated-Chrome four-client acceptance test passes. The browser path covers lobby setup, role/phase enforcement, complete President and Executive submissions, live phase propagation, one authoritative round result, identical player-visible results/news, sign-out/sign-in, refresh, and canonical React map restoration. The four-player API path separately exercises an expired deadline and confirms exactly one recorded automatic decision and one completed round.

**Security review:** Authentication responses exclude password and hash fields; protected REST routes reject unauthenticated, cross-session, wrong-role, and wrong-entity access; readiness and WebSocket messages expose status/identifiers but not private decision payloads; guest and non-member sockets close with authorization errors; and only the instructor's authenticated REST command can advance the canonical server phase.

### Definition of Done

The sprint is complete only when every Progress Tracker item is checked and the four-player scenario passes from separate browser sessions. A working UI without server authorization, or working APIs without the four-client acceptance test, does not count as complete.

### Explicitly Deferred to Later Phase 2 Sprints

- [ ] Bilateral trade proposals, acceptance/rejection, and negotiated contract terms
- [ ] Treaty and public/secret diplomacy workflows
- [ ] Sanctions proposals, voting, enforcement, and lifting
- [ ] FMI quotas, lending products, conditionality, repayment, and default
- [ ] General AI seat backfill and mid-game human takeover
- [x] Drakmoor's deterministic military timeline and instructor behavior override (delivered in the Phase 3 closure ruleset)
- [ ] Production deployment with PostgreSQL, Redis, university SSO, TLS, email verification, and password recovery

---

## Phase 3 Sprint 1 — Military, Events & News Vertical Slice

> **Status:** ✅ Complete — Day 5/5 complete. This is a five-day delivery slice of the broader Phase 3 roadmap, not completion of every military or event feature described above.

> **Goal:** Deliver one secure, instructor-observable conflict-and-event round in the existing four-player game: an instructor can inject a validated event, each President can make authorized military-posture and emergency-preparedness decisions, the server resolves the consequences once during processing, and every player receives the same persisted result and Pangea Times coverage.

### Sprint Scope and Guardrails

- Keep the existing round authority model: clients submit intent; the backend validates, persists, and resolves it exactly once during the processing transition.
- Start with **posture and readiness**, not player-directed attacks: each nation selects a bounded military allocation and posture (`defend`, `patrol`, or `reconnaissance`). Direct attacks, multi-battle engagements, retreats, blockades, and Drakmoor's autonomous war behavior remain later work.
- Every military allocation must reduce the President's available budget or investment capacity and expose that trade-off before submission and in the round result.
- Presidents can invest a bounded portion of their budget in a national **emergency-preparedness fund**. When a natural-disaster event affects a nation, its affected companies may draw from the remaining fund under transparent eligibility and allocation rules.
- If the President did not invest enough in preparedness, affected companies must finance recovery through expensive private emergency funds. The resolver records the higher company cost and the resulting public consequences: lower government approval rating and reduced **GDP** (*Gross Domestic Product*, or *Produto Interno Bruto* in Portuguese).
- The President dashboard must show the immediate opportunity cost of preparedness against civilian investment, while the round result must show the avoided or incurred private-recovery cost, approval effect, and GDP effect.
- Events must be deterministic from the persisted session/round inputs. Instructor-injected events use a validated, allow-listed event catalog; free-form scenario execution is out of scope.
- Event and military results are session-scoped, immutable once the round completes, and visible through REST as the canonical source. WebSockets carry only change notifications.
- Preserve role privacy: players see their own submitted posture before processing; they do not see another nation's private choice unless the published event/result explicitly reveals it.
- Reuse the canonical React `GameMap`; add only a small, snapshot-backed overlay or indicator if needed. `frontend/public/map_prototype.html` remains a design reference, never the running game surface.

### Progress Tracker

- [x] **Day 1 — Domain contract and migrations:** Added typed military posture and emergency-preparedness inputs; event, recovery-funding, and immutable effect records; database bounds; a session-scoped event-target validator; and cross-session/validation regression tests. Verified with 43 backend tests passing.
- [x] **Day 2 — Authoritative APIs and President UI:** Added protected presidential readiness submission, the compact President military/preparedness panel with cost, remaining capacity, and civilian opportunity cost, plus instructor-only event catalog and injection commands. Regression coverage rejects unauthenticated, wrong-role, invalid-posture, out-of-phase, invalid-event, and duplicate-event requests. Verified with 45 backend tests, clean frontend lint, and a successful production build.
- [x] **Day 3 — Resolver and event effects:** Added a pure deterministic disaster resolver with explicit tuning constants, posture/readiness mitigation, public-fund-first allocation, and deterministic company recovery splits. Processing now commits military/preparedness spending, carries unspent public funds, applies private financing costs, approval/GDP effects, and persists immutable public/private effects plus reproducibility keys. A round accepts at most one Phase 3 event. Repeatability and exactly-once coverage pass with 47 backend tests.
- [x] **Day 4 — Results, news, and real-time UX:** Published sanitized, immutable event results with deterministic Pangea Times payloads; rendered canonical public results in the President dashboard and summaries in Pangea Times; retained REST hydration on session notifications and stale-response protection. Added regression coverage for identical cross-role result payloads and privacy. Verified with 48 backend tests, frontend unit tests, clean lint, and a successful production build.
- [x] **Day 5 — Eight-seat stress rehearsal, balancing, and handoff:** Exercised the closest available fixture: an eight-nation session with four isolated browser clients, remaining seats vacant, and a Phase 3 coastal-storm injection. The affected President saved preparedness and ordinary policy in the same round; all clients received identical sanitized results/news after processing, sign-out/sign-in, and reload. Verified with 48 backend tests, 3 frontend unit tests, lint, production build, and the Playwright rehearsal (1 passed; 96.5 seconds).

### Acceptance Criteria

- [x] A President can submit exactly one valid military posture for the active round; it is rejected outside the permitted phase, after deadline, or for another entity/session.
- [x] A President can submit a bounded emergency-preparedness investment. A natural-disaster resolution uses available eligible public funds before applying documented private-recovery costs, approval-rating loss, and GDP loss for any uncovered impact.
- [x] An instructor can inject one catalog event for a permitted target round; duplicate or invalid injections are rejected and audited.
- [x] Processing resolves the same persisted inputs to the same effects and article payloads on repeat/reconnect; a duplicate advance cannot apply effects twice.
- [x] The completed-round result identifies the event, public effects, economic opportunity cost, and any intentionally disclosed posture information without exposing private pre-processing decisions.
- [x] Four isolated browser clients receive the phase/result update, view identical public results/news, and retain those results after sign-out/sign-in and reload.
- [x] Backend regression tests, frontend lint/build, deterministic resolver tests, and the browser acceptance scenario pass before any tracker item is marked complete.

### Explicitly Deferred Beyond Phase 3 Sprint 1

- [x] Direct attacks, abstract strategic territory control, blockade effects, multiple engagement rounds, retreat, and military unit inventories (delivered by Sprint 2 plus the closure sprint).
- [x] Drakmoor's deterministic aggression timeline and instructor behavior override. General AI seat backfill remains Phase 4 scope.
- [x] Reactive events, labeled misinformation/opinion exercises, Gemini-written articles with fallback, and bounded instructor scenario authoring.
- [ ] Phase 2 trade, treaty, sanctions, FMI, and production-deployment work listed above.

### Sprint Verification Commands

```powershell
# Backend regression and multiplayer tests
Set-Location backend
.\.venv\Scripts\python.exe -m pytest tests -v

# Frontend regression suite
Set-Location ../frontend
npm test
npm run lint
npm run build

# Real browser acceptance path (starts isolated local servers and database)
npm run test:e2e
```

> [!IMPORTANT]
> When work is verified, change its checkbox from `[ ]` to `[x]` immediately. Mark a day complete in the Progress Tracker only after all of that day's acceptance checks pass; update the sprint status count at the same time.

---

## Phase 3 Sprint 2 — Direct Conflict Foundation

> **Status:** ✅ Complete as the bounded Sprint 2 delivery. Later Phase 3 closure work is recorded separately below.

> **Goal:** Add one bounded, authoritative direct-conflict decision to the four-player game. A President can procure named units and submit at most one attack against another nation in the same session; processing resolves the clash exactly once from persisted inputs and publishes a privacy-safe result and Pangea Times article to every player.

### Sprint Scope and Guardrails

- Keep Sprint 1 readiness and disaster recovery intact. Procurement is an additional presidential commitment, counted against the same treasury alongside civilian spending, readiness, and preparedness.
- Unit inventory is limited to `infantry`, `navy`, and `air_force`, with fixed visible procurement costs and public aggregate inventory. A submitted deployment cannot exceed inventory, and newly procured units arrive after that round's operation.
- The only executable operation in this slice is `attack`. Target validation is session-scoped, a nation cannot target itself, and each President still has one canonical decision per round.
- Combat uses a pure seeded resolver: attack and defence indices set one to five dice; equal scores favor the higher index. The attacker's stable nation ID defines the documented order for multiple attacks in the same processing phase.
- Persist only intentional public combat disclosures: outcome, indices, and aggregate losses. Planned deployment, rolls, and pre-processing decisions remain private.
- This slice has no territory capture, blockade route effects, retreat, multi-engagement battles, intelligence operations, Drakmoor autonomy, or trade disruption. Those remain later Phase 3 work.

### Progress Tracker

- [x] **Day 1 — Unit and order contract:** Typed unit allocations and attack orders, backwards-compatible national inventory migration, fixed procurement pricing, session/self/inventory validators, and regression tests.
- [x] **Day 2 — Authorized command and President UI:** Extended the canonical readiness command and Intel & Military panel with inventory, procurement cost, target selection, deployment bounds, and civilian opportunity cost. Verified by frontend lint and production build.
- [x] **Day 3 — Deterministic resolver:** Resolve each accepted attack once during processing, return surviving units, persist a public immutable effect, and prove repeatability and duplicate-processing protection.
- [x] **Day 4 — Results and news:** Publish sanitized cross-role combat results and a deterministic Pangea Times article without leaking deployments or rolls.
- [x] **Day 5 — Multiplayer rehearsal and balancing:** Exercised two presidents attacking each other in one round with a concurrent coastal-storm event. All four isolated roles received the same sanitized results and Pangea Times articles, and the President retained the canonical state after sign-out/sign-in and reload. Confirmed fixed procurement pricing and deterministic losses; verified with 53 backend tests, 3 frontend unit tests, clean lint, a production build, and the Playwright rehearsal (1 passed).

### Acceptance Criteria

- [x] A President cannot target another session, target itself, deploy unavailable units, or exceed the shared treasury commitment.
- [x] Procurement, attacks, casualties, and public effects are committed exactly once during processing and resolve identically from identical persisted state.
- [x] All assigned roles receive the same public outcome/news after processing and after reload, while deployment counts and dice remain undisclosed.
- [x] Existing Sprint 1 readiness, disaster, privacy, authorization, and real-time behavior remains regression-tested.

---

### Sprint 2 audit and continuation — September 10, 2026

- [x] Reproduced and repaired a processing failure when an earlier clash destroys units committed to a later attack. Preserve stable nation-ID ordering: cap each later deployment by surviving inventory; publish `attack_cancelled` when no committed units survive. Validate original orders against pre-combat inventory so invalid orders are still rejected. Procurement remains unavailable until all operations finish.
- [x] Explain casualty-driven reduction/cancellation before submission and show cancelled operations in public news without disclosing deployment counts or dice.
- [x] Add regression coverage for partial and total prior losses, conservation of units, sanitized effects, cancellation news, and duplicate processing rejection.
- [x] Complete the mandatory opportunity-cost decision loop through the Phase 3 closure ruleset: persist considered feasible alternatives, the selected next-best foregone alternative, rationale, and submission assumptions; surface marginal comparisons and post-round feedback; and provide instructor evidence summaries plus the Phase 4 advisor prompt contract.

Verification: 55 backend tests, 3 deterministic map tests, frontend lint, and production build pass. Backend tests must run from `backend` using `.venv/bin/python -m pytest tests -q`. The isolated four-player Chrome rehearsal also passes (1 test, 1.7 minutes), covering two direct attacks, shared results, and reload.

---

## Phase 3 closure sprint — September 10, 2026

> **Status:** ✅ COMPLETE. New games use the versioned `phase3-closure-v1` ruleset. Existing games retain `legacy-v1` behavior. Live Gemini prose requires backend credentials; provider-independent fallback news remains available without them.

- [x] Opportunity-cost comparisons, authoritative constraints, immutable reasoning receipts, private feedback, instructor evidence scorecard, and the Phase 4 advisor prompt adapter.
- [x] Multiple engagements, retreat orders, abstract strategic territory control, blockade and intelligence operations, sustained readiness with diminishing returns, and documented war consequences.
- [x] Seeded seven-round schedule (3 major and 11 minor events), CPI-triggered unrest, five scenario categories, and bounded instructor controls.
- [x] Persisted Gemini news using a server-side key, factual fallback, CPI reporting, opinion labeling, and source-verification exercises. Success/failure transports are tested; live credentials are external configuration.
- [x] Instructor-controlled scripted Drakmoor behavior; reserved Drakmoor seats; eight-nation automatic and seven-human-nation/Drakmoor seven-round rehearsals; role privacy regression checks.
- [x] Setup and implementation handoff, backward-compatible local SQLite migration, fresh full verification, and explicit external configuration.

**Final verification (September 10, 2026):** 70 backend tests and 3 deterministic frontend map tests pass; frontend lint and production build succeed; and the isolated four-browser Chrome rehearsal passes (1 test, 1.4 minutes). The build reports one non-blocking bundle-size warning at approximately 510 kB. Live Gemini credentials are not configured in this workspace, so mocked provider success/failure and the provider-independent factual fallback were verified instead.

**Phase 4 readiness:** ready to start the major [Phase 4 AI Integration & Analytics roadmap](./phase-4-and-release.md). The separate [post-launch map roadmap](./post-launch-map-roadmap.md) also contains internally numbered phases; its “Phase 4” means road and city construction and is not the next active product phase.

---
