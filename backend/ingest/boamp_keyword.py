"""BOAMP keyword ingestion for high-temperature textile buying signals.

Two complementary searches run sequentially:

  A) Keyword search — tenders mentioning réfractaires / textiles haute température /
     laine céramique across France (no dept filter). Catches direct procurement intent
     for the product from any industrial buyer.

  B) Company-name search — for each of the 23 atlas companies, checks if they appear
     as a buyer in BOAMP. Rare for private companies but worth scanning.

Both modes also seed the atlas companies into the local organizations table so the
classify → sync pipeline can find them by siren and push results to HubSpot.

Signals are linked to atlas companies when:
  - The buyer name matches one of them (role="buyer")
  - The signal's dept matches an atlas company's dept (role="prospect")

Usage:
    python -m backend.ingest.boamp_keyword --days 365
    python -m backend.ingest.boamp_keyword --days 365 --dry-run
    python -m backend.ingest.boamp_keyword --days 365 --mode keyword   # Mode A only
    python -m backend.ingest.boamp_keyword --days 365 --mode company   # Mode B only
"""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.db import get_engine, init_db, organizations, signal_organizations, signals
from backend.ingest.boamp import (
    MARKET_TYPES,
    NATURES,
    PAGE_SIZE,
    BASE_URL,
    fetch_records,
    first,
    parse_date,
    upsert_buyer,
    upsert_signal,
)

import httpx

SEED = Path(__file__).parent / "atlas_seed.json"

# Product-specific keywords — high-temperature textiles for aluminium extrusion
KEYWORDS = [
    "réfractaire",
    "laine céramique",
    "textile thermique",
    "textile technique",
    "fibre céramique",
    "protection thermique",
    "isolation réfractaire",
    "matériaux réfractaires",
    "silice amorphe",
    "joint haute température",
    "revêtement thermique",
]


def _dept(postal: str) -> str:
    return postal[:2]


def _seed_atlas_orgs(conn, companies: list[dict]) -> dict[str, int]:
    """Upsert atlas companies into organizations table. Returns {siren: org_id}."""
    result = {}
    for c in companies:
        stmt = sqlite_insert(organizations).values(
            siren=c["siren"],
            name=c["name"],
            kind="company",
            raw=c,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["siren"],
            set_={"name": stmt.excluded.name, "raw": stmt.excluded.raw},
        )
        conn.execute(stmt)
        org_id = conn.execute(
            select(organizations.c.id).where(organizations.c.siren == c["siren"])
        ).scalar_one()
        result[c["siren"]] = org_id
    return result


def _link(conn, signal_id: int, org_id: int, role: str):
    stmt = sqlite_insert(signal_organizations).values(
        signal_id=signal_id, org_id=org_id, role=role
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["signal_id", "org_id", "role"])
    conn.execute(stmt)


def _build_keyword_where(since: date) -> str:
    natures = " OR ".join(f'nature_categorise_libelle LIKE "{n}"' for n in NATURES)
    types = " OR ".join(f'type_marche = "{t}"' for t in MARKET_TYPES)
    kws = " OR ".join(f'objet LIKE "%{kw}%"' for kw in KEYWORDS)
    return (
        f"dateparution >= date'{since.isoformat()}'"
        f" AND ({natures})"
        f" AND ({types})"
        f" AND ({kws})"
    )


def _build_company_where(legal_entity: str, since: date) -> str:
    # Simplify name: take first meaningful token to improve LIKE match rate
    simplified = legal_entity.split("(")[0].strip().rstrip()
    natures = " OR ".join(f'nature_categorise_libelle LIKE "{n}"' for n in NATURES)
    return (
        f"dateparution >= date'{since.isoformat()}'"
        f" AND ({natures})"
        f" AND nomacheteur LIKE \"%{simplified}%\""
    )


def run_keyword_search(engine, companies: list[dict], org_ids: dict[str, int], since: date):
    """Mode A: nationwide keyword search for high-temp textile procurement."""
    dept_to_orgs: dict[str, list[tuple[str, int]]] = {}
    for c in companies:
        d = _dept(c["dept"])
        dept_to_orgs.setdefault(d, []).append((c["siren"], org_ids[c["siren"]]))

    where = _build_keyword_where(since)
    print(f"\n[Mode A] Keyword search since {since}...")
    count = linked_buyer = linked_prospect = 0

    with engine.begin() as conn:
        for record in fetch_records(where):
            sig_id = upsert_signal(conn, record)
            buyer_name = record.get("nomacheteur")
            if buyer_name:
                upsert_buyer(conn, sig_id, buyer_name)

            # Link to atlas companies by dept (prospect) or name match (buyer)
            sig_dept = first(record.get("code_departement")) or ""
            for siren, org_id in dept_to_orgs.get(sig_dept, []):
                _link(conn, sig_id, org_id, "prospect")
                linked_prospect += 1

            count += 1

    print(f"  {count} keyword signals ingested ({linked_buyer} buyer links, {linked_prospect} prospect links)")
    return count


def run_company_search(engine, companies: list[dict], org_ids: dict[str, int], since: date):
    """Mode B: check if any atlas company appears as a BOAMP buyer."""
    print(f"\n[Mode B] Company-name search for {len(companies)} atlas companies...")
    total = direct_hits = 0

    for company in companies:
        where = _build_company_where(company["legal_entity"], since)
        count = 0
        with engine.begin() as conn:
            for record in fetch_records(where):
                sig_id = upsert_signal(conn, record)
                _link(conn, sig_id, org_ids[company["siren"]], "buyer")
                # Also upsert buyer org entry (matches by name)
                buyer_name = record.get("nomacheteur")
                if buyer_name:
                    upsert_buyer(conn, sig_id, buyer_name)
                count += 1
        if count:
            print(f"  {company['name']}: {count} direct RFP(s) found")
            direct_hits += count
        total += count

    if not direct_hits:
        print("  No direct RFPs found (expected for private companies)")
    print(f"  Total: {direct_hits} direct company RFPs")
    return total


def run(days: int, mode: str = "both", dry_run: bool = False):
    companies = json.load(open(SEED))
    engine = init_db(get_engine())
    since = date.today() - timedelta(days=days)

    # Always seed atlas companies into SQLite first
    with engine.begin() as conn:
        org_ids = _seed_atlas_orgs(conn, companies)
    print(f"Seeded {len(org_ids)} atlas companies into organizations table")

    if dry_run:
        kw_where = _build_keyword_where(since)
        print(f"\n[dry-run] Keyword WHERE clause:\n  {kw_where}")
        print(f"\n[dry-run] Would search {len(companies)} company names for Mode B")
        return

    total_a = total_b = 0
    if mode in ("both", "keyword"):
        total_a = run_keyword_search(engine, companies, org_ids, since)
    if mode in ("both", "company"):
        total_b = run_company_search(engine, companies, org_ids, since)

    print(f"\nTotal: {total_a + total_b} signals ingested")
    print("Next: python -m backend.workers.classify --limit 500")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Ingest BOAMP thermal-textile signals")
    ap.add_argument("--days", type=int, default=365, help="Lookback window in days (default: 365)")
    ap.add_argument("--mode", choices=["both", "keyword", "company"], default="both")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(args.days, args.mode, args.dry_run)
