# HubSpot — wired ✅

Private app token in `.env` (`HUBSPOT_TOKEN`). Portal **148865690** (eu1, fresh hackathon portal). Base: `https://api.hubapi.com` (works for eu1). Smoke-tested 09/07: account info, company create/read/archive all 200.

## Custom properties (created, live on companies)

| Property | Type | Purpose |
|---|---|---|
| `gtm_signal` | textarea | Latest buying signal (BOAMP / open data / Sillage) |
| `gtm_signal_date` | date | When the signal fired |
| `gtm_priority` | select: hot / warm / watch | Agent ranking |
| `gtm_approach_draft` | textarea | UNUSED — outreach cut from product 09/07 pm (deliberate positioning choice). Property exists in portal, nothing writes it. |

## Core calls

- Upsert company: `POST /crm/v3/objects/companies` (search by domain first: `POST /crm/v3/objects/companies/search`)
- Upsert contact: `POST /crm/v3/objects/contacts` (+ associate: `PUT /crm/v4/objects/companies/{id}/associations/default/contacts/{id}`)
- Note on account: `POST /crm/v3/objects/notes` + association
- Read queue for UI: `POST /crm/v3/objects/companies/search` filter `gtm_priority=hot`

## Current state (09/07 ~13:15) — READ ME, other Claude 👋

**HubSpot holds the demo atlas: 23 companies + 15 unique contacts (24 associations) with DELIVERABLE emails** (French aluminium-extrusion plants, public sources). Properties set per company: `siren` (join key for BOAMP/open data), `gtm_signal` (investment detail when known), `gtm_priority` (**7 hot / 5 warm / 11 watch**), domain (22/23), city, annualrevenue, description (type + legal entity + group).

- Query the base: `POST /crm/v3/objects/companies/search` with filter `siren HAS_PROPERTY`
- Hot queue: filter `gtm_priority EQ hot`
- Seeder code + dataset: **PR #3** (`backend/ingest/seed_atlas.py`, re-runnable upsert by siren) — data is live in the portal regardless of merge status
- Join your BOAMP signals on `siren`; Sillage watchlist should start from the 7 hot accounts

**Contacts (09/07 ~15:45): 29 contacts, 20/23 companies covered.** Two-stage waterfall:
1. `backend/enrich/enrich_hot.py` — FullEnrich people-search + verified emails (provenance `people_search`, 15 contacts)
2. `backend/enrich/contact_router.py` — registry loop for the rest: SIRENE dirigeants (auditors excluded) -> retry FullEnrich with the gérant's name -> push with provenance `registry` (email verified, 3) or `registry_no_email` (identity only, human finds the number, 11)

Contact property `gtm_provenance` tells the rep what's verified vs to-confirm. Still empty: AFE Ham, Extol France, Koalis (registry lists corporate officers only — group-level entities; needs-manual). ~57 credits spent total, 2,448 left.
