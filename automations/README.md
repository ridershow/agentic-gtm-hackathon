# Managed agents

Two autonomous agents keep the platform fed and trustworthy. Repo = source of truth; installed copies live in `~/Library/LaunchAgents`.

| Agent | Schedule | What it does |
|---|---|---|
| **Watcher** (`com.agenticgtm.watcher`) | daily 08:00 | Runs all Sillage agents, waits, pulls detections → HubSpot (`gtm_signal`, priority upgrade per corroboration rules, note per signal). `backend/ingest/sillage_watch.py` |
| **Cleaner** (`com.agenticgtm.cleaner`) | daily 08:15 | Archives garbage/duplicate companies, recomputes `gtm_contact_status`, flags missing provenance, reports 90-day decay candidates (never auto-applies decay). `backend/agents/cleaner.py` |

Install: `./automations/install.sh` (idempotent). Logs in `logs/`.
Run any agent on demand: `python3 -m backend.agents.cleaner` · `python3 -m backend.ingest.sillage_watch pull`.
