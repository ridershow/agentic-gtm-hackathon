"""BOAMP ingestion — French public tenders (RFPs) into the signals table.

API: OpenDataSoft Explore v2, free, no auth.
https://boamp-datadila.opendatasoft.com/explore/dataset/boamp/api/

Usage:
    python -m backend.ingest.boamp --departments 69,38,01 --days 90
"""

import argparse
from datetime import date, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.db import get_engine, init_db, organizations, signal_organizations, signals

BASE_URL = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
PAGE_SIZE = 100  # ODS max per page

# Cast wide: open tenders (the pipeline) + awards (contractor mapping).
# Precise industrial-relevance filtering is Claude's job, not the query's.
NATURES = ("Avis de marché", "Résultat de marché")
MARKET_TYPES = ("TRAVAUX", "FOURNITURES")


def build_where(departments: list[str], since: date) -> str:
    deps = " OR ".join(f'code_departement = "{d}"' for d in departments)
    # Field values carry a trailing slash ("Avis de marché/") — LIKE instead of =
    natures = " OR ".join(f'nature_categorise_libelle LIKE "{n}"' for n in NATURES)
    types = " OR ".join(f'type_marche = "{t}"' for t in MARKET_TYPES)
    return f"dateparution >= date'{since.isoformat()}' AND ({deps}) AND ({natures}) AND ({types})"


def fetch_records(where: str):
    offset = 0
    with httpx.Client(timeout=30) as client:
        while True:
            resp = client.get(
                BASE_URL,
                params={"where": where, "order_by": "dateparution DESC", "limit": PAGE_SIZE, "offset": offset},
            )
            resp.raise_for_status()
            payload = resp.json()
            results = payload.get("results", [])
            if offset == 0:
                print(f"Total matching records: {payload.get('total_count')}")
            if not results:
                return
            yield from results
            offset += PAGE_SIZE


def first(value):
    """BOAMP returns several fields as arrays (code_departement, type_marche...)."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def parse_date(value) -> date | None:
    """BOAMP dates are ISO strings, sometimes with a time component."""
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def upsert_signal(conn, record: dict) -> int | None:
    dialect_insert = pg_insert if conn.dialect.name == "postgresql" else sqlite_insert
    row = {
        "type": "rfp",
        "source": "boamp",
        "source_id": record["idweb"],
        "published_at": parse_date(record.get("dateparution")),
        "deadline_at": parse_date(record.get("datelimitereponse")),
        "departement": first(record.get("code_departement")),
        "title": record.get("objet"),
        "raw": record,
    }
    stmt = dialect_insert(signals).values(**row)
    stmt = stmt.on_conflict_do_update(
        index_elements=["source", "source_id"],
        set_={"raw": stmt.excluded.raw, "deadline_at": stmt.excluded.deadline_at},
    )
    conn.execute(stmt)
    return conn.execute(
        select(signals.c.id).where(signals.c.source == "boamp", signals.c.source_id == record["idweb"])
    ).scalar_one()


def upsert_buyer(conn, signal_id: int, buyer_name: str):
    dialect_insert = pg_insert if conn.dialect.name == "postgresql" else sqlite_insert
    stmt = dialect_insert(organizations).values(name=buyer_name, kind="public_buyer")
    stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
    conn.execute(stmt)
    org_id = conn.execute(select(organizations.c.id).where(organizations.c.name == buyer_name)).scalar_one()

    link = dialect_insert(signal_organizations).values(signal_id=signal_id, org_id=org_id, role="buyer")
    link = link.on_conflict_do_nothing(index_elements=["signal_id", "org_id", "role"])
    conn.execute(link)


def run(departments: list[str], days: int):
    engine = init_db(get_engine())
    since = date.today() - timedelta(days=days)
    where = build_where(departments, since)
    print(f"Ingesting BOAMP: departments={departments}, since={since}")

    count = 0
    with engine.begin() as conn:
        for record in fetch_records(where):
            signal_id = upsert_signal(conn, record)
            buyer = record.get("nomacheteur")
            if buyer:
                upsert_buyer(conn, signal_id, buyer)
            count += 1
            if count % 100 == 0:
                print(f"  {count} records...")
    print(f"Done. {count} RFP signals ingested/updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest BOAMP tenders into the signals DB")
    parser.add_argument("--departments", default="69", help="Comma-separated department codes (default: 69)")
    parser.add_argument("--days", type=int, default=90, help="Lookback window in days (default: 90)")
    args = parser.parse_args()
    run([d.strip() for d in args.departments.split(",")], args.days)
