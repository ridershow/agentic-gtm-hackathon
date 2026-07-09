"""Sillage watch: pull signal detections -> feed HubSpot (gtm_signal + priority + note).

Workspace state (set up 09/07 ~17h, all via API):
  persona 469 · watchlist 13/18 accounts found · agents: 2693 capex FR (keyword),
  2694 four/energie FR (keyword), 2692 job postings usine, 2699 job updates.

All runs complete but return 0 signals on this vertical — the watched plants are
LinkedIn-silent (which is the product thesis; open data carries the signal load).
Pending with the Sillage team on site: content-requests 403 (workspace flag) and
whether hackathon workspaces gate detection persistence.

Usage:
    python -m backend.ingest.sillage_watch run       # launch all agents
    python -m backend.ingest.sillage_watch pull      # query signals -> HubSpot
"""

import json
import os
import sys
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

SIL = "https://api.getsillage.com/api"
HS = "https://api.hubapi.com"
AGENTS = [2693, 2694, 2692, 2699]


def sil_headers():
    return {"Authorization": f"Bearer {os.environ['SILLAGE_API_KEY']}",
            "Content-Type": "application/json"}


def hs_headers():
    return {"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
            "Content-Type": "application/json"}


def run_agents(client):
    for aid in AGENTS:
        r = client.post(f"{SIL}/v2/workspace/signal-runs", headers=sil_headers(),
                        json={"agent_id": aid})
        d = r.json()
        rid = d[0].get("signal_request_id") if isinstance(d, list) and d else None
        print(f"agent {aid} -> run {rid} ({r.status_code})")


def find_company(client, domain=None, name=None):
    filters = []
    if domain:
        filters = [{"propertyName": "domain", "operator": "EQ", "value": domain}]
    elif name:
        filters = [{"propertyName": "name", "operator": "CONTAINS_TOKEN", "value": name}]
    if not filters:
        return None
    r = client.post(f"{HS}/crm/v3/objects/companies/search", headers=hs_headers(),
                    json={"filterGroups": [{"filters": filters}],
                          "properties": ["name", "gtm_priority"], "limit": 1})
    results = r.json().get("results", [])
    return results[0] if results else None


def pull(client):
    r = client.post(f"{SIL}/v2/workspace/signals/query", headers=sil_headers(),
                    json={"page_size": 100})
    signals = r.json().get("data") or []
    print(f"{len(signals)} signal detections")
    for s in signals:
        comp = s.get("company") or {}
        target = find_company(client, comp.get("domain"), comp.get("name"))
        if not target:
            print(f"  ? unmatched: {comp.get('name')}")
            continue
        summary = s.get("summary") or s.get("title") or json.dumps(s)[:200]
        cur = target["properties"].get("gtm_priority") or "watch"
        # market buzz alone -> warm; never downgrade (decay is a separate explicit step)
        new = "warm" if cur == "watch" else cur
        client.patch(f"{HS}/crm/v3/objects/companies/{target['id']}", headers=hs_headers(),
                     json={"properties": {"gtm_signal": summary, "gtm_priority": new}})
        note = {"properties": {"hs_note_body": f"Sillage signal: {summary}",
                               "hs_timestamp": s.get("detected_at") or s.get("created_at")},
                "associations": [{"to": {"id": target["id"]},
                                  "types": [{"associationCategory": "HUBSPOT_DEFINED",
                                             "associationTypeId": 190}]}]}
        client.post(f"{HS}/crm/v3/objects/notes", headers=hs_headers(), json=note)
        print(f"  + {target['properties']['name']}: {summary[:80]} [{cur}->{new}]")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pull"
    with httpx.Client(timeout=120) as client:
        if cmd == "run":
            run_agents(client)
        else:
            pull(client)


if __name__ == "__main__":
    main()
