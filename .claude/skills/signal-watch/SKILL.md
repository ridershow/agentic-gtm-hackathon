---
name: signal-watch
description: Run the watch loop — pull fresh buying signals from BOAMP (public tenders), open data and Sillage, score them against the ICP, match them to atlas accounts, and update HubSpot (gtm_signal, gtm_priority, note). Use when asked to "check signals", "what moved", "run the watch", on any scheduled/managed-agent run, or as step 3 of /goal.
---

# Signal watch — the heartbeat

The engine's whole promise: **know when one of the finite accounts moves, before competitors do.** Signals are real-world (tenders, permits, hiring, investments), not LinkedIn activity.

## Sources, in pipeline order

1. **BOAMP tenders**: `python -m backend.ingest.boamp --departments <dd,dd> --days <n>` → `signals` table (already built).
2. **ICP scoring**: `python -m backend.workers.classify` — Claude scores each raw signal 0-100 against the 5 ICP categories, writes `icp_relevance` (already built). Only signals ≥ 60 move forward; 30-59 = digest-only.
3. **Sillage** (API base `https://api.getsillage.com`, key in `.env`, endpoints in `docs/sillage-integration.md`): read new signals on watched accounts — job postings, keyword detections, competitor/customer interactions. The account watchlist = the atlas hot + warm tier (Sillage cap 20 accounts = exactly a finite market).
4. **Match to accounts**: join on `siren` when the signal carries one; otherwise geography (dept) + Claude reasoning over the account list ("which atlas account does this tender concern or benefit?"). A tender can also point at a NEW ecosystem player (contractor, engineering firm) → add as organization, kind=contractor.

## Priority update rules (corroboration model)

- Administrative proof alone (permit filed, tender published) → `warm`
- Market buzz alone (Sillage: hiring wave, expansion post) → `warm`
- **Both agreeing on the same account → `hot`**
- Nothing new in 90 days → decay one level (hot→warm→watch)

## Writes (HubSpot, via patterns in `docs/hubspot.md`)

- `gtm_signal` = 1-2 plain-French sentences a non-technical owner understands (reuse classify's summary style), `gtm_signal_date` = signal publication date (never today's date), `gtm_priority` per rules above
- A note on the company with the evidence link (tender URL, source)
- Never overwrite a hotter priority with a colder one in the same run; decay is its own explicit step

## Report format

"N signals pulled, M relevant, K matched to accounts: [account — signal — old→new priority]". Zero-match runs say so explicitly — silence is a result, not an error.
