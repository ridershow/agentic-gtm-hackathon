"""Managed agent: Cleaner — keeps the HubSpot base trustworthy.

Runs daily (launchd, see automations/). Fixes what's safe, reports the rest:
- archives garbage companies (empty/None names)
- archives HubSpot auto-created domain-duplicates of atlas companies
- recomputes gtm_contact_status (covered / manual_search) for every atlas company
- flags contacts missing gtm_provenance
- 90-day priority decay is reported (never auto-applied — explicit human step)

Usage: python -m backend.agents.cleaner [--dry]
"""

import os
import sys
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

HS = "https://api.hubapi.com"


def hs_headers():
    return {"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
            "Content-Type": "application/json"}


def search(client, obj, filters, props, limit=100):
    r = client.post(f"{HS}/crm/v3/objects/{obj}/search", headers=hs_headers(), json={
        "filterGroups": [{"filters": filters}], "properties": props, "limit": limit})
    r.raise_for_status()
    return r.json()["results"]


def main():
    dry = "--dry" in sys.argv
    report = []
    with httpx.Client(timeout=30) as client:
        atlas = search(client, "companies",
                       [{"propertyName": "siren", "operator": "HAS_PROPERTY"}],
                       ["name", "domain", "gtm_priority", "gtm_signal_date", "gtm_contact_status"])
        atlas_domains = {c["properties"].get("domain") for c in atlas if c["properties"].get("domain")}
        everyone = search(client, "companies", [{"propertyName": "createdate", "operator": "HAS_PROPERTY"}],
                          ["name", "domain", "siren"], limit=200)
        # 1. garbage + auto-created dupes
        for c in everyone:
            p = c["properties"]
            name = (p.get("name") or "").strip()
            is_garbage = name in ("", "None", "null")
            is_dupe = (not p.get("siren")) and p.get("domain") and any(
                p["domain"] != d and (p["domain"].split(".")[0] in d or d.split(".")[0] in p["domain"])
                for d in atlas_domains)
            if is_garbage or is_dupe:
                report.append(f"archive company '{name or p.get('domain')}' ({'garbage' if is_garbage else 'domain-dupe of atlas account'})")
                if not dry:
                    client.delete(f"{HS}/crm/v3/objects/companies/{c['id']}", headers=hs_headers())
        # 2. contact status recompute
        for c in atlas:
            r = client.get(f"{HS}/crm/v4/objects/companies/{c['id']}/associations/contacts",
                           headers=hs_headers())
            status = "covered" if r.json().get("results") else "manual_search"
            if c["properties"].get("gtm_contact_status") != status:
                report.append(f"status {c['properties']['name']}: -> {status}")
                if not dry:
                    client.patch(f"{HS}/crm/v3/objects/companies/{c['id']}", headers=hs_headers(),
                                 json={"properties": {"gtm_contact_status": status}})
        # 3. provenance check
        orphans = search(client, "contacts",
                         [{"propertyName": "gtm_provenance", "operator": "NOT_HAS_PROPERTY"}],
                         ["firstname", "lastname"])
        for o in orphans:
            report.append(f"contact missing provenance: {o['properties'].get('firstname')} {o['properties'].get('lastname')}")
        # 4. decay report (never auto-applied)
        now = datetime.now(timezone.utc)
        for c in atlas:
            p = c["properties"]
            if p.get("gtm_priority") in ("hot", "warm") and p.get("gtm_signal_date"):
                age = (now - datetime.fromisoformat(p["gtm_signal_date"].replace("Z", "+00:00"))).days
                if age > 90:
                    report.append(f"decay candidate: {p['name']} ({p['gtm_priority']}, signal {age}d old)")
    print(f"cleaner {'DRY ' if dry else ''}run {now.isoformat()}: {len(report)} findings")
    for line in report:
        print(" -", line)


if __name__ == "__main__":
    main()
