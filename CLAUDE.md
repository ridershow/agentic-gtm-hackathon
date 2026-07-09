# CLAUDE.md

Guidance for Claude Code in this repo. Two Claude instances (Alex's and Jeremy's) work here in parallel — keep docs single-truth, push often.

## Project

**Agentic GTM Hackathon — 09 Jul 2026, Track 1 Acquisition.**
Mandatory APIs, all used meaningfully: **Anthropic Claude, FullEnrich, Sillage.**
Judging 4×25: business impact · AI depth · external data depth (FullEnrich+Sillage) · presentation.
Deliverables: 2-min demo + repo + short description. Pitch format: 1:30 pitch / 1:30 demo / 2:00 Q&A.

## The product (positioning locked 09/07 pm)

**A monitoring engine for finite-market industrial SMBs.** The market universe (all accounts that could ever buy) is mapped once with the client; the engine then watches every account continuously — public tenders, open data, Sillage intent — and surfaces signals, including weak ones, in one interface. Sales reps cover more territory because the news-checking runs for them.

**Deliberately NO outreach generation.** In this market every deal is big-ticket and relationship-driven; the approach stays human and custom. The engine's job is to make sure the human never misses the moment. Say this as a product choice in the pitch, not a limitation.

The user is described in PITCH.md (persona lives there only). Live demo base: 23 real FR aluminium-extrusion plants in HubSpot + enriched contacts.

## Engine = the skills (.claude/skills/ — SOT for behavior)

`/goal` runs everything from one plain-language sentence: `atlas` (map 100% of the finite market, evidence per line, saturation stop rule) → `enrich-accounts` (FullEnrich decision-makers, credit-aware) → `signal-watch` (BOAMP ingest → Claude ICP scoring → Sillage → corroboration model → HubSpot priorities). **Read the skill before reimplementing anything it covers.**

## Run commands

```bash
cp .env.example .env                                        # keys: see docs/
python -m backend.ingest.boamp --departments 69,38,01 --days 90   # tenders → signals table
python -m backend.workers.classify --limit 50               # Claude scores signals vs ICP
python -m backend.enrich.fullenrich test                     # FullEnrich wiring test (0 credits)
python -m backend.enrich.enrich_hot --priority hot           # decision-makers → HubSpot
python -m backend.ingest.seed_atlas --check                  # what's in HubSpot
```

## Data stores

- **SQLite `data/gtm.db`** — raw signals + classification queue. Schema SOT: `backend/db.py`.
- **HubSpot portal 148865690** — GTM output (companies, contacts, priorities). Guide + current state: `docs/hubspot.md`.
- API wiring docs: `docs/_index.md` routes them.

## Rules

- `main` is the demo branch — never commit to it directly; use the `/feature` skill (branch + PR).
- TODO.md = task SOT, owner-tagged. Update your line when you ship.
- Do NOT scrape LinkedIn. FullEnrich is the contact source.
- No client names, no persona names outside PITCH.md.
- Demo never fakes: pre-computed real runs may be skipped-to, never invented.
