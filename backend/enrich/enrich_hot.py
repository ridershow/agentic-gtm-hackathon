"""Enrich hot/warm atlas accounts: FullEnrich people-search -> bulk email enrich
-> HubSpot contacts associated to their company.

Implements the enrich-accounts skill. Credit-aware: search 0.25/result (max 5
per account, curated to 3), work emails only (1 credit on hit). Phones are NOT
pulled here (10 credits — hot accounts only, on demand).

Usage:
    python -m backend.enrich.enrich_hot --priority hot         # search + enrich + push
    python -m backend.enrich.enrich_hot --priority hot --dry   # search only, no credits spent on enrich
"""

import argparse
import json
import os
import sys
import time

import httpx
from dotenv import load_dotenv

from backend.enrich.fullenrich import call as fe_call, credits

load_dotenv()

HS = "https://api.hubapi.com"

# Finite-market buyer roles, best first — the owner decides in SMBs
SENIORITY = ["Owner", "Founder", "C-level", "VP", "Head", "Director"]
TITLE_KEYWORDS = ["directeur", "dirigeant", "gérant", "président", "achat", "purchasing",
                  "plant", "site", "usine", "industrial", "technique", "maintenance",
                  "general manager", "ceo", "managing director"]


def hs_headers():
    return {"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
            "Content-Type": "application/json"}


def hot_companies(client, priority):
    r = client.post(f"{HS}/crm/v3/objects/companies/search", headers=hs_headers(), json={
        "filterGroups": [{"filters": [
            {"propertyName": "gtm_priority", "operator": "EQ", "value": priority},
            {"propertyName": "domain", "operator": "HAS_PROPERTY"},
        ]}],
        "properties": ["name", "domain", "city"], "limit": 100})
    r.raise_for_status()
    return r.json()["results"]


def search_people(domain):
    # No server-side seniority filter (enum values are finicky) — pull 10, curate locally.
    res = fe_call("POST", "/people/search", {
        "limit": 10,
        "current_company_domains": [{"value": domain, "exact_match": True}],
    })
    return res.get("people") or []


def title_of(person):
    return ((person.get("employment") or {}).get("current") or {}).get("title") or ""


def seniority_of(person):
    return ((person.get("employment") or {}).get("current") or {}).get("seniority") or ""


def score(person):
    title = title_of(person).lower()
    s = max((len(k) for k in TITLE_KEYWORDS if k in title), default=0)
    if seniority_of(person) in ("Owner", "Founder", "C-Level", "VP", "Head", "Director"):
        s += 10
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--priority", default="hot")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    print("credits before:", credits()["balance"])
    with httpx.Client(timeout=30) as client:
        targets = hot_companies(client, args.priority)
        print(f"{len(targets)} {args.priority} companies with domain")
        to_enrich, meta = [], []
        for c in targets:
            p = c["properties"]
            people = search_people(p["domain"])
            people = sorted(people, key=score, reverse=True)[:3]
            print(f"  {p['name']}: {len(people)} decision-makers found")
            for person in people:
                first = person.get("first_name"); last = person.get("last_name")
                if not (first and last):
                    continue
                entry = {"first_name": first, "last_name": last,
                         "domain": p["domain"], "company_name": p["name"],
                         "enrich_fields": ["contact.work_emails"]}
                url = person.get("professional_network_url") or person.get("linkedin_url")
                if url:
                    entry["linkedin_url"] = url
                to_enrich.append(entry)
                meta.append({"company_id": c["id"], "company": p["name"],
                             "title": title_of(person)})
        if args.dry:
            print(json.dumps(to_enrich, indent=1, ensure_ascii=False))
            return
        if not to_enrich:
            sys.exit("nothing to enrich")
        out = fe_call("POST", "/contact/enrich/bulk",
                      {"name": f"atlas {args.priority} decision-makers", "data": to_enrich})
        eid = out["enrichment_id"]
        print("enrichment", eid)
        for _ in range(30):
            time.sleep(10)
            res = fe_call("GET", f"/contact/enrich/bulk/{eid}")
            if res.get("status") == "FINISHED":
                break
            print("  ...", res.get("status"))
        pushed = 0
        for i, row in enumerate(res.get("data", [])):
            info = row.get("contact_info") or {}
            best = (info.get("most_probable_work_email") or {})
            email, status = best.get("email"), best.get("status")
            if not email or status not in ("DELIVERABLE", "HIGH_PROBABILITY"):
                continue
            m = meta[i]
            inp = row.get("input", {})
            props = {"email": email, "firstname": inp.get("first_name"),
                     "lastname": inp.get("last_name"), "jobtitle": m.get("title") or "",
                     "company": m["company"]}
            r = client.post(f"{HS}/crm/v3/objects/contacts", headers=hs_headers(),
                            json={"properties": props})
            if r.status_code == 409:  # exists — find and update
                cid = r.json().get("message", "").split("ID: ")[-1]
                client.patch(f"{HS}/crm/v3/objects/contacts/{cid}", headers=hs_headers(),
                             json={"properties": props})
            else:
                r.raise_for_status()
                cid = r.json()["id"]
            client.put(f"{HS}/crm/v4/objects/companies/{m['company_id']}/associations/default/contacts/{cid}",
                       headers=hs_headers())
            pushed += 1
            print(f"  + {props['firstname']} {props['lastname']} <{email}> [{status}] -> {m['company']}")
        print(f"\npushed {pushed} contacts | credits after: {credits()['balance']}")


if __name__ == "__main__":
    main()
