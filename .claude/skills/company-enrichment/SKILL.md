---
name: company-enrichment
description: Pull decision-makers (names, emails, phones) for atlas accounts via FullEnrich and write them into HubSpot as contacts associated to their company. Use after the atlas exists, when asked to "enrich accounts", "find the contacts", "get me the decision makers", or as step 2 of /goal. Credit-aware — emails by default, phones only for hot accounts.
---

# Enrich accounts — decision-makers via FullEnrich

Wrapper: `backend/enrich/fullenrich.py` (importable + CLI). Docs: `docs/fullenrich.md`. Key already wired in `.env`.

## Credit economics (hard rules)

Work email = 1 credit · **phone = 10** · personal email = 3 · people-search result = 0.25. Only charged on found results. Budget ~2,500 credits total.

- Enrich `contact.work_emails` for every account.
- Add `contact.phones` ONLY for `gtm_priority = hot` accounts.
- Check balance before and after each batch (`credits` command); log consumption.
- All wiring tests use the zero-credit test contact (`test` command), never a real contact.

## Flow per account

1. **Find the right people**: `POST /people/search` filtered by company domain + roles. Finite-market buyer roles, in order: CEO/gérant (SMBs: the owner decides), plant/site director, purchasing manager, technical/maintenance director. Take top 3 per account max (curation beats volume).
2. **Enrich**: bulk POST (≤100 contacts), then poll `result <enrichment_id>` until `FINISHED`. Include `linkedin_url` whenever search returned one (better hit rates + full profile payload).
3. **Write to HubSpot**: upsert contact (email as dedup key), then associate to the company (`PUT /crm/v4/objects/companies/{cid}/associations/default/contacts/{vid}`). Store job title, phone if enriched.
4. **Report**: per account — contacts found / emails deliverable / phones found / credits spent. Accounts with 0 contacts go in a `needs-manual` list, never silently dropped.

## Rules

- Never enrich accounts outside the atlas (no spray).
- `DELIVERABLE` and `HIGH_PROBABILITY` emails are usable; `CATCH_ALL` flagged as risky; never output `INVALID`.
- Re-running is safe: FullEnrich dedupes re-enrichment within 3 months at 0 credits.
