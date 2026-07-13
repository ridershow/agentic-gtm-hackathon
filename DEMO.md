# Demo script — round 1 format: 1:30 pitch · 1:30 demo · 2:00 Q&A

Everything shown is real data in the live HubSpot portal. Pre-computed steps are announced as pre-computed, never faked.

## PITCH (1:30) — 7 slides. Format: problem → approach + scheme → expected business impact.

~225 words ≈ 88s at pitch pace. No ad-libs — every added sentence eats the impact slide.

**S1 · Title (0:00-0:08).** "Industrial SMBs also need GTM. We built the engine that gives it to them."

**S2 · Not sexy (0:08-0:18).** "Industrial SMBs are not sexy. Founded decades ago, founder-led, profitable, respected in their niche."

**S3 · Not online (0:18-0:33).** "And they barely live on the internet: 58% of EU SMEs reach basic digital intensity, versus 91% of large firms. We watched one industrial vertical on LinkedIn for 180 days — zero posts. Every GTM tool relies on LinkedIn. What about the rest?"

**S4 · Big chunk of the economy + iceberg (0:33-0:50).** "Yet: 2.2 million industrial companies in Europe, €2.5 trillion of value added, 30 million jobs — 99% of those companies are SMBs. And their market is finite: miss a buying window, lose the account for fifteen years. GTM tools don't cover this bottom of the iceberg. Here's how we do."

**S5 · Who we build for (0:50-1:05).** "A founder who knows his market by heart. Shirt, not hoodie. Happy with the status quo — but he knows AI can help. So the engine stays invisible: a custom interface surfaces only what's needed. And deliberately, no AI outreach — his deals are human, his relationships stay his."

**S6 · The scheme (1:05-1:20).** "One sentence in, Claude chains three goals: map 100% of the finite market; enrich every account — FullEnrich, then the registry, then Sillage, each catches what the others miss; then watch everything — tenders, permits, registry events, Claude scores each signal: proof plus buzz equals hot. All in HubSpot, on schedule."

**S7 · Expected business impact (1:20-1:30).** "A trade show costs €5-15K for a handful of unqualified conversations. The engine surfaces dated, documented buying signals at near-zero marginal cost — on 100% of the territory, in auto mode. New revenue, on top of the tactics that already work."

## DEMO (1:30) — Lovable, live

- **0:00-0:10** — Open the app: all leads on screen, live from HubSpot. "23 accounts = the whole French market. hot / warm / watch."
- **0:10-0:15** — Open a hot account (Sépalumic: €30M extension + hybrid press). **Click "Generate brief" now** — "40 seconds, ready by the end of the demo."
- **0:15-0:50** — The monitor at work: swipe cards — account + signal + evidence link + contact with provenance badge. Tell Extol in one line: "FullEnrich empty, registry empty — Sillage found the plant director. Each source catches what the others miss."
- **0:50-1:10** — Map view: the whole territory, colored by priority. "A 2-person sales team now watches all of it, continuously."
- **1:10-1:30** — **The brochure is ready**: Gamma doc, on the supplier's brand — the lead's project on page 1, the decision-makers, the product range mapped to their line. "The AI doesn't do the outreach. When the human gets the meeting, the engine arms him." Close: "You'll never miss the window again."

## Q&A ammo (2:00)

Answer in ≤3 sentences, then stop — let them ask the next one. Q&A is where AI depth and external-data depth get scored; steer there if given the chance.

- **Where's the AI, really?** (= AI depth, 25 pts) Claude is three things here: the **orchestrator** — the whole engine is versioned skills chained by `/goal` from one plain-language sentence; the **scorer** — every raw signal (tender, permit, registry event) is judged against the ICP semantically, not by keywords; and the **janitor** — managed agents (watcher + cleaner) run on schedule to keep the CRM fed and trustworthy. No AI-generated content ships to a prospect — by design.
- **Why no outreach?** Product choice: big-ticket industrial deals are human and custom. The engine maximizes what AI does best (coverage, memory, timing) and leaves relationships to people. It's also why reps trust it.
- **Sillage found nothing?** On LinkedIn-silent verticals, zero *posts* is the expected result — and the thesis. But Sillage's account mapping found the Extol plant director that both FullEnrich and the registry missed. We use every layer for what it's good at.
- **How do you know the atlas is complete?** Saturation proof: independent discovery nets (registry codes, trade directories, competitor customer lists) must stop yielding new names. Graded against a hand-built ground truth of this exact market: coverage, sentinel recall.
- **Business model?** Setup fee for the atlas (one-time, high perceived value — it's their whole market on a map), then monthly monitoring per territory. Recurring by nature: signals never stop.
- **Scalable beyond France?** France-first because it has the best open data in Europe, but every EU country keeps equivalent registries. The vertical and the country are parameters of the skills.
- **Why HubSpot?** The engine writes into the CRM the sales team already lives in — no new tool to adopt. HubSpot is the source of truth; the swipe interface is just a lens on it.

## Fallbacks

- HubSpot connector slow in UI → `src/data/accounts.json` (same shape)
- Gamma slow/offline on stage → keep a pre-generated brochure open in a tab
- Claude Code offline → screen recording (YouTube link in README)
