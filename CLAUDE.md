# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Context

**Hackathon: Agentic GTM** — July 9, 2026
**Track: Track 1 – Acquisition**

**Mandatory APIs (must all be used meaningfully):** Anthropic Claude, FullEnrich (contact enrichment), Sillage (intent signals)

**Judging criteria (25 pts each):** business impact, depth of AI use (Anthropic), depth of external data use (FullEnrich + Sillage), presentation quality.

**Deliverables:** 2-min demo + GitHub repo + short description. Built entirely today. Pitch format: 1:30 pitch / 1:30 demo / 2:00 Q&A.

---

## The Idea (locked)

### Problem

Traditional industrial SMBs (non-digital-native, often founder-led) sell in **capped markets**: the number of factories and warehouses in Europe is finite and known. You can't grow the pie — growth only comes from catching a prospect at the rare moment demand materializes (new site, extension, equipment renewal, relocation). Miss that window and the deal goes to the incumbent supplier for 10-15 years.

These companies have no CRM, no LinkedIn presence, no marketing team. They prospect via trade shows and word of mouth — so they systematically miss those buying moments.

**Pitch line:** *"In a capped market, you don't find new customers — you catch existing ones at the rare moment they're buying."*

### ICP (the user of our product)

B2B industrial European company: 5-50 white collar employees, up to 250 total. Sells physical products/services to **factories and warehouses** (industrial doors, racking, conveyors, packaging lines, cooling, industrial maintenance...). NOT SaaS, not virtual.

**Demo persona:** Martine, 58, sells industrial racking systems in Lyon, 30 employees.

### Scope decision

**France only for the build** (best free open data). **Pitch as expandable to EU** — every EU country has equivalent registries (permits, company registers, environmental permits).

---

## How It Works: Signal-First → Account Mapping

Instead of searching for companies and hoping they need our user's product, the agent **detects signals that prove an industrial project is happening**, then maps the whole ecosystem of stakeholders around that project.

### Pipeline

1. **Profile extraction** (Claude) — parse plain-language input ("je vends des rayonnages industriels, 30 salariés, Lyon") → product category, buyer profile, region
2. **Signal detection** (open data APIs) — scan for live buying signals in the region (see table below)
3. **Account mapping** (Claude reasoning) — for each signal, identify the ecosystem: site owner/operator, general contractor, engineering firm (maître d'œuvre) — and rank who to contact first and why
4. **Contact enrichment** (FullEnrich) — decision-maker names, emails, phones for each mapped account
5. **Outreach generation** (Claude) — plain-French email per contact referencing the specific project/signal

### Signals (France)

| Signal | Source | Meaning |
|---|---|---|
| Building permit — industrial/warehouse | SITADEL (data.gouv.fr) | New capacity 6-18 months out |
| **ICPE registration/modification** | Géorisques / préfecture publications | Factory expansion — legally required, publicly published, **nobody in GTM uses this** |
| New establishment opening | BODACC / Sirene | Site being fitted out now |
| Hiring production/warehouse staff | France Travail API | Capacity ramping |
| Capital increase / M&A | BODACC / Pappers | Capex incoming |
| Digital intent | Sillage | Intent layer on top |
| Public tenders (secondary) | BOAMP | For public-sector industrial projects |

ICPE is the differentiator — lead with it for the "Most creative GTM angle" side challenge.

Do NOT scrape LinkedIn. FullEnrich is the contact data source.

### The wow moment

The outreach email references a real, specific event: *"votre permis pour l'extension de 12 000 m² à Saint-Nazaire..."* — feels like 2 hours of research, done in 90 seconds, for someone who has never used a CRM.

---

## Demo Script (2 min)

1. **0:00–0:15** — "Martine, 58, sells industrial racking in Lyon. No CRM, no marketing team. Her market is capped — she grows only by catching factories at the moment they expand."
2. **0:15–0:35** — Type one sentence into the UI. Agent streams visibly: profile → signal scan → mapping.
3. **0:35–1:10** — Live results: "X industrial permits + ICPE filings found in Auvergne-Rhône-Alpes → 8 live projects → ecosystem mapped per project." Ranked list with signal badges.
4. **1:10–1:40** — Click top project: stakeholder map (owner, contractor, engineering firm) + enriched contacts + email draft referencing the specific permit.
5. **1:40–2:00** — "8 live projects, the right person to call for each, ready-to-send emails. 90 seconds. No CRM, no LinkedIn."

**Critical:** agent steps must stream visibly in the UI. A blank loading screen loses judges.

---

## Key Risks & Mitigations

- **Sillage coverage on French industrial SMBs may be thin** — test the API first. If sparse, BODACC/SITADEL/ICPE carry the intent story; use Sillage for whatever it covers and be explicit: "we cross 6 data sources."
- **FullEnrich coverage of French SMB contacts may be 40-60%** — pre-enrich a real demo dataset so the live demo never shows a blank card.
- **SITADEL data freshness/format** — it's published as datasets, not a live API. May need to pre-download and filter. Check early.
- **Account mapping (permit → who's the contractor?)** — hardest step. May require Claude web search or press-release lookups. If too hard for today, ship owner/operator contacts only and present the full map as vision.

## What to Cut (1-day build)

- Multi-channel cadences → email only
- A/B testing → skip
- Real email sending → copy-paste output only
- Auth / multi-tenant → single-user demo
- Multi-country → France only

---

## Tech Stack (locked)

- **Python + SQLAlchemy**; SQLite (`data/gtm.db`) as the local working store — raw signals + classification queue. Schema in `backend/db.py`.
- **HubSpot CRM is the data store for GTM output** (mapped accounts, enriched contacts, outreach drafts) — portal 148865690, wired 09/07, see `docs/hubspot.md`. **Not Supabase** — that option is dropped.
- FastAPI + Streamlit for the app/demo layer.

## Next Steps

- [ ] Test Sillage API — actual coverage for French industrial companies
- [ ] Test FullEnrich API — enrich a sample French industrial contact
- [ ] Check SITADEL + ICPE data access — live API vs. dataset download
- [ ] Test Pappers/Sirene + BODACC queries
- [x] Decide tech stack — Python/FastAPI + Streamlit; SQLite working DB + HubSpot as GTM data store (no Supabase)
- [ ] Scaffold repo, build pipeline demo-first
- [ ] Pre-build the demo dataset (real signals, pre-enriched contacts)

---

## Side Challenges

- **Most creative GTM angle** — lead with ICPE (environmental permits as buying signals)
- **Best use of Gamma** — auto-generate a Gamma "project brief" per mapped account
- **LinkedIn / X virality** — tag Anthropic, Sillage, FullEnrich; #agenticgtm on X

## Skills (the engine's brain — .claude/skills/)

`/goal` orchestrates the whole engine from one plain-language sentence. It chains: `atlas` (map 100% of the finite market, evidence per line) → `enrich-accounts` (FullEnrich decision-makers, credit-aware) → `signal-watch` (BOAMP + Sillage → HubSpot priorities, corroboration model) → `approach-draft` (signal + contact → first touch, human swipe gate). Each skill runs standalone too. Read the skill before reimplementing anything it covers.
