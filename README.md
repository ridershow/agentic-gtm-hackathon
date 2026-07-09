# Finite-Market GTM Engine

### Agentic GTM Hackathon — Anthropic × FullEnrich × Sillage · STATION F · 09/07/2026

A monitoring engine for industrial SMBs selling in **finite markets**. It maps 100% of the addressable market (live demo base: 23 real French aluminium-extrusion plants), enriches decision-makers through a provenance-tagged waterfall (FullEnrich → company registry → Sillage — each source catches what the others miss), and watches every account for real-world buying signals, surfaced in a swipe interface. **Deliberately no AI outreach**: big-ticket industrial deals stay human — the engine makes sure the human never misses the moment. When a meeting lands, one click generates an on-brand meeting brochure (Gamma) from live CRM data.

**Interface (Lovable):** https://github.com/AlexHoudz/smb-ai · **Demo script:** [DEMO.md](DEMO.md) · **Pitch:** [PITCH.md](PITCH.md)

## The three goals (each a loop of skills — `.claude/skills/`)

1. **Territory Coverage** — one plain-language sentence in → 100% of the finite market mapped with evidence per line (registry sweep + discovery nets + saturation proof) → HubSpot.
2. **Company Enrichment** — FullEnrich people-search → registry fallback (SIRENE dirigeants) → Sillage account mapping. Every contact provenance-tagged; gaps flagged `manual_search`, never dropped.
3. **Signal Watcher** — open data + Sillage agents + Claude ICP scoring. Corroboration model: administrative proof + market buzz = hot. Managed agents (watcher + cleaner, `automations/`) keep the base fed and trustworthy on schedule.

## Stack

Claude (engine + skills) · HubSpot (source of truth) · FullEnrich (contacts) · Sillage (account mapping + intent) · French open data (SIRENE, registries) · Gamma (meeting brochures + deck) · Lovable (interface).

## Run it

```bash
cp .env.example .env            # ANTHROPIC / FULLENRICH / SILLAGE / HUBSPOT / GAMMA keys
python -m backend.ingest.seed_atlas --check          # what's in HubSpot
python -m backend.enrich.enrich_hot --priority hot   # decision-makers → HubSpot
python -m backend.enrich.contact_router              # registry fallback loop
python -m backend.ingest.sillage_watch pull          # Sillage → HubSpot
python -m backend.agents.cleaner --dry               # data hygiene report
python -m backend.agents.brochure --company "X"      # meeting brochure (Gamma)
./automations/install.sh                              # schedule watcher + cleaner
```

Docs routing: [docs/_index.md](docs/_index.md). Built entirely on 09/07/2026.
