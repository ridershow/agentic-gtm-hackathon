# FullEnrich v2 — wired ✅

Key live in `.env`, workspace verified, **2,505 credits** (09/07). Wrapper: `backend/enrich/fullenrich.py` — importable (`verify/credits/enrich/result`) + CLI (`python -m backend.enrich.fullenrich test`).

## Endpoints

| What | Endpoint |
|---|---|
| Key check | `GET /account/keys/verify` |
| Credits | `GET /account/credits` |
| Enrich (≤100/bulk) | `POST /contact/enrich/bulk` → `enrichment_id` |
| Result | `GET /contact/enrich/bulk/{id}` (webhook exists; polling fine for demo) |
| Search people / companies | `POST /people/search` · `POST /company/search` (0.25 credit/result) |
| Company lookup by domain | `POST /company/lookup` |
| Reverse email | `POST /contact/reverse/email/bulk` |

## Credit economics (shapes the build)

Work email = **1** · phone = **10** · personal email = 3 · search = 0.25/result. Only charged when found. Re-enrich within 3 months = free. → Enrich `contact.work_emails` across the atlas; pull phones only for signal-hot accounts.

## Zero-credit testing

`python -m backend.enrich.fullenrich test` — hardcoded FullEnrich-team contact, free, returns full payload (email + profile + company object). Use for all wiring tests.

## Input per contact

`first_name`+`last_name`+`domain`/`company_name`, or `linkedin_url` (better hit rates + returns full profile: title, location, headcount).

## Docs

Index: `https://docs.fullenrich.com/llms.txt` — every page serves clean `.md` (append `.md` to the URL). Context7: `/websites/fullenrich_api_v2`. MCP alt: `https://mcp.fullenrich.com/mcp`.
