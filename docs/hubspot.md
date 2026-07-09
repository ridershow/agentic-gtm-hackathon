# HubSpot — wired ✅

Private app token in `.env` (`HUBSPOT_TOKEN`). Portal **148865690** (eu1, fresh hackathon portal). Base: `https://api.hubapi.com` (works for eu1). Smoke-tested 09/07: account info, company create/read/archive all 200.

## Custom properties (created, live on companies)

| Property | Type | Purpose |
|---|---|---|
| `gtm_signal` | textarea | Latest buying signal (BOAMP / open data / Sillage) |
| `gtm_signal_date` | date | When the signal fired |
| `gtm_priority` | select: hot / warm / watch | Agent ranking |
| `gtm_approach_draft` | textarea | Drafted first touch, pending human swipe |

## Core calls

- Upsert company: `POST /crm/v3/objects/companies` (search by domain first: `POST /crm/v3/objects/companies/search`)
- Upsert contact: `POST /crm/v3/objects/contacts` (+ associate: `PUT /crm/v4/objects/companies/{id}/associations/default/contacts/{id}`)
- Note on account: `POST /crm/v3/objects/notes` + association
- Read queue for UI: `POST /crm/v3/objects/companies/search` filter `gtm_priority=hot`
