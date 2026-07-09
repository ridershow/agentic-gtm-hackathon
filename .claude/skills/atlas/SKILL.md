---
name: atlas
description: Map 100% of a finite B2B market — every company that could buy the user's product — with evidence per line and an honest coverage claim. Use when onboarding a new user profile, when asked to "map the market", "build the account list", "find all the X in France", or as step 1 of /goal. Output = organizations table + HubSpot companies with siren, ready for enrichment and signal watching.
---

# Atlas — finite-market mapping

In a finite market the account list IS the TAM. The goal is not "find some leads", it is **enumerate the entire universe and prove the enumeration is complete**. Every line carries evidence; the final claim is auditable.

## Inputs

From profile extraction (/goal step 0): product category, buyer profile (what the buyer operates: factory type, warehouse, plant), region.

## Method — anchor + discovery nets

1. **Anchor: NAF code sweep.** Identify the 1-3 NAF codes where buyers legally live. Pull every company via the free SIRENE API (`https://recherche-entreprises.api.gouv.fr/search?activite_principale=<naf>&departement=<dd>`, no auth). This is the anchor list — high recall, noisy precision.
2. **Discovery nets — sources OUTSIDE the registry** (catch NAF mismatches, ~10-15% of real players):
   - **Federation/association member rosters** (e.g. trade group directories) — membership tags often encode capability
   - **Certification registries** (quality labels, sector certifications) — certified = operating
   - **Web sentinels**: search brand names known to be in the market; every sentinel MUST be found by at least one source family, or recall is broken
3. **Classify every candidate, 4 states** (never delete, reclassify):
   - `verified_in` — evidence the company operates the capability, with quote + URL
   - `candidate` — plausible, capability not proven
   - `unresolved` — in anchor NAF, no web presence to verify (one-by-one search pass before giving up)
   - `excluded` — negative proof (trader, wrong activity, holding). Keep the reason.
4. **Group resolution.** Brands ≠ legal entities ≠ plants. Resolve each brand to its legal entity (SIREN) and parent group; multi-plant groups get one line per production site.
5. **Saturation matrix = the stop rule.** Track source families × new names found. Stop when every remaining family returns only already-known names. That's the completeness proof for the pitch: "N source families, saturated".

## Output

- `organizations` rows (`backend/db.py`): siren, name, kind=company, raw = full evidence
- HubSpot companies (pattern: `backend/ingest/seed_atlas.py`): `siren`, domain, city, `gtm_priority` (default `watch`), description = type + group
- Coverage block: anchor size → verified_in count, sentinel recall X/Y, known limits stated honestly

## Rules

- No line without an evidence URL. A claim without a source gets state `candidate`, never `verified_in`.
- Report coverage honestly ("~90% confidence, N unresolved") — an auditable 90% beats a fake 100%.
- Demo shortcut: if HubSpot already has seeded atlas companies (`siren HAS_PROPERTY`), skip mapping and report the existing base.
