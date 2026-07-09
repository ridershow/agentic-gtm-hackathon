"""Account mapping — decision-makers for the HubSpot atlas via FullEnrich.

For each atlas company in HubSpot (siren HAS_PROPERTY): find the likely buyers
with FullEnrich people/search (ranked: CEO/gérant > plant/site director >
purchasing > technical/maintenance), bulk-enrich work emails (phones only on
hot accounts), then upsert contacts into HubSpot associated to their company.

Credit rules (docs/fullenrich.md): search 0.25/result, work email 1, phone 10.
Only accounts still below the per-account contact target are processed;
re-runs are safe (HubSpot upserts by email, FullEnrich re-enrich free < 3 months).

Usage:
    python -m backend.enrich.map_accounts --check         # coverage per atlas account
    python -m backend.enrich.map_accounts --dry-run       # plan only, 0 credits
    python -m backend.enrich.map_accounts --limit 1       # map the first account (hot first)
    python -m backend.enrich.map_accounts                 # map every account below target
    python -m backend.enrich.map_accounts --no-phones     # emails only, even on hot
"""

import argparse
import sys
import time
import unicodedata

import httpx
from dotenv import load_dotenv

from backend.enrich import fullenrich

load_dotenv()

HS_BASE = "https://api.hubapi.com"
TARGET_PER_ACCOUNT = 3   # curation beats volume (enrich-accounts skill)
SEARCH_LIMIT = 25        # people/search cap per account (<= 6.25 credits)

# Buyer roles for a finite-market industrial SMB, best first.
ROLE_TIERS = [
    ("dirigeant", ["ceo", "gerant", "president", "directeur general", "directrice generale",
                   "general manager", "managing director", "chief executive", "founder", "fondateur"]),
    ("site", ["directeur d'usine", "directeur usine", "directrice usine", "plant manager",
              "plant director", "site manager", "directeur de site", "directeur industriel",
              "operations", "directeur des operations", "coo"]),
    ("achats", ["achat", "purchasing", "procurement", "sourcing"]),
    ("technique", ["directeur technique", "directrice technique", "technical director",
                   "maintenance", "travaux neufs", "engineering manager"]),
]


def _norm(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return text.lower()


def _hs_headers():
    import os

    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        sys.exit("HUBSPOT_TOKEN not set (.env)")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- HubSpot side ----------

def fetch_atlas_companies(client):
    r = client.post(f"{HS_BASE}/crm/v3/objects/companies/search", headers=_hs_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": "siren", "operator": "HAS_PROPERTY"}]}],
        "properties": ["name", "domain", "city", "gtm_priority", "siren"],
        "limit": 100,
    })
    r.raise_for_status()
    companies = [{"id": row["id"], **row["properties"]} for row in r.json()["results"]]
    order = {"hot": 0, "warm": 1, "watch": 2}
    companies.sort(key=lambda c: order.get(c.get("gtm_priority"), 3))
    return companies


def contact_count(client, company_id):
    r = client.get(f"{HS_BASE}/crm/v4/objects/companies/{company_id}/associations/contacts",
                   headers=_hs_headers(), params={"limit": 100})
    r.raise_for_status()
    return len(r.json().get("results", []))


def upsert_contact(client, company_id, contact):
    props = {k: v for k, v in contact.items() if k in
             ("email", "firstname", "lastname", "jobtitle", "phone") and v}
    r = client.post(f"{HS_BASE}/crm/v3/objects/contacts/search", headers=_hs_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ",
                                       "value": contact["email"]}]}],
        "properties": ["email"], "limit": 1,
    })
    r.raise_for_status()
    found = r.json()["results"]
    if found:
        contact_id = found[0]["id"]
        r = client.patch(f"{HS_BASE}/crm/v3/objects/contacts/{contact_id}",
                         headers=_hs_headers(), json={"properties": props})
    else:
        r = client.post(f"{HS_BASE}/crm/v3/objects/contacts",
                        headers=_hs_headers(), json={"properties": props})
    r.raise_for_status()
    contact_id = r.json()["id"]
    r = client.put(
        f"{HS_BASE}/crm/v4/objects/companies/{company_id}/associations/default/contacts/{contact_id}",
        headers=_hs_headers(),
    )
    r.raise_for_status()
    return contact_id, bool(found)


# ---------- FullEnrich side ----------

def search_people(company):
    """people/search by company domain (else exact name), France. Returns raw person dicts."""
    body = {"limit": SEARCH_LIMIT, "person_locations": [{"value": "France"}]}
    if company.get("domain"):
        body["current_company_domains"] = [{"value": company["domain"]}]
    else:
        body["current_company_names"] = [{"value": company["name"], "exact_match": True}]
    try:
        payload = fullenrich.call("POST", "/people/search", body)
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 400:
            raise
        body.pop("person_locations")  # schema drift tolerance — retry without the location filter
        payload = fullenrich.call("POST", "/people/search", body)
    return payload.get("data") or payload.get("results") or []


def rank_candidates(people, company):
    """Order by buyer-role tier, then same-city bonus. Drop people with no usable title."""
    city = _norm(company.get("city"))
    ranked = []
    for p in people:
        current = (p.get("employment") or {}).get("current") or {}
        title = _norm(current.get("title"))
        if not title:
            continue
        tier = next((i for i, (_, kws) in enumerate(ROLE_TIERS)
                     if any(kw in title for kw in kws)), len(ROLE_TIERS))
        if tier == len(ROLE_TIERS):
            continue  # not a buyer role — don't spend credits on it
        p_city = _norm((p.get("location") or {}).get("city"))
        ranked.append((tier, 0 if city and city == p_city else 1, p))
    ranked.sort(key=lambda t: t[:2])
    return [p for _, _, p in ranked]


def to_enrich_input(person, company, with_phone):
    linkedin = (((person.get("social_profiles") or {}).get("professional_network")) or {}).get("url")
    current = (person.get("employment") or {}).get("current") or {}
    fields = ["contact.work_emails"] + (["contact.phones"] if with_phone else [])
    entry = {
        "first_name": person.get("first_name") or "",
        "last_name": person.get("last_name") or "",
        "company_name": company["name"],
        "enrich_fields": fields,
        "custom": {"company_id": company["id"], "jobtitle": current.get("title") or ""},
    }
    if company.get("domain"):
        entry["domain"] = company["domain"]
    if linkedin:
        entry["linkedin_url"] = linkedin
    return entry


def poll_enrichment(enrichment_id, timeout=300):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        payload = fullenrich.result(enrichment_id)
        status = payload.get("status")
        if status == "FINISHED":
            return payload
        if status in ("CANCELED", "CREDITS_INSUFFICIENT", "RATE_LIMIT"):
            sys.exit(f"Enrichment aborted: {status}")
        time.sleep(5)
    sys.exit(f"Enrichment {enrichment_id} still running after {timeout}s — "
             f"resume with: python -m backend.enrich.fullenrich result {enrichment_id}")


def usable_email(contact_info):
    """Best email we'd actually send to: DELIVERABLE > HIGH_PROBABILITY > CATCH_ALL (flagged)."""
    emails = (contact_info or {}).get("work_emails") or []
    by_status = {e.get("status"): e.get("email") for e in reversed(emails)}
    for status in ("DELIVERABLE", "HIGH_PROBABILITY", "CATCH_ALL"):
        if by_status.get(status):
            return by_status[status], status
    return None, None


# ---------- Orchestration ----------

def build_plan(client, companies, limit=None):
    """Accounts below the contact target, hot first."""
    plan = []
    for company in companies:
        have = contact_count(client, company["id"])
        need = TARGET_PER_ACCOUNT - have
        if need > 0:
            plan.append({"company": company, "have": have, "need": need})
    return plan[:limit] if limit else plan


def run(args):
    with httpx.Client(timeout=30) as client:
        companies = fetch_atlas_companies(client)
        print(f"{len(companies)} atlas companies in HubSpot")

        if args.check:
            for c in companies:
                n = contact_count(client, c["id"])
                flag = "✓" if n >= TARGET_PER_ACCOUNT else f"needs {TARGET_PER_ACCOUNT - n}"
                print(f"  {c.get('gtm_priority', '?'):5} {c['name']:40} {n} contacts ({flag})")
            return

        plan = build_plan(client, companies, limit=args.limit)
        print(f"{len(plan)} accounts below target ({TARGET_PER_ACCOUNT} contacts)")
        if args.dry_run:
            for entry in plan:
                c = entry["company"]
                print(f"  {c.get('gtm_priority', '?'):5} {c['name']:40} "
                      f"has {entry['have']}, search via "
                      f"{'domain ' + c['domain'] if c.get('domain') else 'name'}")
            return
        if not plan:
            print("Nothing to do — every account is at target.")
            return

        before = fullenrich.credits()
        print(f"Credits before: {before}")

        # 1. Search + rank per account
        to_enrich, needs_manual = [], []
        for entry in plan:
            company, need = entry["company"], entry["need"]
            people = search_people(company)
            picked = rank_candidates(people, company)[:need]
            hot = company.get("gtm_priority") == "hot"
            for person in picked:
                to_enrich.append(to_enrich_input(person, company, with_phone=hot and not args.no_phones))
            print(f"  {company['name']}: {len(people)} found, {len(picked)} picked"
                  + (" (+phones)" if picked and hot and not args.no_phones else ""))
            if not picked:
                needs_manual.append(company["name"])

        if not to_enrich:
            print("No candidates found for any account — nothing to enrich.")
            return

        # 2. One bulk enrichment for everyone (<=100)
        enrichment = fullenrich.enrich(to_enrich, name="atlas account mapping")
        enrichment_id = enrichment.get("enrichment_id") or enrichment.get("id")
        print(f"Enriching {len(to_enrich)} contacts (id {enrichment_id})...")
        outcome = poll_enrichment(enrichment_id)

        # 3. Write back to HubSpot
        by_id = {c["id"]: c for c in companies}
        synced = no_email = 0
        for record in outcome.get("data", []):
            custom = record.get("custom") or {}
            company = by_id.get(custom.get("company_id"))
            if not company:
                continue
            email, status = usable_email(record.get("contact_info"))
            inp = record.get("input") or {}
            if not email:
                no_email += 1
                needs_manual.append(f"{company['name']} — {inp.get('full_name') or inp.get('first_name', '')} (no email)")
                continue
            phone = ((record.get("contact_info") or {}).get("most_probable_phone") or {}).get("number")
            _, existed = upsert_contact(client, company["id"], {
                "email": email,
                "firstname": inp.get("first_name"),
                "lastname": inp.get("last_name"),
                "jobtitle": custom.get("jobtitle"),
                "phone": phone,
            })
            synced += 1
            risky = " ⚠ catch-all" if status == "CATCH_ALL" else ""
            print(f"{'~' if existed else '+'} {company['name']}: {email} "
                  f"({custom.get('jobtitle') or 'n/a'}){' 📞' if phone else ''}{risky}")

        after = fullenrich.credits()
        print(f"\ndone: {synced} contacts synced to HubSpot, {no_email} without usable email")
        print(f"Credits after: {after} (before: {before})")
        if needs_manual:
            print("needs-manual:\n  " + "\n  ".join(needs_manual))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="coverage report, no enrichment")
    ap.add_argument("--dry-run", action="store_true", help="plan only, no FullEnrich calls")
    ap.add_argument("--limit", type=int, help="process at most N accounts (hot first)")
    ap.add_argument("--no-phones", action="store_true", help="skip phones even on hot accounts")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
