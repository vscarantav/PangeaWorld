# Product Delivery Roadmap

> Part of the [PangeaWorld architecture documentation](../../app_architecture.md).

## Proposed Changes

### Phase 1 — Foundation & World Building (MVP)
> Goal: Playable single-nation prototype with core economy loop

---

#### Game Engine & Data Model

##### [NEW] Core simulation engine
- **Round Manager**: Controls game state transitions (submission → processing → results)
- **Economy Engine**: Calculates GDP, CPI, inflation, trade balances per nation
- **Resource Engine**: Manages production, consumption, trade flows, and scarcity
- **Event Engine**: Injects world events (weather, political crises, market shocks)

<a id="data-schema-design"></a>

##### [NEW] Data schema design

```
World
├── Map
│   ├── Nations (8 territories with borders & geography)
│   ├── Infrastructure
│   │   ├── Railroads (inter-city, inter-nation — cost per unit distance)
│   │   ├── Rivers (navigable waterways — moderate shipping cost)
│   │   ├── Ports (coastal access points for sea shipping)
│   │   ├── Sea Lanes (cheapest long-distance routes between ports)
│   │   ├── Airports (emergency/premium freight only)
│   │   └── Chokepoints (straits, canals — can be blockaded)
│   └── Routes (precomputed paths between resource nodes)
├── Nations (8 — 7 player + 1 AI)
│   ├── President (user or AI agent for Drakmoor)
│   ├── Confidential Intel Vault (isolated database/table)
│   │   ├── Secret military deployments & covert operations
│   │   ├── Private company lobbying requests
│   │   └── ONLY accessible to the President; leaks ONLY via enemy spy activity
│   ├── Resources (production rates, stockpiles, geographic location on map)
│   ├── Military (budget, units, deployments on map)
│   ├── Economy (GDP, CPI basket, inflation, unemployment)
│   ├── Infrastructure (railroads, ports, bridges — investable & destructible)
│   ├── Policies (tax rates, tariffs, subsidies)
│   └── Companies (10-15 per nation)
│       ├── Team (users)
│       ├── Financials (revenue, costs incl. shipping, profit, cash)
│       ├── Supply Chain (sourcing routes on map, shipping mode, costs)
│       ├── Products (price incl. logistics markup, quality, market share)
│       └── Decisions (per-round submissions)
├── Global Market
│   ├── Commodity Prices
│   ├── Exchange Rates
│   ├── Trade Agreements
│   └── Shipping Rate Index (fluctuates with fuel prices & disruptions)
├── Rounds
│   ├── Round Number
│   ├── Status (planning / submitted / processing / complete)
│   ├── Events (injected scenarios)
│   └── Results (per-nation, per-company snapshots)
├── Global Ledger (AI Knowledge Base)
│   ├── Every public user decision (pricing, sourcing, public military, R&D)
│   ├── Every diplomatic action (proposals, FMI votes, rejected treaties)
│   ├── Every event & disaster (major and minor)
│   ├── Every news article and Pangea Assembly chat message
│   └── Note: AI is strictly partitioned from the Confidential Intel Vaults and cannot leak secrets unless a spy operation officially succeeds.
└── News Feed
    ├── System-generated articles
    ├── Event announcements
    └── Market reports
```

---

#### Frontend — Company Dashboard

##### [NEW] Company executive dashboard
- **Financial Overview**: Revenue, COGS (incl. shipping costs breakdown), gross margin, net profit, cash position (charts + tables)
- **Sourcing Module**: Executives select a required resource and view a live marketplace of suppliers (both user-run and bot companies). The interface displays the base price + available shipping modes + transit times = **Total Landed Cost**.
- **Supply Chain Map**: Interactive map showing chosen sourcing routes. Routes highlighted in green (active), yellow (at risk), red (disrupted)
- **Virtual Consumer Market (Sales)**: Companies set their final product prices in a competitive virtual market. They compete for market share against other user teams AND automated bot companies.
- **Market Position**: Market share vs. competitors, product pricing comparison, and consumer demand curves.
- **Decision Panel**: Per-round input forms for pricing, production volume, R&D investment, and **sourcing route/supplier selection**.
- **News Feed**: "Pangea Times" — AI-generated news articles reflecting world events
- **AI Advisor Panel**: Embedded Gemini chatbot with company-specific context

##### [NEW] President dashboard
- **National Overview**: GDP, CPI breakdown (product-by-product), unemployment rate, trade balance, **FMI debt status**
- **Intelligence Panel**: Reports on other nations' public data + purchased intel
- **Military Command**: Troop deployment map, budget allocation, operation planning
- **Diplomacy Center**: Active treaties, trade agreements, pending proposals, **sanctions voting panel**
- **FMI Portal**: Apply for loans, view repayment schedule, monitor credit rating, and **allocate budget to FMI contributions** (which increases borrowing capacity)
- **Policy Controls**: Tax rates, tariffs, subsidies, **immigration quotas (stimulate/restrict based on labor needs)**
- **AI Advisor Panel**: Embedded Gemini chatbot with nation-specific context

---

#### The Pangea World Map & Logistics System

##### [NEW] Interactive world map
The map is the **centerpiece** of PangeaWorld — a fictional continent where all 8 nations are positioned with realistic geography:

```
                    ┌─────────────┐
              ╔═════╡   NORDVIK   ╞══════╗
              ║     │  (arctic)   │      ║
              ║     └──────┬──────┘      ║
         ┌────╨───┐   river│        ┌────╨────┐
         │VALDORIA│◄───────┤        │DRAKMOOR │
         │(desert/│  railroad  │        │(mountain│
         │ oil)   ├────────┤        │ fortress│
         └───┬────┘   ┌────┴────┐   └────┬────┘
        port │        │KORVATH  │        │ railroad
     ~~~~~~~~│~~~~~~~~│(industr)│~~~~~~~~│~~~~~~~~~
     ~ SEA ~ │  port  └────┬────┘  port  │ ~ SEA ~
     ~~~~~~~~│~~~~~~~~~~~~~│~~~~~~~~~~~~~│~~~~~~~~~
         ┌───┴────┐   railroad │        ┌────┴────┐
         │SOLHAVEN│◄───────┤        │ZEPHYRIA │
         │(finan- │        │        │(trade   │
         │ cial)  │   ┌────┴────┐   │ hub)    │
         └────────┘   │TERRANOVA│   └─────────┘
                      │(agricul)│
              ~~~~~~~~┴─────────┴~~~~~~~~
              ~    LUNARA (island)      ~
              ~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

> [!NOTE]
> This is a simplified layout — the actual game map will be a beautifully rendered interactive visualization. The key point is that **geography determines logistics costs and trade routes**.

##### [NEW] Infrastructure types

| Infrastructure | Description | Shipping Cost | Speed |
|:---|:---|:---|:---|
| **Sea Lanes** 🚢 | Ocean routes between ports | **~$2/unit** (cheapest) | Slow (2-3 days/round) |
| **Rivers** 🛥️ | Navigable waterways within/between nations | **~$5/unit** | Moderate |
| **Railroads** 🚛 | Overland freight routes | **~$12/unit** (most expensive) | Fast (1 day/round) |
| **Air Freight** ✈️ | Emergency/premium cargo only | **~$30/unit** | Instant |

> [!IMPORTANT]
> **Oil Transportation Rule:** Oil cannot be transported by air freight. It must be transported by sea or railroad.

- Costs scale with **distance** (number of map segments traversed)
- Sea shipping requires both origin and destination to have **port access**
- Drakmoor has constrained sea access through its single starting port; if that port is blockaded or unavailable, it must use premium railroad routes or negotiate access through a neighbor's ports
- Rivers are only available along specific geographic features — not every nation pair has a river connection

##### [NEW] Logistics cost model
Shipping cost is factored into every trade and sourcing decision, heavily relying on **volume, weight, and distance**.

- **Distance Scale**:
  - Every tile edge (triangle side), whether land or ocean, represents **100 kilometers**.
  - International waters for freight and transportation are represented by connected ocean triangles. Ocean-touching edges are always impassable to railroad construction.
- **Distance Calculation**:
  - **By Plane (Air Freight)**: Calculated as a straight line from origin point to destination point.
  - **By Rail and Sea**: Calculated by tracing the actual path taken along existing route traffic (railroad networks or international sea lanes).

```
Landed Cost = Base Commodity Price
            + (Freight Cost based on Volume & Weight × Distance × Mode Multiplier)
            + Tariffs (if crossing borders)
            + Insurance (higher in conflict zones)
            + Port/Transit Fees
```

**Example scenario:**
> A company in Solhaven needs steel. Options:
> - **Korvath** (nearby, has port): $50/unit steel + $4 sea shipping = **$54 landed**
> - **Nordvik** (far, no direct sea): $45/unit steel + $36 railroad shipping = **$81 landed**
> - **Drakmoor** (sanctioned, cheap steel): $30/unit steel + $24 railroad... but sanctions block the trade entirely
>
> If war disrupts the Korvath sea lane, suddenly Nordvik's $81 becomes the only option — and every company in Solhaven sees margins collapse.

##### [NEW] Infrastructure Construction & Strategic Assets
- **Grid-Based Construction**: The map is divided into a fine **triangular grid**. When Presidents invest in new railroads, they don't just click a button — they physically **trace the route** line-by-line across the triangles.
- **Project Creation & Approval Flow**: Both the government (Presidents) and companies (Executives) can create new infrastructure projects like building new routes. The government directly builds and approves these projects. Executives, however, propose (lobby) projects to the government; these lobbied projects appear in the Presidential dashboard for final approval.
- **AI Route Generation & Corruption Mechanic**: When creating routes, both Presidents and Executives have the option to trace routes manually or generate them with AI (using the optimized route builder algorithm). However, the AI has a **3% chance of choosing an unoptimized route** (adding 3-6 unnecessary tiles). If the Executives and Presidential cabinet both fail to review the route and it gets built, *PangeaNews* will generate an article exposing the scandal. The article will highlight the millions of extra tax dollars wasted, suggesting money laundering or a corruption scheme, which heavily penalizes the government's approval rating and the company's reputation. **However, if the Executives fail to review the proposed unoptimized route but the Government catches the error during approval, the Government will reject the project and apply a financial penalty to the company, negatively impacting their profit reports.**
- **Distance, Terrain Costs & Timeframes**: The cost of railroads depends heavily on the length of the traced route. Furthermore, construction is not instant. When planning a route, the system calculates a **construction timeframe** based on distance and terrain (e.g., 6 months [0.5 rounds], 1 year [1 round], 1.5 years, 2 years). Presidents must weigh this time delay when deciding whether to build a long railroad vs. utilizing existing routes.
- **Mountain Ranges**: The map features impassable or highly restrictive mountain ranges. These natural barriers make railroad-building incredibly difficult, forcing presidents to either build long, expensive routes *around* the mountains or rely on premium air freight infrastructure.
- **River Crossings (Bridges)**: If a traced railroad crosses a river tile, a bridge must be built. Bridges cost **3x the price** of a normal railroad segment.
- **Airports & Hubs**: Airports are located exclusively in the largest cities (cities spanning 2 triangles). These large cities serve as the major logistics hubs for their respective countries.
- **Starting City Allocation**: Each nation starts with exactly **8 cities total**. Large cities, small cities, and port cities all count toward the same total of 8; ports are not extra settlements.
- **Port City Placement**: Nordvik and Lunara each start with exactly **2 port cities**. Drakmoor starts with exactly **1 port city**, reflecting limited coastal access rather than complete landlock. All other nations (Valdoria, Terranova, Korvath, Solhaven, and Zephyria) start with **0 port cities**. Zephyria is fully landlocked with no coastal access. Where coastline length permits, a nation's two ports are distributed near the 1/3 and 2/3 marks of its eligible coastline. Ports are strictly forbidden from spawning within 2 triangles of another country's border, within 3 triangles of an impassable mountain range, or on tiles entirely enclosed by mountains. Lunara remains an exception to the distribution pattern: its two ports may cluster on the Strait of Lunara because of its dedicated 2-3-triangle-thick southern mountain range. If preferred positions are invalid, deterministic fallback selection must find other eligible coastal cities without changing the required count.
- **Starting Railroad Networks**: At the start of the game, every small city (1-triangle) is automatically connected to its nearest large city/airport hub via pre-built railroad networks. The paths are algorithmically plotted to avoid impassable terrain and minimize the number of expensive river crossings.
- **Destructible Assets**: War can destroy infrastructure. Enemies can bomb bridges (severing vital railroad connections), blockade ports, and mine sea lanes.
- **Strategic Chokepoints**: Straits and canals can be blockaded by naval forces, disrupting trade for multiple nations simultaneously.
- **Zephyria's Challenge**: Positioned as a landlocked crossroads between Nordvik and Drakmoor with no sea access. Its core strategic challenge is negotiating overland road access through neighboring nations to reach resources. Its primary asset is **cheap labor** — when other nations open new cities, Zephyria's workforce is the most affordable option, creating natural diplomatic leverage. However, its lack of ports makes it entirely dependent on land routes and vulnerable to being squeezed by neighbors controlling transit.

---

#### The 8 Nations of Pangea

##### [NEW] Nation design document
Each nation is designed to mirror real-world archetypes without mapping 1:1 to any real country, following the guidelines:

| Nation | Archetype | Key Resources | Economic Profile |
|:---|:---|:---|:---|
| **Valdoria** | Resource-rich, politically complex | Oil, natural gas, minerals | High commodity exports, developing manufacturing |
| **Lunara** 🏝️ | Middle East-like peninsula | Highest oil production, technology, fisheries, renewable energy | High-skill economy, **small land connection (strait)** — most trades made by sea |
| **Terranova** | Agricultural powerhouse | Grain, livestock, timber, freshwater | Food exporter, growing middle class |
| **Korvath** | Industrial manufacturing hub | Steel, chemicals, labor | Export-driven manufacturing, trade surplus |
| **Solhaven** | Financial & services center | Capital, banking, insurance | Financial hub, **Headquarters of the IMF**, low resources, high GDP per capita |
| **Nordvik** | Northern resource frontier | Rare earth minerals, timber, oil | Rich resources, harsh climate, small population |
| **Zephyria** | Landlocked emerging market | **Cheap labor** (primary), limited local resources | Landlocked crossroads between Nordvik and Drakmoor, no sea access, must negotiate road access through neighbors, rapid urbanization fueled by labor exports |
| **Drakmoor** 🤖 | Marginalized military state (AI-controlled) | Iron, coal, weapons manufacturing | Sanctioned economy, strong military, isolated, with one strategically vulnerable starting port |

> [!NOTE]
> Each nation is intentionally designed with **asymmetric advantages and vulnerabilities** to force trade and diplomacy. No nation can be self-sufficient — this is a core design principle that teaches interdependence.

> [!WARNING]
> ### 🏝️ Lunara — The Strait Strategy
> Lunara has only a **small land connection (strait)** with the mainland. Like a Middle Eastern peninsula, this creates unique challenges and advantages:
> - **Most imports and exports arrive by sea** — limited railroad options through the narrow strait. Minimum shipping cost is ~$2/unit (sea) for most volume
> - **Food insecurity** — Lunara has fisheries but no agriculture. It must import grain, livestock, and timber from the mainland at premium shipping costs
> - **Vulnerable to naval blockade** — if a hostile nation (e.g., Drakmoor) blockades Lunara's ports or the strait, the entire economy grinds to a halt
> - **Weather disruptions** — storms can temporarily shut down sea lanes to Lunara, cutting off supplies for 1-2 rounds
> - **High cost of living** — imported goods drive up consumer prices, making Lunara's CPI naturally higher than mainland nations
> - **Compensating strengths** — Lunara's technology exports and renewable energy are highly valued, and its island position makes it hard to invade by land. Its educated workforce commands premium prices for tech and services
>
> This mirrors real-world island economies (Iceland, Japan, Singapore, New Zealand) that must navigate the constant tension between geographic isolation and global trade dependency.

---

#### 🤖 Drakmoor — The AI-Controlled Antagonist Nation

Drakmoor is the **8th nation**, fully controlled by an AI agent (not played by students). It serves critical educational purposes:

**Backstory & Context:**
- Drakmoor was once a prosperous industrial power but has been **marginalized by international sanctions** due to authoritarian governance and aggressive posturing
- Its economy is suffering — limited access to global markets, rising unemployment, crumbling infrastructure
- Its coastline supports exactly **one starting port**, creating a vulnerable maritime chokepoint without making the nation fully landlocked
- However, it has maintained a **disproportionately strong military** (spending 40%+ of GDP on defense)
- Its AI-driven leadership grows increasingly desperate and nationalistic as sanctions bite harder each round

**Behavioral Programming — Randomized Per Game Instance:**

At the start of each new game, Drakmoor's AI agent rolls a **randomized profile** so that no two games play out the same way. Students who replay the game cannot assume Drakmoor's behavior:

| Randomized Element | Possible Values |
|:---|:---|
| **Primary Motivation** | Resource hunger (targets resource-rich nations), territorial expansion (targets neighbors), ideological rivalry (targets the most prosperous nation), revenge (targets whoever led the sanctions) |
| **Target Nation** | Any of the 7 player nations — weighted by proximity and motivation (e.g., attacks Korvath for steel in one game, Lunara for technology in another, Terranova for food in another) |
| **Aggression Timeline** | War initiation randomly falls between rounds 2-5; pre-war diplomacy length varies |
| **Diplomatic Personality** | Cold & calculating, erratic & unpredictable, publicly aggressive, or deceptively friendly before striking |
| **War Strategy** | Blitzkrieg (fast, concentrated attack), war of attrition (slow escalation), proxy conflict (funds instability in target nation first), or naval blockade |
| **Post-War Behavior** | Seeks peace if losing, doubles down if winning, fragments into civil war, or pivots to a new target |

- **Round 1**: Drakmoor always begins with diplomatic overtures — but the *tone* varies (friendly trade proposals vs. threatening demands). It **actively seeks alliances** with player nations, offering cheap resources, military cooperation, or favorable trade terms
- **Rounds 2-5**: War is initiated based on the rolled timeline. The buildup includes escalating news events, troop movements reported in the Pangea Times, and rejected ultimatums. Drakmoor will vote against any sanctions targeting itself or its allies in the FMI
- **Alliance strategy**: Drakmoor specifically targets nations that are economically struggling or diplomatically isolated — offering them a lifeline that comes with international consequences. Any nation that aligns with Drakmoor risks sanctions from the other nations and reduced FMI lending access
- **Post-war**: Behavior adapts dynamically based on both the randomized profile AND the actual outcomes
- The instructor can view (but students cannot see) Drakmoor's rolled profile for the current game via the GM panel

**Educational Purpose:**
- Forces students to deal with **geopolitical instability they didn't cause**
- Teaches that sanctions have consequences (pushing nations toward desperation)
- Creates urgency for military preparedness, intelligence gathering, and alliance formation
- Shows how war disrupts supply chains, trade routes, and commodity prices for ALL nations — even those not directly involved
- Mirrors real-world scenarios where conflict emerges from marginalization and economic isolation

> [!IMPORTANT]
> Drakmoor's actions should generate **ripple effects** across the entire game world:
> - Commodity prices spike (especially energy, metals)
> - Trade routes through conflict zones are disrupted
> - Nations must choose sides or stay neutral (diplomatic pressure)
> - Companies face supply chain disruptions and must find alternative sourcing
> - The "Pangea Times" news feed covers the crisis extensively

---

### Phase 2 — Multiplayer & Round System

##### [NEW] Drakmoor AI agent
- AI decision engine with weighted randomization for diplomatic and military actions
- Configurable aggression timeline (default: war between rounds 2-5)
- Instructor override capability (GM can adjust Drakmoor's behavior mid-game)
- Drakmoor's actions generate automatic news articles and market disruption events

##### [NEW] Authentication & session management
- User registration with role assignment (President vs. Company Executive)
- Team formation and nation assignment
- **Customization (Round 1):** Users have the option to change their assigned Nation's name or Company's name during the first round to increase team identity and ownership. **Strict content moderation filters** will block offensive, profane, or blasphemous names to maintain a professional educational environment.
- **Independent Game Sessions:** The architecture supports multiple concurrent game sessions that run completely independently.
- **Session-Locked Map Generation:** When a new session is started, a random seed is generated to procedurally create the map (rivers, mountains, cities, borders). Before persistence, the generated start state must pass all map invariants, including exactly 8 cities per nation, exactly 2 ports for Nordvik and Lunara, exactly 1 port for Drakmoor, 0 ports for all other nations, exactly 1 passable edge per mountain triangle, and zero passable edges touching ocean. After this initial validated creation, the map is locked for that session. The map will only get updates and upgrades based on users' decisions (like building roads) across the 7 rounds.

##### [NEW] AI bot backfill system
If there aren't enough students to fill all roles, **AI bots automatically fill empty slots** so the game world always runs at full capacity:

**How it works:**
- The instructor sets up a game and assigns students to nations/companies
- Any **unfilled president seat** is run by an AI bot (similar to Drakmoor, but non-antagonistic — plays as a rational, moderate leader)
- Any **unfilled company slot** is run by an AI bot that makes reasonable business decisions (competitive but not dominant)
- AI bots are clearly labeled in the UI with a 🤖 icon so students know which actors are human vs. AI

**AI Bot Difficulty Levels:**

| Level | Behavior | Best For |
|:---|:---|:---|
| **Passive** | Makes safe, conservative decisions — easy to outcompete | Small classes, introductory courses |
| **Balanced** | Makes competent decisions — realistic competition | Standard gameplay |
| **Aggressive** | Plays to win — challenges students to perform | Advanced courses, experienced students |

**Scaling scenarios:**

| Class Size | Setup |
|:---|:---|
| **200+ students** | All 7 nations fully student-run, no bots needed |
| **100-200 students** | 4-5 student nations, 2-3 AI-run nations with AI companies |
| **50-100 students** | 2-3 student nations, rest AI-run; fewer companies per student nation |
| **20-50 students** | 1-2 student nations, rest AI-run; students focus on company roles |
| **< 20 students** | 1 student nation (all students are company execs + 1 president), 6 AI nations |

- The instructor can **swap a bot for a student** mid-game (e.g., a late-joining student takes over an AI company)
- AI bots submit decisions automatically during the submission phase — no waiting
- Bot-run nations still participate in **sanctions votes, trade proposals, and FMI lending** — creating a living world regardless of class size

> [!NOTE]
> This means PangeaWorld works for a class of 10 students or 300 students. The game world always has 8 nations, 80-120 companies, trade, diplomacy, and conflict — the only variable is how many of those actors are human.

##### [NEW] Round lifecycle system
```
┌─────────────┐     ┌────────────────┐     ┌────────────────┐     ┌─────────────┐     ┌──────────────┐
│  PLANNING   │────▶│ DAY 1: PRES.   │────▶│ DAY 2: COMPANY │────▶│ PROCESSING  │────▶│   RESULTS    │
│  Phase      │     │ Deadline       │     │ Deadline       │     │ Engine      │     │  & Debrief   │
│             │     │                │     │                │     │ Calculates  │     │              │
│ • Review    │     │ • Companies    │     │ • Policies &   │     │ • Economy   │     │ • Updated    │
│   results   │     │   lobby Pres.  │     │   Tariffs lock │     │ • Military  │     │   dashboards │
│ • Analyze   │     │ • Presidents   │     │ • Companies    │     │ • Events    │     │ • News feed  │
│   data      │     │   set macro    │     │   submit micro │     │ • Trade     │     │ • Rankings   │
│ • Consult   │     │   policy       │     │   decisions    │     │ • Results   │     │ • AI debrief │
│   AI        │     │                │     │                │     │             │     │              │
└─────────────┘     └────────────────┘     └────────────────┘     └─────────────┘     └──────────────┘
```

##### [NEW] Trade & diplomacy system
- Proposal/acceptance workflow for trade deals
- Treaty templates (mutual defense, trade agreements, non-aggression pacts)
- Tariff mechanics (set per nation, per product category)
- Public vs. secret negotiations

##### [NEW] Fundo Monetário Internacional (FMI)
The FMI is a **multilateral financial institution** — the game's equivalent of the IMF — that provides loans to nations and enforces financial discipline:

**Lending Products:**

| Loan Type | Purpose | Terms | Conditions |
|:---|:---|:---|:---|
| **Emergency Credit** | Short-term liquidity crisis (can't pay military, infrastructure) | 1-2 rounds, high interest (8-12%) | Must be repaid quickly or credit rating drops |
| **Development Loan** | Long-term infrastructure, education, industrialization | 4-6 rounds, moderate interest (3-6%) | Requires reform commitments (e.g., reduce military spend) |
| **Bailout Package** | Nation on verge of economic collapse | Full game duration, low interest (1-3%) | Severe conditions: austerity, privatization, oversight |

**Lending Limits:**
- Each nation has a **credit allowance** based on GDP, debt-to-GDP ratio, international standing, and **most importantly, their direct financial contributions (quotas) to the FMI**. Presidents can invest national budget into the FMI to increase this limit.
- Nations under sanctions have **reduced FMI allowances** — less access to cheap capital
- Nations allied with Drakmoor face **further FMI restrictions** — the international community penalizes alignment with a sanctioned state
- **Automatic Sabotage Penalties**: If a nation or its companies are caught conducting covert sabotage, the FMI automatically freezes their credit access and imposes strict sanctions for 1-2 rounds
- Defaulting on FMI loans triggers automatic credit downgrades and trade penalties

**Educational Purpose:**
- Teaches how international financial institutions influence national policy
- Shows the tension between sovereignty and financial dependency
- Demonstrates how debt can constrain a nation's freedom of action
- Mirrors real-world IMF conditionality debates

##### [NEW] Sanctions voting system
Sanctions are **not automatic** — they require a democratic vote among all 8 presidents (including Drakmoor):

- Any president can **propose sanctions** against another nation (trade embargo, asset freeze, FMI restrictions)
- All 8 presidents vote: **simple majority (5 of 8)** passes a sanction
- Drakmoor gets a vote too — it will vote strategically (e.g., voting against sanctions on its allies)
- **Sanction types:**
  - 🚫 **Trade Embargo**: Blocks specific commodity trade with the sanctioned nation
  - 🏦 **Financial Sanctions**: Reduces the nation's FMI credit allowance by 30-50%
  - ⚓ **Shipping Restrictions**: Other nations' ports cannot service the sanctioned nation's cargo
  - 🔒 **Full Isolation**: Combination of all above (requires supermajority: 6 of 8)
- Sanctions can be **lifted** by a new vote (same majority threshold)
- **Consequences of aligning with Drakmoor**:
  - If a player nation votes consistently with Drakmoor or signs alliance/trade deals with it, other nations may propose sanctions against *them*
  - Their FMI credit allowance is reduced proportionally to the depth of the alliance
  - This creates a **diplomatic trap**: Drakmoor may offer cheap iron, coal, or military support, but accepting it risks international isolation

> [!IMPORTANT]
> The sanctions voting system teaches that **international pressure is a political process, not a rule of nature**. Students learn that sanctions require coalition-building, and that sanctioned nations still have agency (they can seek allies, circumvent restrictions, or retaliate).

---

### Phase 3 — Military, Events & News

##### [NEW] Military operations system
- Unit types: Infantry, Navy, Air Force (each with cost and capability)
- Operations: Attack, Defend, Blockade, Intelligence Gathering
- **Resolution: Attack Index vs. Defense Index** — each nation's ATK and DEF indices determine how many dice they roll (1–5 dice scaled by index level 1–10). Ties are won by the higher index. This replaces fixed RISK dice counts with a dynamic system that rewards sustained military investment. Outcomes remain randomized — war is unpredictable, but preparation matters.
  - Multiple engagement rounds per battle, with the option to retreat
  - Indices grow through sustained investment over multiple rounds (infantry, navy, air force, technology, fortifications, intelligence)
  - This teaches that **military capability is a long-term strategic investment**, not a panic buy
- Costs: Military spending directly reduces money available for economic investment (teaching opportunity cost)
- **War ripple effects**: Active conflicts disrupt trade routes, spike commodity prices, and trigger refugee/humanitarian events

##### [NEW] Dynamic event engine
- **Instructor-triggered events**: GM panel to inject custom scenarios
- **Scheduled events**: Pre-programmed events tied to round numbers
- **Reactive events**: Triggered by game state (e.g., if a nation's CPI exceeds 115, trigger "civil unrest")
- **Frequency & Scale**: A standard game contains **3 major events** (massive disruptions) and **10-12 minor events** randomly distributed throughout the game. Minor events usually require financial investments to rebuild or recover.
- Event categories:
  - 🌪️ Natural disasters & Hazards (earthquakes, twisters, hurricanes, tsunamis, oil leakages, droughts)
  - 📰 Political crises (coups, elections, protests)
  - 📈 Market shocks (commodity price spikes, financial crises)
  - 🦠 Health emergencies (pandemics, supply disruptions)
  - 🔬 Technology breakthroughs (new resource discovery, innovation)

##### [NEW] "Pangea Times" news system
- AI-generated news articles reflecting game events in journalistic style
- Market reports with charts and data
- Opinion pieces that introduce bias (teaching media literacy)
- Some articles contain **deliberate misinformation** (teaching source verification)

---

### Phase 4 — AI Integration & Analytics

##### [NEW] Gemini AI advisor integration
- Per-user chat interface with persistent conversation history
- **Global Event Ledger (Knowledge Base)**: The game maintains a complete, immutable ledger of every action, disaster, decision, deal, rejected proposal, and news event. The AI advisor queries this ledger to provide context-aware advice grounded in the exact history of the current game instance.
- **System prompt engineering**:
  - Company advisors: Knowledgeable about business strategy, supply chain, finance
  - President advisors: Knowledgeable about macroeconomics, geopolitics, military strategy
  - Both: Will NOT give direct answers — uses Socratic method to guide thinking
  - Both: Has access to the user's game data for contextual advice
- **AI usage logging**: Track all AI interactions for instructor review
- **Guardrails**: AI cannot reveal other players' secret decisions or provide optimal solutions

##### [NEW] Instructor analytics dashboard
- Per-student engagement metrics (decisions made, AI usage, login frequency)
- Learning outcome tracking (did decision quality improve over rounds?)
- Game balance monitoring (is one nation too dominant?)
- Export functionality for grades and reports

##### [NEW] Post-game debrief tools
- Historical playback of all rounds
- "What-if" analysis (what would have happened if X decision was different?)
- Connection to real-world examples: "Your nation experienced Y — here's when that happened in the real world"

---
