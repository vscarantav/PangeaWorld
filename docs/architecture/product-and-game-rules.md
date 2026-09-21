# PangeaWorld — Educational Simulation Game Development Plan

> Part of the [PangeaWorld architecture documentation](../../app_architecture.md).


## Vision & Overview

**PangeaWorld** is a round-based, multiplayer educational simulation that blends the territorial strategy of RISK, the resource economy of CATAN, and the business simulation depth of CAPSIM. Set in a fictitious world of **8 nations** (7 player-controlled + 1 AI-controlled), students assume roles as either **National Presidents** or **Company Executives**, making decisions that ripple across military, economic, and diplomatic systems. The 8th nation, **Drakmoor**, is fully AI-controlled — a marginalized, sanctioned, militarily powerful state that will provoke conflict in the early game, forcing students to deal with the reality that war can happen even when no one wants it. Each user is assisted by an **AI advisor** (Gemini), teaching them to critically evaluate AI-assisted decision-making.

> [!IMPORTANT]
> This is a large-scale project. The plan is structured in **4 major phases** to deliver a working MVP first, then layer in complexity. Each phase is self-contained and playable.

---

## User Review Required

### Naming & Theming
- **"PangeaWorld"** is a working title — do you have a preferred name?
- Should the visual theme lean toward a **stylized/illustrated map** aesthetic (Risk-like), a **clean data-dashboard** feel (Bloomberg terminal), or a **hybrid** with both?

### Deployment & Infrastructure
- How many concurrent students do you anticipate? (This impacts architecture decisions — 50 students vs. 500 is very different)
- Will instructors need a **Game Master (GM) panel** to inject events, pause rounds, and override decisions?

### AI Integration ✅
- **Guardrails**: The Gemini AI advisor will act dynamically based on the game's context. Its advice and analysis will be strictly grounded in the **Pangea Assembly (UN forum) discussions** and the **Pangea Times newsletters**, ensuring it doesn't "hallucinate" external optimal strategies but instead helps students navigate the actual evolving narrative of their specific game.
- **Grading & Logging**: AI usage will be logged and graded as a core learning outcome. Instructors will have visibility into the quantity and quality of student prompts to assess how well they are learning to leverage AI for decision-making.

### Authentication & Access

- **Current authentication:** Secure email/password authentication with HTTP-only cookie sessions is implemented. University SSO, email verification, password recovery, and forced first-login password changes remain future identity work.
- **Account hierarchy:** Every user has exactly one installation-level `account_type`: `admin`, `professor`, or `student`. The hierarchy is authoritative on the server and is independent of the seat held inside an individual simulation.
- **Bootstrap rule:** The first account in a new installation becomes the initial Admin. Public registrations after the first account are always Students. Only an Admin can create a Professor; Admins and Professors can create Students.
- **Assignment rule:** Session managers assign President and Executive seats. A Professor may select facilitator-only, President, or Executive participation when creating a session. Students cannot grant themselves elevated account or session permissions.

### Confirmed Hosting and AI Services ✅

- **Application hosting:** Render.com is the canonical production host. Deploy the React/Vite frontend as a Render Static Site and the FastAPI backend as a Render Web Service.
- **Production database:** Neon PostgreSQL is the authoritative production database. SQLite remains local-development and isolated-test storage only; production game state must never depend on a Render service filesystem.
- **Availability:** Configure a scheduled keep-alive request to the backend health endpoint when the selected Render service plan can suspend after inactivity. Prefer an always-on Render instance for classroom sessions; the cron ping is a deployment safeguard, not a substitute for capacity and uptime guarantees.
- **AI provider:** Gemini is the production AI provider. All Gemini requests proxy through FastAPI, and the API key and model names are server-side secrets. They must never be embedded in the Vite bundle, committed to Git, logged, or returned by an API response.
- **Initial scaling boundary:** Run one FastAPI instance while WebSocket fan-out remains in process memory. Before scaling to multiple backend instances, move real-time pub/sub to a shared service such as Redis so every connected classroom receives the same notifications.

#### Canonical production service layout

| Component | Provider | Required configuration |
| --- | --- | --- |
| React/Vite frontend | Render Static Site | Build from `frontend`; publish `frontend/dist`; set `VITE_API_URL` to the public FastAPI URL before building. |
| FastAPI API and WebSockets | Render Web Service | Build/install `backend/requirements.txt`; start Uvicorn on Render's assigned `PORT`; allow the frontend origin; expose `/healthz`; initially run one instance. |
| Relational game state | Neon PostgreSQL | Use Neon's pooled PostgreSQL connection string with TLS; store it only as `PANGEAWORLD_DATABASE_URL`; apply migrations before serving traffic. |
| Keep-alive scheduler | Render Cron Job or approved external monitor | Request `GET /healthz` on the interval permitted by the selected hosting plan; alert after repeated failures. Do not mutate game state from this job. |
| AI advisor and newsroom | Google Gemini API | Set `GEMINI_API_KEY`, `GEMINI_ADVISOR_MODEL`, and `GEMINI_NEWS_MODEL` only on the backend service. |

#### Required production environment variables

```text
# Render frontend build
VITE_API_URL=https://<pangeaworld-api>.onrender.com

# Render FastAPI service
PANGEAWORLD_DATABASE_URL=postgresql+psycopg://<neon-user>:<password>@<neon-pooler-host>/<database>?sslmode=require
PANGEAWORLD_MIGRATION_DATABASE_URL=postgresql+psycopg://<neon-user>:<password>@<neon-direct-host>/<database>?sslmode=require
PANGEAWORLD_CORS_ORIGINS=https://<pangeaworld-frontend>.onrender.com
PANGEAWORLD_COOKIE_SECURE=1
GEMINI_API_KEY=<render-secret>
GEMINI_ADVISOR_MODEL=gemini-3.8-flash
GEMINI_NEWS_MODEL=gemini-3.8-flash
```

Use Render and Neon secret/environment-variable controls for all credentials. The keep-alive URL contains no secret and must call a read-only health route. Live Gemini validation must verify quota behavior, latency, provider failure fallback, privacy guardrails, and usage-cost monitoring before the first student pilot.

---

## Confirmed Design Decisions

### Account and Session Authorization — Implemented September 16, 2026

PangeaWorld uses two related but separate authorization layers:

1. **Installation account type** answers what a person may administer across the application.
2. **Session membership role** answers which seat or facilitator identity that person holds in one game.

| Account type | Installation capabilities | Session participation |
| --- | --- | --- |
| `admin` | Create Professors and Students, change account types, view every session and its progress, explicitly enter any session, create sessions, and use all Professor capabilities. | May facilitate or take a President/Executive seat. An Admin who opens another owner's session receives an explicit facilitator membership. |
| `professor` | Create managed Student accounts, create sessions, view owned-session progress, distribute join codes, assign seats, start games, advance phases, and use instructor analytics/tools for owned sessions. | Chooses facilitator-only, President, or Executive when starting a session. Ownership preserves management authority after taking a player seat. |
| `student` | No account-management or session-creation authority. | Join by lobby code, accept an assigned President/Executive seat, submit decisions, participate in rounds, and use player-scoped advisor/debrief tools. |

#### Persisted identity and ownership

- `users.account_type` stores `admin`, `professor`, or `student` and is the canonical installation role. The legacy `is_instructor` field remains synchronized for compatibility with existing instructor-only Phase 3/4 routes while those routes are incrementally migrated.
- `users.managed_by_user_id` associates a Professor-created Student with that Professor's account workspace. Admins can see the complete account directory; Professors see the Students they provisioned.
- `game_sessions.owner_user_id` records the Admin or Professor who created or claimed the session. Ownership is stable even if that user changes their `game_memberships.role` to `president` or `executive`.
- `game_memberships.role` remains session-local and may be `instructor`, `player`, `president`, or `executive`. It must not be used as a substitute for the installation account type.

#### Authorization rules

- FastAPI is the enforcement boundary. Frontend visibility is a usability feature only; every privileged endpoint independently verifies the authenticated account and, where applicable, session ownership or membership.
- Admins may see installation-wide session summaries. Entering a session is an explicit `POST /api/accounts/sessions/{session_id}/access` action that creates a facilitator membership if one does not already exist.
- Professors may manage only sessions they own or legacy sessions in which they retain the instructor membership. Taking a player seat does not remove their ability to generate the map, start the game, inspect readiness, or advance phases.
- Students cannot create sessions, create accounts, change roles, access instructor analytics, or invoke facilitator commands. Decision routes continue to enforce session membership, assigned seat, entity ownership, phase, and deadline constraints.
- The installation must retain at least one Admin. The API rejects demotion of the sole remaining Admin.

#### Account and dashboard API

| Endpoint | Access | Purpose |
| --- | --- | --- |
| `GET /api/accounts/dashboard` | Authenticated | Returns a role-filtered account directory, session list, live progress, and aggregate counts. |
| `POST /api/accounts/users` | Admin or Professor | Admin creates Professors or Students; Professor creates Students only. |
| `PATCH /api/accounts/users/{user_id}/role` | Admin | Changes an installation account type while preserving the last-Admin invariant. |
| `POST /api/accounts/sessions/{session_id}/access` | Admin | Explicitly enters any session with facilitator authority. |
| `POST /api/sessions` with `owner_role` | Admin or Professor | Creates a session as facilitator-only, President, or Executive and persists the creator as owner. |

#### Frontend behavior

- `frontend/src/components/AccountDashboard/index.jsx` is the canonical post-login landing experience.
- Admins see installation-wide live-session counts, session/round progress, the account directory, role controls, account creation, join codes, and session-entry controls.
- Professors see owned sessions, managed Students, Student provisioning, deadline configuration, and a participation selector for facilitator, President, or Executive.
- Students see only their sessions and the join-code workflow. They do not receive account or session administration controls.
- A Professor who plays a seat receives a compact facilitator control dock during gameplay so they can view readiness and advance phases without abandoning the assigned President/Executive identity.
- The landing experience and login screen are responsive, keyboard accessible, and preserve the existing account-creation, login, lobby, reload, and sign-out recovery contracts.

#### Migration and compatibility

Alembic revision `20260916_0002` adds `users.account_type`, `users.managed_by_user_id`, and `game_sessions.owner_user_id`. During upgrade:

1. Existing instructor accounts become Professors.
2. The earliest existing account becomes the bootstrap Admin.
3. Existing non-instructor accounts remain Students.
4. Existing session ownership is derived from each session's instructor membership when available.

SQLite development startup applies the same compatibility additions in `backend/database.py`. Production continues to rely exclusively on the Render pre-deploy Alembic command against the direct Neon connection.

### 0. Opportunity Cost Is a Core Learning Mechanic ✅

Opportunity cost, as taught in economics, is the value of the **next-best feasible alternative forgone** when a choice is made. PangeaWorld must teach this through the decision loop itself, not only mention it in explanatory text. The intended pattern is comparable to CAPSIM-style marketing allocation: increasing a marketing budget may improve awareness or demand, but the same money can no longer fund R&D, capacity, quality, working capital, or debt reduction, and additional spending is subject to diminishing marginal returns.

This requirement applies to **both Presidential and Company Executive decisions** in every round:

1. **Constrained choice set:** Each material choice draws from an authoritative, finite resource pool and competes with at least one other feasible use of that resource. Choices must interact; they may not behave as independent sliders whose maximum settings can all be selected without consequence.
2. **Explicit alternatives before submission:** The interface must show at least two relevant alternatives or allocations, the binding constraint, the direct and recurring cost of the draft choice, and the projected effect on the other options. The player must identify the next-best alternative they are giving up and briefly explain why the selected use is preferred.
3. **Marginal, not merely total, effects:** Previews and advisor prompts must emphasize the expected benefit of the **next unit** spent or committed. Where appropriate, formulas must use diminishing returns, capacity limits, delays, crowding out, maintenance obligations, or risk so that “spend the maximum everywhere” is not a dominant strategy.
4. **Server enforcement and persistence:** FastAPI validates resource feasibility, rejects over-allocation and double-spending, calculates authoritative costs and effects, and stores the submitted allocation, considered alternatives, selected next-best foregone alternative, player rationale, assumptions available at submission time, and ruleset version in the immutable decision ledger.
5. **Consequences and feedback:** Round results must show the chosen action's realized benefits and costs, changes to the constrained resource pool, and the effect of what was delayed or forgone. When the deterministic engine supports it, the debrief must compare the chosen outcome with a labeled counterfactual of the recorded next-best alternative; estimates must never be displayed as certain historical facts.
6. **Assessment:** Instructor analytics and scorecards must evaluate whether teams recognized constraints, compared credible alternatives, reasoned at the margin, and revised their allocations based on prior outcomes. The game must not award points merely for spending more.

**Presidential applications include:**

- Military readiness versus infrastructure, education/industrial policy, disaster recovery, debt service, or tax relief.
- Rush deployment versus the cheaper but slower and more exposed project timelines.
- Tariff revenue/protection versus higher input and consumer prices, retaliation, and export competitiveness.
- Subsidies or an approved lobbying request versus competing industries, regions, and fiscal capacity.
- FMI contributions, borrowing, reserves, diplomacy, sanctions, and covert action versus the alternative uses and future flexibility they displace.

**Company Executive applications include:**

- CAPSIM-style marketing spend versus R&D, product quality, production capacity, inventory, hiring, supply-chain resilience, cash reserves, and debt reduction.
- Lower price and possible volume/market-share gains versus unit margin and capacity pressure.
- Higher production versus working-capital needs and the risk/carrying cost of unsold inventory.
- A cheap supplier or shipping mode versus lead time, reliability, tariffs, insurance, quality, and disruption risk.
- Automation or long-term capacity versus current liquidity and near-term flexibility.

**Definition of done for any new decision mechanic:** Its specification, API contract, UI, engine formula, round report, AI-advisor prompt, and tests must identify (a) the scarce resource, (b) at least two competing feasible uses, (c) the next-best alternative that can be forgone, (d) short- and long-run effects, and (e) how the trade-off is surfaced to the student. A decision mechanic that fails any of these checks must not be marked complete.

### 1. Round Duration & Pacing ✅
- **In-Game Timeframe:** Each round represents **1 full year** in Pangea.
- **Staggered 2-Day Rounds (Real Time)** — The 48-hour real-time round is split into two distinct phases to simulate macroeconomic cause and effect. This creates a narrative **6-month delay** between macro policy changes and micro market reactions:
  - **Day 1 (Presidential Phase / First 6 Months):** Presidents analyze data, receive lobbying requests from their companies, and submit their macro decisions (infrastructure, tariffs, military, diplomacy).
  - **Day 2 (Company Phase / Second 6 Months):** Companies react to the new policies set by their president and the global market, locking in their micro decisions (pricing, sourcing, production).
- **Lobbying Mechanic:** During Day 1, companies can submit formal requests to their president for specific resources (e.g., "we need cheaper steel") or infrastructure (e.g., "build a port"). The president's dashboard will aggregate these requests, prioritizing the needs of larger companies that impact GDP the most.
- **7 total rounds** per game (14 calendar days for a full game, representing 7 years in Pangea)
- **Asynchronous** — decisions are submitted like homework, not live in class. The engine processes once the Day 2 deadline passes
- Class time can be used for debriefing, strategy discussion, and connecting game events to real-world examples

### 2. Player Scale ✅
- **2-4 students per company team**
- 10-15 companies × 7 player nations = 70-105 company teams + 7 presidents
- Unfilled slots backfilled by AI bots (see Phase 2)

### 3. Win Conditions & Scoring ✅
**No elimination** — all nations and companies play all 7 rounds regardless of performance.

> [!TIP]
> ### Balanced Evaluation (Proportional + Absolute)
> Because nations start with asymmetric resources and geographic advantages (e.g., Lunara's high baseline costs vs. Valdoria's resource wealth), scoring evaluates a **balance of both proportional growth AND absolute raw values**.
> - **Proportional Growth** measures who managed their resources best relative to their starting position.
> - **Absolute Values** represent the sheer scale and dominance achieved in the global market.
> Winning requires a combination of smart incremental management and achieving massive scale.

**Company Scorecard** (CAPSIM-style round report):

| KPI | Description |
|:---|:---|
| **Net Profit (Absolute & Relative)** | Raw profit value + evaluated against baseline expectations |
| **Market Share (Absolute & Growth)** | Total % of market owned + round-over-round % change |
| **Revenue (Absolute & Growth)** | Total revenue generated + round-over-round % increase |
| **Gross Margin** | (Revenue - COGS) / Revenue — measures pure operational efficiency |
| **Return on Assets (ROA)** | Net income / total assets — measures how well they use what they have |
| **Cash Position** | Available cash after obligations (absolute) |
| **Supply Chain Efficiency** | Landed cost vs. competitors sourcing the same resources |
| **Customer Satisfaction** | Composite of price competitiveness, product quality, and availability |

**President Scorecard:**

| KPI | Description |
|:---|:---|
| **GDP (Absolute & Growth)** | Total national GDP + round-over-round % change |
| **Inflation (CPI Stability)** | How well the president managed inflation/deflation relative to their nation's baseline |
| **Unemployment (Absolute & Change)** | Current unemployment % + the % reduction or increase |
| **Trade Balance** | Total value of exports vs. imports |
| **Infrastructure Index** | Quality and coverage of railroads, ports, and routes |
| **Debt-to-GDP Ratio** | FMI debt relative to GDP — lower is healthier |
| **Diplomatic Standing** | Number of active trade agreements, alliances, and sanctions (for/against) |
| **Military Readiness** | Total defensive capability + capability relative to active threats |
| **National Approval Rating** | Composite score simulating citizen satisfaction with the president's leadership |

**Drakmoor Targeting the Leader:**
- Drakmoor's AI factors in **who is currently winning** when making decisions
- The leading nation/company may attract Drakmoor's attention — trade disruptions, hostile diplomacy, or even military targeting
- This adds a "rubber-band" mechanic that prevents runaway leaders and keeps the game competitive
- However, Drakmoor is careful about attacking militarily strong nations — it prefers economically dominant but militarily weak targets

**Auto-Decision Penalty:**
- If a team **does not submit decisions** by the 48-hour deadline, the engine applies **auto-decisions**
- Auto-decisions are intentionally **suboptimal** — conservative pricing, no R&D investment, no supply chain adjustments, no diplomatic actions
- This serves as a **penalty for inactivity** — your company/nation falls behind if you don't engage
- The Pangea Times may report: *"[Company X] appears to be on autopilot this quarter..."*
- Presidents who skip a round default to status-quo policies with no military actions and abstain on sanctions votes

### Project & Operation Timelines (Deployment Speed vs. Cost)
When presidents deploy major projects, sweeping decisions, or military operations, they must choose a deployment timeframe ranging from 1 to 3 rounds. This forces a strategic trade-off between speed, financial cost, and secrecy:

| Timeframe | Cost Multiplier | Intel Vulnerability | Description |
|:---|:---|:---|:---|
| **1 Round** (Rush) | 5x Normal Price | Immune to Interception | Executed immediately with maximum secrecy, but financially devastating. Foreign intel cannot intercept 1-round decisions before they happen. |
| **2 Rounds** (Standard) | 2x Normal Price | Moderate Vulnerability | Executed with moderate urgency. There is a chance foreign spies might uncover the plans during the intermediate round. |
| **3 Rounds** (Long-term) | 1x Normal Price | High Vulnerability | The most cost-effective option, requiring long-term planning. Because the operation develops over 3 years, it is highly susceptible to being discovered by rival intelligence networks before execution. |

- This mechanic teaches that **fast execution requires massive capital** and that **secrecy has a steep price**.
- The likelihood of rival nations finding out about a pending operation increases significantly as the timeframe increases.

### 4. Resource Types ✅
Six resource categories confirmed:
- **Energy** (oil, natural gas, renewables)
- **Minerals** (metals, rare earths)
- **Agriculture** (food, livestock)
- **Technology** (R&D output, patents)
- **Labor** (population, education level)
- **Capital** (financial markets, banking)
- Resources **deplete gradually** over time, teaching sustainability and forcing nations to adapt

<a id="rare-earth-discovery"></a>

### 4.1 Rare-Earth Discovery and Extraction — Proposed

This mechanic adds a secret, high-cost national development project. It is intentionally a speculative investment: every President may pay to explore, but only two nations actually contain a deposit. The allocation is fixed for the entire session and cannot be changed by reloading, retrying, or beginning a second exploration.

#### Canonical rules

- **Exactly two hidden deposits:** At session creation, the server selects exactly two distinct nations from the canonical set of eight. Drakmoor is eligible under the default rule because it is one of the eight nations; excluding it would require a separate versioned ruleset decision. Selection uses server-only entropy and the selected nation IDs are persisted in confidential game state. The public session/map seed alone must not reveal or reproduce the selection.
- **Unknown at the start:** No President, Company Executive, AI advisor, public API, news feed, analytics response, or ordinary instructor dashboard can see the allocation at game start. Administrative database access is outside the game-information boundary. The owning President does not know whether their nation has a deposit until exploration finishes.
- **One exploration per nation:** A President may start one national rare-earth exploration program. The normal exploration duration is **3 completed round resolutions**. Its ruleset-configured cost is committed when the project starts, competes with military, preparedness, infrastructure, services, and debt uses of treasury, and is not refunded if no deposit is found.
- **Private discovery result:** At the end of the exploration duration, the server records `confirmed_present` or `confirmed_absent`. The result is initially visible only to that nation's President and authorized instructor audit/debrief views. A negative result is final; repeated exploration cannot convert an absent nation into a deposit nation.
- **Extraction cannot be bought speculatively:** The server must reject an extraction-infrastructure purchase unless that nation has a completed `confirmed_present` discovery. A client hiding the button is not sufficient enforcement.
- **Two-round extraction build:** After a positive discovery, the President may fund extraction infrastructure. The normal build duration is **2 completed round resolutions**. The project becomes operational at the beginning of the following round; construction does not produce a partial GDP benefit.
- **Operational benefit:** An operational deposit applies a ruleset-tunable GDP level uplift with a default target of **20%**. The authoritative formula is `final_gdp = pre_rare_earth_gdp × (1 + rare_earth_bonus_rate × operational_fraction)`, where the default bonus rate and operational fraction are `0.20` and `1.0`. The multiplier is applied to that round's GDP after the ordinary GDP calculation and documented event/conflict adjustments. It must not compound by multiplying a prior round's already boosted GDP, and it is not a one-time cash grant.
- **First implementation boundary:** The operational deposit affects national GDP and the President scorecard but does not automatically create tradeable `Minerals` stockpile or company inventory. A later ruleset may add rare earths as a separately priced commodity; doing so must avoid counting both commodity output and the full GDP multiplier twice.

#### Timeline and private-capital acceleration

Project progress advances exactly once during authoritative round processing. A project started in Round 1 follows this normal schedule:

| Round | Normal project state |
|:---|:---|
| **1** | Exploration year 1 of 3 |
| **2** | Exploration year 2 of 3 |
| **3** | Exploration year 3 of 3; result revealed privately after processing |
| **4** | If present and funded, extraction construction year 1 of 2 |
| **5** | Extraction construction year 2 of 2; construction completes after processing |
| **6** | First round receiving the GDP uplift |

The President may request and accept one server-quoted private-capital package over the entire rare-earth project lifecycle:

- The package accelerates **either** exploration from 3 rounds to 2 **or** extraction construction from 2 rounds to 1. It cannot accelerate both phases, cannot stack with another request, and cannot make any phase instantaneous. The earliest possible GDP benefit for a Round 1 start is therefore **Round 5**.
- In the first implementation, private capital is an abstract financing market rather than a direct transfer from a player-controlled company. This prevents the multi-round schedule from depending on whether a particular Company seat is filled. The accepted offer, financing amount, repayment or revenue-share terms, and accelerated phase are persisted in the decision ledger.
- Private acceleration is not a free bonus. The quote must impose a visible ruleset-configured concession, such as future repayments or a share of project revenue, and the President must compare it with at least two feasible uses of public treasury before accepting it. Exact exploration cost, extraction cost, private-finance terms, and any diminishing-return parameters remain balance constants that require playtesting; they must not be hard-coded in React.
- The dashboard must show the forecast discovery round, earliest legal construction round, operational round, remaining game rounds receiving benefits, total public commitment, private financing obligation, and the selected next-best alternative. It must warn when a new project cannot become operational before the seven-round game ends.

Examples: a normal Round 2 start becomes operational in Round 7. A normal Round 3 start would not pay off within the game, while a Round 3 start with one valid acceleration can become operational in Round 7.

#### Balance consequences

- With two deposits among eight eligible nations, every nation has a **25% ex ante chance** of containing one. Because Drakmoor is eligible by default, there is also a 25% chance that one deposit belongs to Drakmoor; the expected number of player-controlled deposits is 1.75. If the product intent is exactly two human-controlled opportunities, the eligible pool must instead be explicitly limited to the seven player nations in the versioned ruleset.
- A successful normal Round 1 project receives two benefit rounds (Rounds 6–7), while either acceleration path receives three (Rounds 5–7). At a stable baseline GDP, those are gross cumulative uplifts equal to approximately 40% and 60% of one annual baseline-GDP amount respectively, not a 40% or 60% uplift in any single round.
- Before project costs, the ex ante gross value of normal Round 1 exploration is therefore approximately 10% of one annual baseline-GDP amount (`25% success × 2 rounds × 20%`). With acceleration it is approximately 15%. These values are balancing reference points, not player guarantees; exploration cost, extraction cost, financing terms, events, conflict, and changing GDP determine realized value.
- The random endowment can create a substantial leaderboard swing late in the game. Scorecards and debriefs must attribute the uplift separately from underlying economic performance so instructors can distinguish a sound high-risk decision from luck, while final GDP remains the authoritative in-game value used by systems such as Drakmoor leader targeting.

#### Information disclosure

- Exploration status and a completed negative result remain private to the owning President. The AI advisor may reason over these facts only for that same President and may not expose them through instructor-wide prompts, another player's context, or the Global Ledger.
- A positive result remains private until the President begins extraction construction. Starting visible extraction infrastructure necessarily confirms the deposit and becomes a public project event. The operational status, gross GDP uplift, financing cost, and resulting net effect appear in round results and the President scorecard.
- WebSockets publish only a generic state-change notification. Clients re-fetch an authorization-filtered REST representation; neither notification payloads nor market/resource serializers may contain hidden deposit fields.
- Post-game debrief may reveal the original two-nation allocation, exploration choices, timing, costs, and forgone alternatives to all participants as historical evidence.

#### Required project changes and current-project impact

| Area | Required change | Primary impact or risk |
|:---|:---|:---|
| **Ruleset and session creation** | Add a versioned rare-earth ruleset/config and allocate exactly two deposits when the session is seeded. Persist allocation separately from the public map snapshot. | Using the existing public session seed would make the secret predictable; existing sessions need a migration/default with the mechanic disabled. |
| **Database model** | Add confidential deposit state plus a persisted project record containing nation, status, phase, start/completion rounds, progress, costs, discovery result, acceleration used, financing terms, and reproducibility key. | The existing `Resource` row is serialized to nation and market APIs, so placing undiscovered deposits there would leak them. Multi-round state must survive reloads and deploys. |
| **Round manager and economy engine** | Validate and reserve funds, advance each active project once per processed round, reveal discovery, unlock construction, activate production, and apply the non-compounding GDP multiplier in a documented order. | Processing must remain idempotent; a phase retry must not advance a project twice or apply 20% twice. |
| **API and authorization** | Add owner-scoped quote/start/status commands and a sanitized public project/result view. Enforce `confirmed_present` before accepting construction. | New object-level authorization and response-sanitization tests are required to prevent cross-nation discovery leaks. |
| **President dashboard** | Add an exploration/extraction panel with cost, risk, project timeline, private offer, constraints, opportunity cost, and owner-only results. | The seven-round horizon makes timing comprehension essential; optimistic client calculations are previews only. |
| **Scoring and analytics** | Store and display pre-uplift GDP, gross rare-earth uplift, financing obligations, and final GDP separately. Keep the random endowment visible in post-game evaluation. | A 20% level uplift can materially change the GDP leaderboard and Drakmoor's leader-targeting behavior; without attribution, luck may be mistaken for decision quality. |
| **Advisor, news, and debrief** | Filter unrevealed state from prompts and public news; publish construction/operation only after the defined reveal point; add a post-game timeline and counterfactual. | Existing AI/public-ledger adapters must not receive confidential allocation fields. |
| **Auto-decisions and Drakmoor** | Define conservative AI behavior for exploration, construction, and private offers without reading the hidden answer. | An AI that invests only when a deposit exists would leak state and gain an unfair advantage. |

#### Acceptance and verification requirements

- Across a broad seed corpus, each enabled new session has exactly two distinct persisted deposit nations, the selection is stable across reloads, and it is absent from every unauthorized serializer, market endpoint, WebSocket message, advisor prompt, export, and public ledger record.
- A Round 1 normal project reveals after Round 3, builds during Rounds 4–5, and first applies the uplift in Round 6. Either valid acceleration path first applies it in Round 5. No path can gain two rounds, build before positive confirmation, or receive a partial construction benefit.
- Negative exploration consumes its committed cost, reveals only to the owner, rejects construction, and cannot be retried. Missed/automatic Presidential decisions never start or accelerate a rare-earth project implicitly.
- Reprocessing the same round is idempotent: progress, costs, reveal events, financing obligations, and GDP uplift are each recorded exactly once.
- GDP tests prove that the default uplift is 20% of the current round's pre-rare-earth GDP, is itemized in results, and does not compound from a prior boosted total. Disaster/conflict ordering and any `operational_fraction` reduction are deterministic and covered explicitly.
- Opportunity-cost tests reject unaffordable or double-committed treasury, require reviewed alternatives and rationale, and show private-finance terms and the number of benefit rounds remaining before acceptance.

### 5. Military Mechanics Depth ✅ — Medium
- Students choose **unit types** (infantry, navy, air force) and deploy them on the map
- **Supply lines matter** — troops far from borders cost more to maintain
- **Intelligence operations** — spend budget to spy on other nations. This can randomly uncover secret information, such as intercepted lobbying requests from foreign companies to their presidents, helping players deduce rival nations' long-term economic or military plans. **Note: Nations are fully protected from all espionage and sabotage during Rounds 1 and 2**, giving them a grace period to build their economies. However, presidents can begin investing in their intelligence capabilities starting in Round 1 to prepare for Round 3.
- **Covert Sabotage** — When resources are scarce, rival nations building infrastructure (e.g., railroads) to shared resource nodes will drive up your costs. Presidents and companies can fund covert sabotage to destroy this competing infrastructure. Success is randomized (resolved with Attack Index / Defense Index) and depends on both the attacker's and defender's intelligence capabilities, which can be upgraded through investments. If caught, the FMI automatically sanctions the aggressor for 1-2 rounds.
- **False Flag Attacks (Round 5+)** — Companies with high intelligence/military investments can orchestrate false flag attacks starting in Round 5. Success is randomized and odds scale with their investment level. If successful, the framed nation takes the blame and faces immediate international sanctions. If discovered (failed roll), the executing company and their home nation face severe FMI sanctions and diplomatic isolation.

**Combat Resolution — Attack Index vs. Defense Index:**

Each nation has two military indices that grow with investment:

| Index | Components |
|:---|:---|
| **Attack Index (ATK)** | Offensive units (infantry, navy, air) + technology level + supply line proximity + intelligence intel |
| **Defense Index (DEF)** | Defensive units + fortifications + terrain bonus + infrastructure quality |

The index determines **how many dice** each side rolls:

| Index Level | Dice Rolled | Example Investment Level |
|:---|:---|:---|
| 1–2 | 1 die | Minimal military, no tech investment |
| 3–4 | 2 dice | Moderate standing army |
| 5–6 | 3 dice | Well-funded military with tech |
| 7–8 | 4 dice | Major military power |
| 9–10 | 5 dice | Superpower-level force projection |

**Tie-breaking rule:** When the highest dice are compared, **ties go to whichever side has the higher index** (ATK or DEF). This means a nation with ATK 7 that ties with a nation at DEF 5 wins the tie. Investing in your index gives a subtle but powerful edge.

**Quarterly Campaign Cycle & Conditional Orders:**
- Wars are not resolved in a single instant. An attack order initiates a **year-long campaign** (1 round = 1 year) that resolves in **quarterly phases (every 3 months)**.
- **Conditional Orders (If/Then):** Presidents can issue logical conditionals for their campaigns (e.g., "If we haven't secured the territory by the 6-month mark, halt the attack and retreat" or "If our casualties exceed 30%, stop"). This adds strategic depth to military planning.
- **Campaign End Conditions:** Troops will continue to attack each quarter until either the territory/objective is fully conquered, the attacking force is depleted/lost for the year, or a conditional order halts the offensive.
- **Mid-Year War Report:** Since Presidents lock in their attack policies on Day 1 (Month 1), the first two quarters of the campaign are resolved by the engine *before* companies make their Day 2 (Month 7) decisions.
- This gives companies crucial intelligence on how the war is progressing (e.g., "Our forces are stalled" or "The enemy port has been captured") so they can adjust their supply chains and pricing accordingly for the second half of the year.

**Key implications:**
- **War is Unpopular:** Starting an offensive war significantly lowers a president's Approval Rating. The game remains fundamentally an educational business simulation, not a war game. Military is a calculated geopolitical tool, not a default strategy.
- A nation with ATK 2 (1 die) attacking a nation with DEF 6 (3 dice) is near-suicidal — the defender compares 3 dice to 1
- A nation with ATK 8 (4 dice) vs. DEF 4 (2 dice) has overwhelming advantage + wins all ties
- Even at equal dice, the higher-index nation has the tie-breaking edge
- Indices grow through **sustained investment over multiple rounds** — you can't build a superpower military overnight
- This teaches that military capability is a long-term strategic investment, not a last-minute panic buy

- War is costly — military spending directly reduces economic investment capacity
- Ties into supply chain, budgeting, and opportunity cost lessons

### 6. Trade & Diplomacy ✅ — Full Feature Set
- **Alliances**: Presidents can formally ally (shared military defense, preferential trade rates, joint sanctions voting)
- **Trade defaults allowed**: Nations can break deals — the game engine does NOT enforce contracts. This teaches contract risk, trust, and the importance of enforceable international agreements
- **UN-style forum ("Pangea Assembly")**: A public chat space where all 8 presidents (including Drakmoor) can make speeches, propose resolutions, negotiate deals, and posture. All messages are logged and visible to the instructor

---

## Suggested Additional Course Connections

Based on your framework, here are courses that naturally map to PangeaWorld mechanics:

| Course | Game Mechanic |
|:---|:---|
| **International Affairs** | Diplomacy, alliances, sanctions, war declarations, UN-style forum |
| **International Business** | Cross-border trade, tariffs, currency exchange, FDI decisions |
| **Supply Chain Management** | Resource sourcing, logistics routes, disruption events (port closures, weather) |
| **Macroeconomics** | CPI, GDP, inflation, monetary policy, interest rates, unemployment |
| **Finance** | Company valuation, stock prices, debt/equity decisions, ROI |
| **Marketing** | Product positioning, pricing strategy, market share competition |
| **Data Analytics** | Dashboard interpretation, KPI analysis, forecasting |
| **Ethics & Corporate Responsibility** | Environmental impact, labor conditions, corruption mechanics |
| **Negotiation** | Trade deals, alliance formation, conflict resolution |
| **Political Science** | Government types, policy decisions, public approval ratings |

---
