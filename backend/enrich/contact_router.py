"""Registry fallback loop: FullEnrich not found -> SIRENE dirigeants -> retry
FullEnrich with the gérant's name -> HubSpot contact with provenance.

Every contact carries gtm_provenance:
  people_search     — found + verified email via FullEnrich people search
  registry          — identity from the company registry, email resolved by FullEnrich
  registry_no_email — identity from the registry, email unresolved (human follow-up)

Usage:
    python -m backend.enrich.contact_router            # fill companies with 0 contacts
    python -m backend.enrich.contact_router --tag-only # just tag existing contacts people_search
"""

import os
import sys
import time

import httpx
from dotenv import load_dotenv

from backend.enrich.fullenrich import call as fe_call, credits

load_dotenv()

HS = "https://api.hubapi.com"
SIRENE = "https://recherche-entreprises.api.gouv.fr/search"
GOOD_ROLES = ("gérant", "président", "directeur général", "directeur")


def hs_headers():
    return {"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
            "Content-Type": "application/json"}


def atlas_companies(client):
    r = client.post(f"{HS}/crm/v3/objects/companies/search", headers=hs_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": "siren", "operator": "HAS_PROPERTY"}]}],
        "properties": ["name", "domain", "siren"], "limit": 100})
    r.raise_for_status()
    return r.json()["results"]


def contact_count(client, company_id):
    r = client.get(f"{HS}/crm/v4/objects/companies/{company_id}/associations/contacts",
                   headers=hs_headers())
    r.raise_for_status()
    return len(r.json().get("results", []))


def dirigeants(client, siren):
    r = client.get(SIRENE, params={"q": siren})
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return []
    people = [d for d in results[0].get("dirigeants", [])
              if d.get("type_dirigeant") == "personne physique" and d.get("nom")
              and "commissaire" not in (d.get("qualite") or "").lower()]  # auditors are not buyers
    people.sort(key=lambda d: min((i for i, role in enumerate(GOOD_ROLES)
                                   if role in (d.get("qualite") or "").lower()), default=9))
    return people[:2]


def push_contact(client, company_id, first, last, title, email, provenance):
    props = {"firstname": first, "lastname": last, "jobtitle": title or "",
             "gtm_provenance": provenance}
    if email:
        props["email"] = email
    r = client.post(f"{HS}/crm/v3/objects/contacts", headers=hs_headers(),
                    json={"properties": props})
    if r.status_code == 409:
        cid = r.json().get("message", "").split("ID: ")[-1]
        client.patch(f"{HS}/crm/v3/objects/contacts/{cid}", headers=hs_headers(),
                     json={"properties": props})
    else:
        r.raise_for_status()
        cid = r.json()["id"]
    client.put(f"{HS}/crm/v4/objects/companies/{company_id}/associations/default/contacts/{cid}",
               headers=hs_headers())
    return cid


def tag_existing(client):
    r = client.post(f"{HS}/crm/v3/objects/contacts/search", headers=hs_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": "gtm_provenance", "operator": "NOT_HAS_PROPERTY"}]}],
        "properties": ["firstname"], "limit": 100})
    r.raise_for_status()
    for row in r.json()["results"]:
        client.patch(f"{HS}/crm/v3/objects/contacts/{row['id']}", headers=hs_headers(),
                     json={"properties": {"gtm_provenance": "people_search"}})
    print(f"tagged {len(r.json()['results'])} existing contacts as people_search")


def main():
    with httpx.Client(timeout=30) as client:
        tag_existing(client)
        if "--tag-only" in sys.argv:
            return
        print("credits before:", credits()["balance"])
        empty = [c for c in atlas_companies(client) if contact_count(client, c["id"]) == 0]
        print(f"{len(empty)} companies with 0 contacts")
        # 1. registry identities
        plan = []
        for c in empty:
            p = c["properties"]
            people = dirigeants(client, p["siren"])
            print(f"  {p['name']}: {len(people)} registry dirigeant(s)"
                  + (f" — {people[0]['prenoms']} {people[0]['nom']} ({people[0].get('qualite')})" if people else ""))
            for d in people:
                first = (d.get("prenoms") or "").split()[0].title()
                plan.append({"company_id": c["id"], "company": p["name"],
                             "domain": p.get("domain"), "first": first,
                             "last": (d["nom"] or "").title(), "title": d.get("qualite") or "Dirigeant"})
        if not plan:
            sys.exit("registry returned nothing")
        # 2. retry FullEnrich with registry names (emails only)
        batch = [{"first_name": x["first"], "last_name": x["last"],
                  **({"domain": x["domain"]} if x["domain"] else {"company_name": x["company"]}),
                  "company_name": x["company"], "enrich_fields": ["contact.work_emails"]}
                 for x in plan]
        eid = fe_call("POST", "/contact/enrich/bulk",
                      {"name": "registry retry loop", "data": batch})["enrichment_id"]
        res = {}
        for _ in range(30):
            time.sleep(10)
            res = fe_call("GET", f"/contact/enrich/bulk/{eid}")
            if res.get("status") == "FINISHED":
                break
        # 3. push with provenance
        n_email = n_noemail = 0
        for i, row in enumerate(res.get("data", [])):
            x = plan[i]
            best = ((row.get("contact_info") or {}).get("most_probable_work_email") or {})
            email = best.get("email") if best.get("status") in ("DELIVERABLE", "HIGH_PROBABILITY") else None
            provenance = "registry" if email else "registry_no_email"
            push_contact(client, x["company_id"], x["first"], x["last"], x["title"], email, provenance)
            n_email += bool(email); n_noemail += (not email)
            print(f"  + {x['first']} {x['last']} ({x['title']}) -> {x['company']} [{provenance}]"
                  + (f" <{email}>" if email else ""))
        print(f"\nregistry loop: {n_email} with email, {n_noemail} identity-only | credits after: {credits()['balance']}")


if __name__ == "__main__":
    main()
