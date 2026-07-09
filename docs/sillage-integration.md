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
- MCP is separate (login-based, no API key) — scripted access goes through the v2 API above.

Pipeline usage: `signal-watch` skill (corroboration model, priority rules).
