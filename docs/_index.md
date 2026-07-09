# docs/ — routing

- `hubspot.md` — HubSpot wiring + **current portal state** (seeded accounts, contacts, properties, queries). Read before touching HubSpot.
- `fullenrich.md` — FullEnrich endpoints, credit economics, zero-credit testing. Read before any enrichment.
- `sillage-integration.md` — Sillage v2 endpoints + gotchas. Read before pulling signals.
- `gamma.md` — Gamma deck generation API (used for the presentation, not the engine).
- `architecture.md` — signal ingestion flow + build order. Schema SOT is `backend/db.py`, not this file.
- `market-analysis.md` + `icp-breakdown.md` — **pitch/deck inputs only, do not load at runtime** (market figures + ICP category detail; classify.py embeds what the engine needs).

Engine behavior lives in `.claude/skills/`, tasks in `TODO.md`, pitch in `PITCH.md`.
