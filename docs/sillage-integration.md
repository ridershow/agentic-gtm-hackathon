# Sillage — wired

Key in `.env` (`SILLAGE_API_KEY`, `sk_live_` direct-client). Base `https://api.getsillage.com`, Bearer auth.
Docs: https://www.getsillage.com/docs/api (OpenAPI; every docs page has "Copy Markdown").

## Endpoints (v2)

- `GET /api/v2/top-account-list/accounts` — read watchlist (tested: 200)
- `POST /api/v2/top-account-list/accounts` — add accounts to watch
- `PUT /api/v2/persona` — set ICP persona
- `POST /api/v2/contents/query` — pull signals/content
- `POST /api/v2/enrich-company-mapping` · `GET /api/v2/company-mappings`

## Gotchas

- `GET /api/v2/content-requests` → 403 "not enabled for this workspace" — ask the Sillage team on site to enable it.
- Coverage is thin on silent industrial SMBs: watch the **buyer side** (atlas hot+warm tier), not the user. Watchlist cap: 20 accounts.
- 8 agent types (job updates, keyword, competitor, customer, partner, influencer, champion, job-posting keyword); playbooks readable via MCP `get_signal_playbook`.
- **MCP works with the API key directly** (`.mcp.json` at repo root, Bearer via ${SILLAGE_API_KEY} env). URL: `https://api.getsillage.com/api/mcp/v2`. 36 tools incl. `sillage_v2_get_setup_state` (diagnostic checklist) and `sillage_v2_get_signal_playbook`.

## Workspace state (live, set up 09/07 via API)

Persona 469 (FR industrial decision-makers) · watchlist: 13/18 domains found (not found = the web-invisible micro-sites) · agents: **2693** capex FR keywords · **2694** four/énergie FR keywords · **2692** job-posting keywords · **2699** job updates. Connector: `backend/ingest/sillage_watch.py` (run | pull -> HubSpot).

**All runs complete with 0 detections on this vertical** — the watched plants are LinkedIn-silent (= the product thesis; open data carries the signal load). MCP `get_setup_state` confirms everything green EXCEPT: contents feature 'not enabled for this workspace. Contact Sillage to enable it.' → ask the Sillage crew on site to flip the flag, then re-run `sillage_watch.py`.

Pipeline usage: `signal-watch` skill (corroboration model, priority rules).
