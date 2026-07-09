"""Seed HubSpot with the demo atlas — French aluminium-extrusion plants.

Dataset: backend/ingest/atlas_seed.json — 23 companies, public sources only
(SIRENE registry, company websites, trade press). This is the pre-computed
output of the Atlas step so signal ingestion (BOAMP, Sillage) has a real
account base to hit from minute one.

Usage:
    python -m backend.ingest.seed_atlas          # upsert all
    python -m backend.ingest.seed_atlas --check  # count what's in HubSpot
"""

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.hubapi.com"
SEED = Path(__file__).parent / "atlas_seed.json"


def _headers():
    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        sys.exit("HUBSPOT_TOKEN not set (.env)")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def find_by_siren(client, siren):
    r = client.post(f"{BASE}/crm/v3/objects/companies/search", headers=_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": "siren", "operator": "EQ", "value": siren}]}],
        "properties": ["name"], "limit": 1,
    })
    r.raise_for_status()
    results = r.json()["results"]
    return results[0]["id"] if results else None


def to_properties(c):
    props = {
        "name": c["name"],
        "siren": c["siren"],
        "city": c["city"],
        "country": "France",
        "industry": None,  # keep HubSpot enum untouched; type goes in description
        "description": f"{c['type']} — {c['legal_entity']}"
                       + (f" — group: {c['parent_group']}" if c.get("parent_group") else " — independent"),
        "gtm_priority": c["gtm_priority"],
    }
    if c.get("domain"):
        props["domain"] = c["domain"]
    if c.get("annual_revenue"):
        props["annualrevenue"] = str(c["annual_revenue"])
    if c.get("gtm_signal"):
        props["gtm_signal"] = c["gtm_signal"]
    return {k: v for k, v in props.items() if v is not None}


def main():
    companies = json.load(open(SEED))
    with httpx.Client(timeout=30) as client:
        if "--check" in sys.argv:
            r = client.post(f"{BASE}/crm/v3/objects/companies/search", headers=_headers(), json={
                "filterGroups": [{"filters": [{"propertyName": "siren", "operator": "HAS_PROPERTY"}]}],
                "limit": 100, "properties": ["name", "gtm_priority"],
            })
            r.raise_for_status()
            rows = r.json()["results"]
            print(f"{len(rows)} atlas companies in HubSpot")
            for row in rows:
                print(f"  {row['properties'].get('gtm_priority','?'):5} {row['properties']['name']}")
            return
        created = updated = 0
        for c in companies:
            props = to_properties(c)
            existing = find_by_siren(client, c["siren"])
            if existing:
                r = client.patch(f"{BASE}/crm/v3/objects/companies/{existing}",
                                 headers=_headers(), json={"properties": props})
                updated += 1
            else:
                r = client.post(f"{BASE}/crm/v3/objects/companies",
                                headers=_headers(), json={"properties": props})
                created += 1
            r.raise_for_status()
            print(f"{'~' if existing else '+'} {c['name']} [{c['gtm_priority']}]")
        print(f"\ndone: {created} created, {updated} updated")


if __name__ == "__main__":
    main()
