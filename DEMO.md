# Demo script — 2 minutes

Everything shown is real data in the live HubSpot portal. Nothing mocked; pre-computed steps are announced as pre-computed.

## 0:00–0:15 — The problem (1 slide / spoken)

"Industrial SMBs sell in finite markets. Our demo case: a supplier to aluminium-extrusion plants. His entire addressable market in France is **23 factories**. Miss a buying window, lose the account for 15 years. And these buyers are invisible: we watched them on LinkedIn for 180 days — zero posts."

## 0:15–0:40 — Goal 1: Territory Coverage

Claude Code, `/goal` with one sentence: *"Je vends des équipements et services aux usines d'extrusion aluminium, 25 salariés."*
Engine confirms the reading, announces: **"Atlas pre-computed this morning: 23 accounts = 100% of the French market, evidence per line."** Show HubSpot/UI: 23 companies, hot/warm/watch.

## 0:40–1:10 — Goal 2: Company Enrichment (the waterfall)

Show contacts with **provenance** in the UI:
- FullEnrich people-search: 15 verified emails
- Registry fallback: +15 (in an SMB the gérant IS the buyer — legally registered, open data)
- **Sillage: found the plant director at the account both others missed** (Extol) — then FullEnrich resolved his colleagues' emails at Hydro/Technal
- 3 accounts flagged `manual_search`: the engine says exactly where the human takes over

## 1:10–1:40 — Goal 3: Signal Watcher + the interface

Real capex signals on the hot accounts (€50M foundry, plant doubling, new press). Swipe UI: card = account + signal + evidence + contact. Swipe right = hot. "The owner does this with his coffee. The watcher re-runs on schedule — managed agents keep feeding and cleaning the base."

## 1:40–2:00 — Close

"No AI outreach — deliberate: industrial deals are human. The engine's job is that you **never miss the window again**. One caught window in a finite market = a 10-15 year customer. Built today: Claude engine + FullEnrich + Sillage + open data, versioned skills, live CRM."

## Fallbacks

- HubSpot connector slow in UI → `src/data/accounts.json` (same shape)
- Claude Code offline → screen recording (YouTube link in README)
- Q&A ammo: why no outreach (product choice) · Sillage 0 LinkedIn signals = the thesis, but it found the Extol lead · eval: atlas graded vs a hand-built ground truth
