# PangeaWorld Architecture & Instructions


## Architecture Document Map

This file is the entry point and the source of truth for repository-wide constraints, current behavior, and document-routing instructions. Detailed specifications and implementation history live in focused modules so no architecture document exceeds 500 lines.

| Document | Owns |
|:---|:---|
| [Product and Game Rules](docs/architecture/product-and-game-rules.md) | Product vision, hosting and identity decisions, opportunity-cost rules, round pacing, scoring, rare-earth discovery, military, trade, and course connections. |
| [Product Delivery Roadmap](docs/architecture/delivery-roadmap.md) | Planned Phase 1–4 product scope, data model, dashboards, map/logistics, nations, multiplayer, military/events, and AI/analytics deliverables. |
| [Technical Architecture and Phase 1](docs/architecture/technical-architecture-and-phase-1.md) | Technology stack, verification strategy, delivery estimates, and completed Phase 0/1 implementation record. |
| [Phase 2 and Phase 3 Implementation](docs/architecture/phase-2-and-3-implementation.md) | Multiplayer, authorization, deadlines, real-time synchronization, conflict, events, opportunity-cost closure, and associated acceptance history. |
| [Phase 4 and Release Readiness](docs/architecture/phase-4-and-release.md) | Gemini advisor, usage logging, instructor analytics, debrief, AI backfill, production deployment, and remaining release checks. |
| [Post-Launch Map Architecture and Roadmap](docs/architecture/post-launch-map-roadmap.md) | Shared world document, 2D/3D map architecture, construction persistence, rendering, performance, migration, and phased map delivery. |

### Maintenance instructions

- Start here to find the owning module; do not append detailed feature specifications to this index.
- Keep each Markdown file at **500 lines or fewer**, including headings and blank lines. When a module approaches 450 lines, split it at a top-level concern, add both new documents to the table above, and repair relative links in the same change.
- Keep one authoritative home for each rule. Other modules should link to it instead of copying it. Cross-cutting changes may update multiple modules, but duplicated normative text should be avoided.
- Put product rules and player-visible behavior in **Product and Game Rules**; planned scope in **Product Delivery Roadmap**; shared technology and verification guidance in **Technical Architecture and Phase 1**; completed sprint evidence in the applicable phase-history module; and future map work in **Post-Launch Map Architecture and Roadmap**.
- Preserve the distinction between **implemented**, **planned**, and **deferred** behavior. Updating a proposal does not make it implemented; update the status summary in this file only when application code and verification support the change.
- Use repository-relative Markdown links and stable heading anchors rather than line-number references. After moving a section, search the full repository for its old filename, heading, and any stale “above/below” wording.
- Repository-wide architectural constraints in this file override narrower module text. If two modules conflict, resolve the conflict explicitly here and then align both modules.

## Repository File Map

The principal structure of the PangeaWorld repository:

```
PangeaWorld/
├── app_architecture.md                         (Architecture index and global constraints)
├── docs/architecture/                          (Focused architecture and roadmap modules)
│   ├── product-and-game-rules.md
│   ├── delivery-roadmap.md
│   ├── technical-architecture-and-phase-1.md
│   ├── phase-2-and-3-implementation.md
│   ├── phase-4-and-release.md
│   └── post-launch-map-roadmap.md
├── backend/
│   └── main.py                                (Initial FastAPI backend setup)
└── frontend/
    ├── package.json / vite.config.js          (Vite tooling configuration)
    ├── index.html                             (Vite entry point)
    ├── src/
    │   ├── components/GameMap.jsx             (Canonical snapshot-backed React Canvas renderer)
    │   ├── utils/MapGenerator.js              (One-time seeded map generator)
    │   └── utils/MapSnapshot.js               (Snapshot serialization and hydration)
    ├── src/utils/MapGenerator.test.js         (Seeded and snapshot regression suite)
    ├── e2e/four-player.spec.js                (Isolated four-browser acceptance path)
    └── public/
        ├── favicon.svg / icons.svg
        └── map_prototype.html                 (Standalone Canvas map kept behaviorally aligned)
```

### Current application additions

- `backend/database.py` owns the local SQLite connection. The canonical local development database is `backend/pangeaworld.db`; root-level `.db` copies are disposable and ignored.
- `backend/auth.py`, `backend/deadlines.py`, and `backend/realtime.py` support multiplayer authentication, phase timing, and session-scoped real-time updates.
- `backend/routes/accounts.py` owns installation-level Admin, Professor, and Student account management plus the role-aware landing-dashboard API. `backend/migrations/versions/20260916_0002_account_roles.py` upgrades existing installations with persisted account roles, Professor-managed students, and stable session ownership.
- `backend/engines/`, `backend/models/`, `backend/routes/`, and `backend/tests/` contain the authoritative game engines, domain/schema layer, API routes (including Phase 3), and regression suites.
- `frontend/src/api/client.js`, `context/GameContext.jsx`, `hooks/useSessionEvents.js`, `components/AccountDashboard/`, and the President/Executive dashboard component trees provide the API-backed account, session-management, and gameplay interfaces.

## Tools Used
- **Map Prototype**: Built entirely with Vanilla JavaScript, HTML5 `<canvas>`, and CSS.
- **Procedural Generation**: Utilizes pure math (composite sine/cosine waves, Voronoi partitioning, and distance calculations) instead of external noise libraries (like Perlin) to generate natural shapes and borders.
- **Frontend Framework**: React single-page application built and served with Vite.
- **Map Renderer**: HTML5 Canvas hosted inside React. D3.js, Mapbox, and a Next.js migration are not part of the canonical architecture.
- **Backend Framework**: Scaffolded using Python FastAPI.

## Expected Behaviors
- **Preview Map Generation**: The standalone `map_prototype.html` is a non-authoritative visual and interaction reference. It may generate a new transient layout when reloaded, and its changes are discarded when the page closes.
- **Game-Session Map Generation**: A real game receives one server-issued seed when the session is created. `MapGenerator.js` generates it once, the full geometry and state are persisted, and the canonical React `GameMap` subsequently hydrates only from that snapshot; refreshing a client never regenerates it.
- **Natural Borders**: The 8 countries are divided using a Voronoi diagram based on fixed capital anchor points, enhanced with 2D noise to create squiggly, organic borders.
- **Map Adjustments**: Zephyria is positioned on the main continent between Nordvik and Drakmoor, reducing Terranova's coastline. Zephyria is landlocked with no sea access; its core challenge is securing resources and negotiating road access through neighboring nations, and its main resource is cheap labor for other nations opening new cities. Lunara has a small land connection (strait) to the mainland.
- **Canonical Starting Settlement Counts**: Every nation starts with **exactly 8 cities total**. Port cities are included in this total rather than added on top of it.
- **Canonical Starting Port Counts**: Nordvik and Lunara each start with **exactly 2 ports**. Drakmoor starts with **exactly 1 port**; it is coastal but has deliberately constrained sea access, not a landlocked nation. All other nations (Valdoria, Terranova, Korvath, Solhaven, and Zephyria) start with **0 ports**. Zephyria is fully landlocked with no sea access.
- **Interactive Grid**: The prototype demonstrates edge-hover and railroad interactions. The multiplayer `GameMap` is read-only for players; future validated infrastructure commands will be the only authoritative mutation path.
- **Dynamic Labels**: The country labels (e.g. "Terranova") dynamically position themselves deep within their respective borders based on the procedural shape formula.
- **Zoom Controls**: The sidebar features a "Map Controls" panel with a slider to zoom the canvas in and out, preserving interaction accuracy.

## Architectural Constraints
- **Procedural Generation Contract**: The procedural map remains seed-driven and may generate different layouts for different games, but every generated map must satisfy the locked gameplay invariants below. Corrective changes to generation or validation logic are permitted when required to enforce those invariants; changes must be covered by deterministic seed-based tests and must not silently change unrelated terrain rules.
- **Canonical Frontend Contract**: React + Vite is the only application frontend. HTML Canvas is the canonical map renderer. The standalone HTML map remains a development preview, not a second game client.
- **Server Authority Contract**: FastAPI owns authoritative game state, decision validation, round transitions, economy calculations, random seeds, and persisted results. React renders server state and submits commands; client calculations may be previews only and cannot determine official outcomes.
- **Identity and Authorization Contract**: Installation account types (`admin`, `professor`, and `student`) are persisted separately from session memberships (`instructor`, `player`, `president`, and `executive`). FastAPI enforces both layers. Hiding a control in React is never an authorization boundary.
- **Session Ownership Contract**: Every newly created game records an `owner_user_id`. An Admin may manage any session; a Professor may manage sessions they own. That authority survives the owner taking a President or Executive seat, so teaching controls and gameplay identity do not depend on the same membership label.
- **Deterministic Simulation Contract**: A stored ruleset version, session seed, starting snapshot, and ordered decision ledger must reproduce the same round results. Authoritative randomness is seeded and executed on the server.
- **Hidden-Randomness Contract**: Secret allocations that players must not infer, including rare-earth deposits, use persisted server-only entropy or a persisted private starting snapshot rather than the client-visible map seed. Hidden state must never appear in generic nation, resource, market, analytics, WebSocket, advisor, or public-ledger payloads before the applicable reveal rule is satisfied.
- **Opportunity-Cost Contract (Required)**: Every material Presidential and Company Executive decision must consume or commit a scarce resource (for example treasury/cash, borrowing capacity, labor, production capacity, inventory, political capital, diplomatic leverage, military readiness, or time) and therefore rule out, delay, or weaken at least one feasible alternative. The product must make that trade-off visible before submission and report it after resolution. A feature is not complete if it presents benefits and direct costs but hides the value of the next-best foregone alternative, permits unconstrained allocation, or creates an obviously dominant choice with no meaningful sacrifice.

## Game Rules (As implemented)
- **Railroad Construction**: Building a standard railroad costs **$1M** per segment.
- **Bridges**: Railroads built over river edges cost **$3M** per segment.
- **Mountain Railroads**: Railroads built on the passable sides of mountains cost **$1.5M** per segment.
- **Impassable Ocean**: Edges touching ocean triangles cannot be built upon.
- **Mountain Mazes**: Mountain generation creates clustered mountain ranges. Crucially, every mountain triangle has **exactly 1 passable edge** (with the other 2 being impassable). This forces players to navigate winding valleys and find specific "passes" through mountain ranges, making logistics a strategic challenge.
- **Starting Cities**: Every nation starts with **exactly 8 cities**. A port is a capability assigned to an eligible coastal city and does not increase its nation's settlement count.
- **Starting Ports**: Nordvik and Lunara each start with **exactly 2 port cities**. Drakmoor starts with **exactly 1 port city**. All other nations (Valdoria, Terranova, Korvath, Solhaven, and Zephyria) start with **0 port cities**. Zephyria is landlocked with no sea access — its strategic challenge is negotiating overland trade routes through neighbors, and its main resource is cheap labor. Port placement may not fall back to a non-coastal tile or create a buildable edge that touches ocean.
- **Dynamic Cost Calculation**: The UI updates the "Total Project Cost" automatically as railroads are placed.
- **River Quotas**: Rivers are generated such that Terranova receives approximately 45% of all river tiles, while all other nations receive at least 5% each.

## Applied vs. Not Yet Applied Planned Features

### ✅ Phase 0 and Phase 1 MVP — Complete
- **Grid-Based Construction**: The map is successfully divided into a fine grid where presidents "trace the route" line-by-line.
- **Distance & Terrain Costs**: Baseline edge traversal costs and edge restrictions are implemented (railroads vs. bridges, exactly one passable edge per mountain triangle, and no passable edge touching ocean).
- **8 Nations Geography**: The 8 nations are fully defined and geographically distributed based on the updated positioning logic.
- **Mountain Ranges**: Distinct, restrictive mountain barriers are implemented with the one-passable-edge invariant enforced per mountain triangle.
- **Starting Settlements & Ports**: Start-state allocation enforces exactly 8 cities per nation, exactly 2 ports for Nordvik and Lunara, exactly 1 port for Drakmoor, and 0 ports for all other nations (Valdoria, Terranova, Korvath, Solhaven, and Zephyria). Zephyria is landlocked with no sea access.
- **Authoritative Game Sessions**: FastAPI and SQLite persist sessions, validated map snapshots, seven-round phase state, decisions, events, and immutable round results.
- **Macro/Micro Economy Engine**: GDP, CPI, inflation, unemployment, pricing, production, R&D, company financials, market share, and policy decisions process on the server.
- **Resources and Logistics**: Production, depletion, scarcity pricing, supplier selection, map-distance routing previews, shipping modes, tariffs, insurance, stock transfers, COGS, and trade balances are connected to round processing.
- **Connected Dashboards**: President and Company Executive dashboards load live API data, submit authoritative decisions, display results/history/news, and distinguish local drafts from server-confirmed submissions.
- **Role-Aware Account Center**: Admin, Professor, and Student accounts receive distinct server-authorized landing experiences. Admins manage accounts and monitor all sessions; Professors create sessions and managed Student accounts and may participate as President or Executive; Students can join and play but cannot create accounts or sessions.
- **Opportunity-Cost Decision Framework**: New `phase3-closure-v1` games enforce shared treasury/cash/capacity constraints, server-quoted alternatives, a selected next-best foregone choice, a written rationale, immutable review history, labeled post-round feedback, and an instructor evidence scorecard.
- **Military and Conflict**: Unit procurement, readiness, deterministic multi-engagement attacks, retreat thresholds, abstract strategic control, naval blockades, private intelligence, conflict-driven prices/insurance/GDP/approval effects, and Drakmoor's instructor-controlled scripted behavior resolve authoritatively.
- **Event and News Engine**: The seven-round schedule contains 3 major and 11 minor seeded incidents, supports reactive unrest and bounded instructor scenarios, and persists market reporting, opinion, and source-verification exercises. Gemini-written market summaries use public facts only and fall back safely when the provider is unavailable.

### ⏳ Remaining Later Work and Deployment Validation
- **Multiplayer Expansion**: Phase 2 Sprint 1 is complete: authentication, instructor assignment, role enforcement, readiness, enforced deadlines, conservative automatic submissions, session-scoped real-time synchronization, and the four-player one-round vertical slice are implemented. Trade, diplomacy, sanctions, FMI, and AI backfill remain in later Phase 2 sprints.
- **AI Agent Integration**: Phase 4 is complete: the private per-user Gemini advisor, persistent chat history, immutable AI-usage logging and grading, instructor analytics, post-game debrief, deterministic Drakmoor behavior, and general AI seat backfill/takeover are implemented. Live Gemini credentials and provider quality/cost validation remain release-readiness work.
- **Future Portals**: The FMI portal and Pangea Assembly remain planned product features.
- **Advanced Logistics Construction**: Dedicated sea-lane/airway path records, chokepoint blockades, project approval/lobbying, construction timeframes, and wartime destruction are later-phase systems.
- **Rare-Earth Discovery and Extraction**: The hidden two-nation allocation, multi-round exploration and extraction projects, private-capital acceleration, owner-only discovery results, and approximately 20% operational GDP uplift in [Product and Game Rules](docs/architecture/product-and-game-rules.md#rare-earth-discovery) are approved architecture but are **not implemented** in the current backend or dashboards.


---
