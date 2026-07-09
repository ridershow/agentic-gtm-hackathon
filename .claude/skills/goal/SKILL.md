---
name: goal
description: The full GTM engine, end to end — from a one-sentence business description to a live, monitored pipeline in HubSpot. Use when onboarding a new user ("je vends des rayonnages industriels, 30 salariés, Lyon"), when asked to "run the engine", "set up my GTM", or for the demo. Orchestrates the three goals: territory-coverage → company-enrichment → signal-watcher.
---

# /goal — the engine, end to end

Input: **one sentence in plain language.** Output: a mapped market, enriched contacts and live signal watching. Zero digital skills required from the user.

## Step 0 — Profile extraction

Parse the sentence → product category, buyer profile (what the buyer operates), region, company size. Confirm the reading back in one line ("Vous vendez X à des Y, région Z — c'est bien ça ?"). Everything downstream keys off this.

## Goal 1 — Territory Coverage (skill: `territory-coverage`)

Map 100% of the finite market with evidence. → HubSpot companies with `siren`, default priority `watch`.

**Demo shortcut**: if HubSpot already holds atlas companies (`siren HAS_PROPERTY` > 0), announce "atlas pre-computed this morning: N accounts" and continue. The long step is skippable, never fake.

## Goal 2 — Company Enrichment (skill: `company-enrichment`)

Top 3 decision-makers per account via FullEnrich → HubSpot contacts. Emails everywhere, phones on hot only.

## Goal 3 — Signal Watcher (skill: `signal-watcher`)

BOAMP + open data + Sillage → scored, matched, written to `gtm_signal`/`gtm_priority`. Register the hot+warm tier as the Sillage watchlist. In production this step re-runs on schedule (managed agent); on demand it runs once and reports.

## Final briefing (what the user actually sees)

5 lines max, owner language:
"Votre marché : N acteurs, cartographié. M contacts identifiés. Cette semaine, K comptes ont bougé : [account — pourquoi c'est le moment, qui contacter]."

## Hard rules

- Every number in the briefing must be queryable in HubSpot (no invented counts).
- If a step fails, say which and continue with what exists — a partial pipeline that's honest beats a full one that lies.
