# TODO — live board

**This repo = source of truth. Notion is frozen as scratch notes.** Update checkboxes here; anything new gets a line here, not a Notion block.

## Setup

- [x] Team repo + push access (Alex ✅, Claude Code ✅)
- [x] FullEnrich — key wired, tested live, 2,505 credits (`docs/fullenrich.md`)
- [ ] Anthropic API keys — each redeems own $100 link (one code per org!) → `.env`
- [ ] HubSpot — fresh portal (NOT a client's) + service key → `.env` — **Jerem**
- [ ] Sillage — team workspace at hackathon.getsillage.com + key + MCP connect — **Alex**
- [ ] Gamma API key — **Alex**

## Alex

- [ ] **Atlas** — NAF codes + annuaire + third-party sources → `organizations` table
- [ ] **FullEnrich account mapping** — decision-makers per account → push into HubSpot
- [ ] **Managed Agent** — monitoring + feeding, HubSpot bilateral read/write

## Jerem

- [x] BOAMP ingestion scaffold (signals table, SQLite/Postgres)
- [ ] Clean HubSpot + connectors management
- [ ] Sillage intents from FullEnrich output → HubSpot

## Afternoon (shared, timeboxed)

- [ ] Lovable swipe UI — separate GitHub-synced repo, rebuilt fresh (LCF learnings, no old commits). Start **15:30-16:00 latest**; first thing cut if the engine slips.
- [ ] Gamma deck — **Alex, 1h timebox** (also feeds "Best use of Gamma" side prize)
- [ ] 2-min demo run-through + screen-recording backup (demo gods insurance)
- [ ] Submit: repo + short description + demo before deadline (confirm deadline time on site)
- [ ] Optional: LinkedIn post tagging Anthropic + Sillage + FullEnrich (side prize)

## Demo flow (target)

One sentence in ("je vends des rayonnages industriels, 30 salariés, Lyon") → signals (BOAMP + open data + Sillage) → account map → FullEnrich contacts → drafted outreach → swipe to approve.

## Open questions

- Can the Managed Agent reach Sillage MCP / HubSpot from the cloud? Fallback: scheduled local run, demo unchanged.
- HubSpot vs local DB split: signals staging = SQLite (done), CRM/SOT = HubSpot. Confirm nothing needs more than that.
