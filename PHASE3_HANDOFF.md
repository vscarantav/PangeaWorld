# Phase 3 implementation handoff

New instructor games use `phase3-closure-v1`. Existing databases migrate to
`legacy-v1` so previously accepted inputs remain compatible. Create a new game
to use the closure features; changing an active game's ruleset is unsupported.
The deferred 3D map roadmap remains separate.

## Decisions and teaching feedback

Submitting policy, readiness, or company decisions opens a server-quoted review.
It displays the selected allocation, feasible alternatives, remaining funds,
recurring wages, projected effects, and uncertainty. The player selects the
next-best alternative and writes a 20–2000 character rationale. A digest binds
the review to the session, round, entity, inventory, allocation, available funds,
and projections. Changed inputs require another comparison.

`POST /api/sessions/{id}/decision-review/{president|company}/{entity_id}` previews
without submitting. `decision_reviews` stores each accepted human submission as
an append-only record. Replacement submissions supersede earlier records for
resolution; earlier reasoning remains available without incorrectly attributing
the final outcome to it. `GET /api/sessions/{id}/phase3/decision-reviews` exposes
only the requesting player's records, or all records to the instructor. After
processing it includes actual results and clearly labeled submission-time
alternative estimates. It does not claim to simulate a full alternate history.
When no different feasible allocation exists, the review records that fact.

The instructor sees constraint recognition, considered alternatives, rationale,
and changes over rounds. The instructor-only `opportunity-cost-scorecard`
endpoint and readiness-board table aggregate participation, comparison rates,
and revisions. Evidence flags are not automatic grades for reasoning
quality. The Phase 4 advisor adapter is `advisor_prompt_for_review`; it requires
an already authorized review and asks Socratic questions about marginal choices.
The live advisor, general learning analytics, and full what-if replay remain
Phase 4 features.

Company production is capped at 2x and hiring at 100 per company. Production
reserves 10% of baseline COGS as working capital; expected sales fund remaining
operating costs. R&D, wages, sourcing, and working capital share available cash.
R&D quality gains use diminishing returns in the new ruleset. Recovery can
still cause losses; previews are not guaranteed profits.

## Military and events

There is one operation per president per round. Attack orders allow 1–3
engagements and a precommitted retreat threshold. A naval blockade costs $50M,
requires navy, and prevents foreign sea shipments involving its target while
naval forces survive. An intelligence mission costs $25M and provides its owner
with a private resolved-round readiness/posture observation. Other players see
only that a mission occurred. All operations compete with spending and the
single operation slot. Procurement becomes usable after operations.

Attacks resolve by stable nation ID. Prior losses reduce later deployments;
orders without surviving committed units are cancelled. Readiness contributes
a capped square-root bonus in the new ruleset, rewarding sustained investment
with diminishing returns. Active conflict adds 2 CPI points, reduces approval
by 2, reduces GDP by 1%, and raises foreign freight insurance from 2% to 7% for
affected nations. Humanitarian news identifies those aggregate effects; there
is no population migration simulation in this ruleset. A victory transfers one
abstract strategic control point when the defender has more than one remaining.
This models contested territory without changing fixed national borders or map
topology; a nation cannot lose its final point.

The seed schedules 3 major and 11 minor incidents over seven rounds. Additional
CPI-above-115 unrest uses a one-round cooldown. The instructor may add one
bounded scenario per round during planning or decision phases. Five categories
are supported. Natural disasters use severity-based preparedness/recovery;
other custom scenarios use bounded CPI and approval effects. Scenario prose is
data, never executable code.

Drakmoor's scripted mode gathers intelligence in year 1 and attacks from year 2,
keeping half its inventory available and retreating after sufficient losses.
The instructor can switch between scripted/passive during planning; changes
are recorded. Vacant seats receive recorded conservative automatic decisions.

## Gemini news

Configure these in the **backend process environment**, then restart it:

```text
GEMINI_API_KEY=<your server-side key>
GEMINI_NEWS_MODEL=<a generateContent-compatible model enabled for your account>
```

Do not put the key in a `VITE_` variable or commit it. The implementation uses
Google's [generateContent REST API](https://ai.google.dev/api/generate-content)
with `x-goog-api-key`, bounded output, and an eight-second request timeout.
One public market roundup is generated per resolved round and stored in round
results. GET requests never call Gemini. Only allow-listed public GDP, CPI,
inflation, trade balance, and event headlines are sent. Decisions, rationales,
planned deployments, and intelligence reports are excluded. Provider errors
produce a stored factual fallback without exposing error bodies or credentials.
Generated prose is labeled and shown beside source data and a CPI chart.
Opinion and unverified-claim exercises are explicitly identified as classroom
content, separate from authoritative results.

Live Gemini verification requires an enabled key/model; mocked transport checks
verify success, public-source filtering, and fallback but do not establish live
provider availability. Generated prose can be inaccurate; students can compare
it to the stored source data. News never changes simulation outcomes.

## Verification

Run backend tests from `backend`: `.venv/bin/python -m pytest tests -q`.
Run `npm test`, `npm run lint`, `npm run build`, and `npm run test:e2e` from
`frontend`. Do not edit source files while the Vite browser rehearsal runs:
hot reload can invalidate an in-flight dialog or context.

Closure tests cover seven-round automatic play, seven human-controlled nations
and Drakmoor across all rounds, repeated processing, causal losses, blockaded
stock transfers, private intelligence, authorized scenario controls, immutable
review history, stale previews, and private/public separation. These engine/API
rehearsals complement the isolated four-browser test; they are not a measured
production-scale concurrency benchmark.

Final local verification on September 10, 2026: 70 backend tests, 3 frontend
map tests, frontend lint, production build, and the isolated four-browser Chrome
rehearsal pass. The production build has a non-blocking approximately 510 kB
bundle warning. The workspace has no live Gemini key/model configured.

The next active product phase is the major **Phase 4 — AI Integration &
Analytics** section in the canonical roadmap. The deferred post-launch map
roadmap has its own internal phase numbers; its Phase 4 is road/city construction.
