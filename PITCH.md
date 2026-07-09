# Agentic GTM Hackathon — Problem, Approach, Business Impact

## Problem

Europe runs on industrial SMBs — manufacturers and service providers selling physical products to factories and warehouses: racking, industrial doors, conveyors, packaging lines, cooling, maintenance. Most were founded 20-40 years ago and are still run by their founders. They are profitable, respected in their niche… and invisible online.

Their market is **capped**: the number of factories and warehouses in Europe is finite and known. You can't grow the pie. Growth comes from exactly one thing — **being there at the rare moment a buyer has a live project**: a new site, an extension, a production line upgrade, a relocation. Miss that window, and the deal goes to the incumbent supplier for the next 10-15 years.

Today these companies find that window by accident. They prospect the way they did in 1995: trade shows, professional associations, word of mouth, waiting for the phone to ring. No CRM, no LinkedIn, no marketing team, no intent data. Meanwhile, the signals that reveal a live industrial project — building permits, environmental permit filings, company registry events, hiring surges — are **published in open data, in plain sight, and almost nobody in GTM exploits them**.

The result: millions of European industrial SMBs systematically miss the buying moments happening in their own region, in their own market.

## High-Level Approach

An AI agent that turns open data into a pipeline — with zero digital skills required from the user.

**Input:** one sentence in plain French. *"Je vends des rayonnages industriels, 30 salariés, basé à Lyon."*

**Output:** a ranked list of live industrial projects in the region, the map of stakeholders around each project, enriched decision-maker contacts, and a ready-to-send outreach email referencing the specific project.

The agent works signal-first — it doesn't search for companies hoping they need the product; it detects **proof that a project is happening**, then maps everyone involved:

1. **Profile extraction** (Claude) — parse the one-sentence description into a product category, buyer profile, and region
2. **Signal detection** (French open data) — scan for live buying signals:
   - Building permits for industrial/warehouse buildings (SITADEL)
   - **Environmental permit filings (ICPE)** — every factory expansion legally requires one, publicly published, unexploited by GTM tooling
   - New establishment openings, capital increases (BODACC / Sirene)
   - Production and warehouse hiring surges (France Travail)
   - Digital intent signals (Sillage)
3. **Account mapping** (Claude reasoning) — for each project, identify the ecosystem: site owner/operator, general contractor, engineering firm — and rank who to contact first, with reasoning
4. **Contact enrichment** (FullEnrich) — decision-maker names, emails, phone numbers
5. **Outreach generation** (Claude) — a short, plain-French email per contact that references the specific project ("votre permis pour l'extension de 12 000 m² à Saint-Nazaire…")

Built France-first on French open data — and expandable by design: every EU country maintains equivalent registries (company registers, building permits, environmental permits).

## Business Impact

**Increase revenue from open-data intent signals and new relationships — replacing the traditional marketing tactics (trade shows, associations, word of mouth) that founder-led industrial SMBs rely on today.**

Concretely:

- **Catch revenue that is currently lost by default.** In a capped market every missed buying window is a deal locked up by a competitor for 10-15 years. Detecting projects at permit stage puts the SMB in the conversation 6-18 months before equipment decisions are finalized — before competitors even know the project exists.
- **Compress prospecting from hours to seconds.** What a (nonexistent) marketing team would spend 2 hours researching per account — finding the project, identifying stakeholders, hunting emails — the agent does in 90 seconds, at the cost of an API call.
- **Replace tactic spend with signal precision.** A trade show costs €5-15k per event for a handful of unqualified conversations. The agent surfaces prospects with a *proven, dated, documented* buying signal — a fundamentally warmer conversation at near-zero marginal cost.
- **A massive, underserved market.** ~4 million French SMBs, ~25 million across the EU — the overwhelming majority spend €0 on digital prospecting today, not because they don't need pipeline, but because every existing tool assumes a digitally-native user. Zero setup, one sentence in, pipeline out.
