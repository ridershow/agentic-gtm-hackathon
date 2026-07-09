"""Sync GTM output from SQLite to HubSpot (system of record, portal 148865690).

Pushes organizations that have >= 1 ICP-relevant signal as companies, with the
gtm_* custom properties (signal summary, date, hot/warm/watch priority, outreach
draft). Upserts enriched contacts by email and associates them to their company.
Re-runnable: companies match by siren when present (atlas convention), else by
exact name; contacts match by email. Same values re-sync as no-op PATCHes.

Usage:
    python -m backend.sync.hubspot                  # sync everything relevant
    python -m backend.sync.hubspot --dry-run        # print plan, no API calls
    python -m backend.sync.hubspot --limit 10       # first N orgs only
    python -m backend.sync.hubspot --check          # count gtm companies in HubSpot

Priority mapping (max ICP score across an org's signals): >=70 hot, >=50 warm,
else watch. Classification only stores scores >=30, so anything synced is relevant.
"""

import argparse
import sys
from collections import defaultdict

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

from backend.db import (
    enriched_contacts,
    get_engine,
    icp_relevance,
    organizations,
    outreach_drafts,
    signal_organizations,
    signals,
)

load_dotenv()

BASE = "https://api.hubapi.com"


def _headers():
    import os

    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        sys.exit("HUBSPOT_TOKEN not set (.env)")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _priority(score):
    return "hot" if score >= 70 else "warm" if score >= 50 else "watch"


def _signal_text(sig, categories):
    cats = ", ".join(f"{c} {s}" for c, s in categories) or "n/a"
    parts = [sig.summary_fr or sig.title or "Signal détecté"]
    meta = [f"source: {sig.source.upper()}"]
    if sig.published_at:
        meta.append(f"publié le {sig.published_at}")
    if sig.deadline_at:
        meta.append(f"réponse avant le {sig.deadline_at}")
    meta.append(f"pertinence ICP: {cats}")
    parts.append(f"({' · '.join(meta)})")
    return " ".join(parts)


def load_sync_plan(engine, limit=None):
    """One entry per org with >= 1 relevant signal: properties ready for HubSpot."""
    with engine.connect() as conn:
        score_by_signal = defaultdict(list)
        for row in conn.execute(select(icp_relevance)):
            score_by_signal[row.signal_id].append((row.icp_category, row.score))

        sigs = {s.id: s for s in conn.execute(select(signals))}
        orgs = {o.id: o for o in conn.execute(select(organizations))}

        sig_ids_by_org = defaultdict(list)
        for link in conn.execute(select(signal_organizations)):
            if link.signal_id in score_by_signal:
                sig_ids_by_org[link.org_id].append(link.signal_id)

        draft_by_signal = {}
        for d in conn.execute(select(outreach_drafts).order_by(outreach_drafts.c.created_at)):
            draft_by_signal[d.signal_id] = d  # latest wins

        contacts_by_org = defaultdict(list)
        for c in conn.execute(select(enriched_contacts)):
            if c.email:
                contacts_by_org[c.org_id].append(c)

    plan = []
    for org_id, sig_ids in sig_ids_by_org.items():
        org = orgs[org_id]
        best_score = max(s for sid in sig_ids for _, s in score_by_signal[sid])
        # freshest relevant signal carries the gtm_signal text
        lead_sig = max(
            (sigs[sid] for sid in sig_ids),
            key=lambda s: (s.published_at is not None, s.published_at),
        )
        cats = sorted(score_by_signal[lead_sig.id], key=lambda cs: -cs[1])
        props = {
            "name": org.name,
            "country": "France",
            "gtm_signal": _signal_text(lead_sig, cats),
            "gtm_priority": _priority(best_score),
        }
        if org.siren:
            props["siren"] = org.siren
        if lead_sig.published_at:
            props["gtm_signal_date"] = str(lead_sig.published_at)
        draft = next((draft_by_signal[sid] for sid in sig_ids if sid in draft_by_signal), None)
        if draft:
            props["gtm_approach_draft"] = f"Objet : {draft.subject}\n\n{draft.body}"
        plan.append({"org": org, "props": props, "contacts": contacts_by_org[org_id]})

    plan.sort(key=lambda e: ["hot", "warm", "watch"].index(e["props"]["gtm_priority"]))
    return plan[:limit] if limit else plan


def _search_one(client, object_type, prop, value):
    r = client.post(f"{BASE}/crm/v3/objects/{object_type}/search", headers=_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": prop, "operator": "EQ", "value": value}]}],
        "properties": ["name"], "limit": 1,
    })
    r.raise_for_status()
    results = r.json()["results"]
    return results[0]["id"] if results else None


def upsert_company(client, org, props):
    company_id = org.siren and _search_one(client, "companies", "siren", org.siren)
    company_id = company_id or _search_one(client, "companies", "name", org.name)
    if company_id:
        r = client.patch(f"{BASE}/crm/v3/objects/companies/{company_id}",
                         headers=_headers(), json={"properties": props})
    else:
        r = client.post(f"{BASE}/crm/v3/objects/companies",
                        headers=_headers(), json={"properties": props})
    r.raise_for_status()
    return r.json()["id"], bool(company_id)


def upsert_contact(client, contact, company_id):
    props = {"email": contact.email}
    if contact.full_name:
        first, _, last = contact.full_name.partition(" ")
        props.update({"firstname": first, "lastname": last or first})
    if contact.job_title:
        props["jobtitle"] = contact.job_title
    if contact.phone:
        props["phone"] = contact.phone
    contact_id = _search_one(client, "contacts", "email", contact.email)
    if contact_id:
        r = client.patch(f"{BASE}/crm/v3/objects/contacts/{contact_id}",
                         headers=_headers(), json={"properties": props})
    else:
        r = client.post(f"{BASE}/crm/v3/objects/contacts",
                        headers=_headers(), json={"properties": props})
    r.raise_for_status()
    contact_id = r.json()["id"]
    r = client.put(
        f"{BASE}/crm/v4/objects/companies/{company_id}/associations/default/contacts/{contact_id}",
        headers=_headers(),
    )
    r.raise_for_status()
    return contact_id


def check(client):
    r = client.post(f"{BASE}/crm/v3/objects/companies/search", headers=_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": "gtm_priority", "operator": "HAS_PROPERTY"}]}],
        "limit": 200, "properties": ["name", "gtm_priority", "gtm_signal_date"],
    })
    r.raise_for_status()
    rows = r.json()["results"]
    by_prio = defaultdict(int)
    for row in rows:
        by_prio[row["properties"].get("gtm_priority", "?")] += 1
    print(f"{len(rows)} gtm companies in HubSpot — " +
          ", ".join(f"{k}: {v}" for k, v in sorted(by_prio.items())))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        with httpx.Client(timeout=30) as client:
            check(client)
        return

    plan = load_sync_plan(get_engine(), limit=args.limit)
    print(f"{len(plan)} orgs to sync"
          + f" ({sum(len(e['contacts']) for e in plan)} contacts, "
          + f"{sum('gtm_approach_draft' in e['props'] for e in plan)} drafts)")

    if args.dry_run:
        for e in plan:
            print(f"  {e['props']['gtm_priority']:5} {e['org'].name}"
                  + (f" [+{len(e['contacts'])} contacts]" if e["contacts"] else ""))
        return

    created = updated = n_contacts = 0
    with httpx.Client(timeout=30) as client:
        for e in plan:
            company_id, existed = upsert_company(client, e["org"], e["props"])
            created += not existed
            updated += existed
            for c in e["contacts"]:
                upsert_contact(client, c, company_id)
                n_contacts += 1
            print(f"{'~' if existed else '+'} {e['org'].name} [{e['props']['gtm_priority']}]")
    print(f"\ndone: {created} companies created, {updated} updated, {n_contacts} contacts")


if __name__ == "__main__":
    main()
