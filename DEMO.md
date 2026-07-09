# Demo script — round 1 format: 1:30 pitch · 1:30 demo · 2:00 Q&A

Everything shown is real data in the live HubSpot portal. Pre-computed steps are announced as pre-computed, never faked.

## PITCH (1:30) — deck

**Problem (0:00-0:25).** "Industrial SMBs sell in finite markets. Our real demo case: a supplier to aluminium-extrusion plants — his entire addressable market in France is 23 factories. Miss a buying window, lose the account for 15 years. And these buyers are invisible: we watched them on LinkedIn for 180 days. Zero posts. Every intent tool on the market is blind here."

**Goal 1 — Territory Coverage (0:25-0:45).** One sentence in, the engine maps 100% of the market: registry sweep + discovery nets + saturation proof. 23 accounts, evidence per line, live in HubSpot.

**Goal 2 — Company Enrichment (0:45-1:05).** Provenance-tagged waterfall: FullEnrich found 15 verified emails → the registry added 15 (in an SMB the gérant IS the buyer) → Sillage found the plant director both others missed. 3 accounts flagged for human search — never silently dropped.

**Goal 3 — Signal Watcher (1:05-1:30).** Open data + Sillage + Claude scoring each signal against the ICP. Corroboration model: administrative proof + market buzz agreeing = hot. Real capex signals on our hot accounts: a €50M foundry, a plant doubling, a new press. Managed agents (watcher + cleaner) keep the base fed and trustworthy on schedule.

## DEMO (1:30) — Lovable, live

- **0:00-0:10** — Open the app: all leads on screen, live from HubSpot. "23 accounts = the whole French market. hot / warm / watch."
- **0:10-0:15** — Open a hot account (Sépalumic: €30M extension + hybrid press). **Click "Generate brief" now** — "40 seconds, ready by the end of the demo."
- **0:15-0:50** — The monitor at work: swipe cards — account + signal + evidence link + contact with provenance badge. Tell Extol in one line: "FullEnrich empty, registry empty — Sillage found the plant director. Each source catches what the others miss."
- **0:50-1:10** — Map view: the whole territory, colored by priority. "A 2-person sales team now watches all of it, continuously."
- **1:10-1:30** — **The brochure is ready**: Gamma doc, on the supplier's brand — the lead's project on page 1, the decision-makers, the product range mapped to their line. "The AI doesn't do the outreach. When the human gets the meeting, the engine arms him." Close: "You'll never miss the window again."

## Q&A ammo (2:00)

- **Why no outreach?** Product choice: big-ticket industrial deals are human and custom. The engine maximizes what AI does best (coverage, memory, timing) and leaves relationships to people. It's also why reps trust it.
- **Sillage found nothing?** On LinkedIn-silent verticals, zero *posts* is the expected result — and the thesis. But Sillage's account mapping found persona-fit plant directors that enrichment and registry missed. We use every layer for what it's good at.
- **Eval?** The atlas is graded against a hand-built ground truth of the same market (real client work): coverage, sentinel recall, saturation matrix.
- **Scalable?** Every EU country keeps equivalent registries. The skills are versioned; the vertical is a parameter.

## Fallbacks

- HubSpot connector slow in UI → `src/data/accounts.json` (same shape)
- Gamma slow/offline on stage → pre-generated brochure tab: [removed]
- Claude Code offline → screen recording (YouTube link in README)
