# Sillage Integration Plan

## What Sillage actually is (verified July 9, 2026)

Paris-based GTM startup, founded 2025, €1.7M pre-seed (April 2026, Kima Ventures, Angel Invest, Drysdale Ventures). An **AI signal engine**: define an ICP, activate "signal agents," receive prioritized buying signals with context and suggested next steps, routed to Slack/CRM. Claimed +50% reply rates vs. regular outbound. Crucially for us: **it streams signals to AI agents through an API** — explicitly designed for agentic workflows.

**Signal types:**
- *Social* (LinkedIn-heavy): job changes at target accounts, new executive hires, hiring waves, executive posts about strategic priorities, competitor engagement, market expansion announcements
- *Web*: funding rounds, M&A, leadership changes, press releases on expansion, tech/vendor migrations, product launches
- *First-party*: CRM-based signals (champion moves, renewal windows) — less relevant for our CRM-less users

**Coverage caveat:** Sillage's showcase customers are large enterprises (LVMH, Capgemini, BNP Paribas). Social/web signal density on 30-person industrial SMBs will be thin. Our integration design turns that constraint into an advantage (see below).

## The key insight: point Sillage at the BUYERS, not the user

Our user (Martine, 30-person racking manufacturer) has no digital footprint — but her **prospects' ecosystems do**. The company building a 12,000 m² warehouse is often a sizable logistics group; the general contractors and engineering firms in the account map are mid-size+ companies with real LinkedIn presence and press coverage. That's exactly the population Sillage covers well.

## Three integration points in the pipeline

### 1. Signal corroboration & ranking boost (Step 3-4)

Open data detects *that a project exists* (permit, ICPE filing, BODACC event). We then query Sillage on each detected account for corroborating signals:

- Expansion press releases or executive posts about the project → confidence boost + urgency boost
- Hiring waves at the account → project is accelerating
- Funding/M&A → capex confirmed

Claude's ranking step consumes both layers: `score = f(open data signal recency/type, Sillage signal density/type)`. Two independent signal sources agreeing = a hot account. This is also the judging story: "we cross official registries with Sillage's social/web signals — administrative proof + market buzz."

### 2. People-level timing signals (Step 4-5)

Sillage detects **job changes and new executive hires** at target accounts. For us this is gold: a new site director, operations director, or maintenance manager arriving at a mapped account is *the* moment to reach out — new leaders re-evaluate suppliers in their first 100 days (this is the primary growth lever for our Services & Maintenance ICP category). The detected person also becomes the priority contact to enrich via FullEnrich — Sillage tells us WHO and WHEN, FullEnrich gets us the reachable email/phone.

### 3. Continuous monitoring — from one-shot tool to living pipeline (post-pipeline)

After the initial scan, the agent registers the mapped accounts as a target list in Sillage. From then on, Sillage's signal agents watch them continuously; new signals stream back via API and trigger the agent to re-rank, re-enrich, and draft fresh outreach. Delivered to Martine as a simple email digest (no Slack, no CRM — she doesn't have them).

**Pitch line:** *"The agent doesn't find you a pipeline once — it keeps watching it. Official registries tell us a project exists; Sillage tells us the moment it heats up."*

## Outreach enrichment bonus

Sillage surfaces *executive posts about strategic priorities* with context. When available, Claude's outreach generator quotes the buyer's own stated priority in the email ("vous évoquiez l'automatisation de votre logistique...") — the deepest personalization tier in the demo.

## Demo integration

In the streamed agent steps, show a distinct "Sillage check" phase per top account with signal badges (e.g. 🔵 permit + 🟣 hiring wave + 🟣 new site director). One account in the demo dataset should have a strong Sillage signal so the corroboration story is visible on screen.

## Day-1 validation checklist

- [ ] Get API key, read API docs — confirm we can (a) submit accounts to monitor, (b) pull signals for a given company on demand
- [ ] Test signal density on 5 real French mid-size logistics/industrial companies (the *buyer* side)
- [ ] Test on 2 small SMBs to confirm the thin-coverage hypothesis (informs how we frame it)
- [ ] Fallback if API is watch-list-only (no on-demand query): pre-register the demo dataset accounts at the start of the hackathon so signals accumulate all day
