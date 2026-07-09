"""Database layer. Postgres (Supabase) via DATABASE_URL, SQLite fallback for local dev."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    SmallInteger,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)

load_dotenv()

metadata = MetaData()

# BigInteger autoincrement doesn't work on SQLite; Integer maps to 64-bit there anyway.
_PK = Integer

signals = Table(
    "signals",
    metadata,
    Column("id", _PK, primary_key=True, autoincrement=True),
    Column("type", Text, nullable=False),  # rfp | icpe | permit | bodacc | sillage
    Column("source", Text, nullable=False),  # boamp | georisques | ...
    Column("source_id", Text, nullable=False),
    Column("published_at", Date),
    Column("deadline_at", Date),
    Column("departement", Text),
    Column("raw", JSON, nullable=False),
    # Claude-extracted fields (classification worker fills these)
    Column("title", Text),
    Column("summary_fr", Text),
    Column("project_type", Text),
    Column("building_type", Text),
    Column("works", JSON),
    Column("est_value_eur", Numeric),
    Column("processed_at", DateTime(timezone=True)),  # NULL = awaiting classification
    UniqueConstraint("source", "source_id", name="uq_signals_source"),
)

organizations = Table(
    "organizations",
    metadata,
    Column("id", _PK, primary_key=True, autoincrement=True),
    Column("siren", Text, unique=True),
    Column("name", Text, nullable=False, unique=True),
    Column("kind", Text),  # public_buyer | company | contractor | engineering
    Column("raw", JSON),
)

signal_organizations = Table(
    "signal_organizations",
    metadata,
    Column("signal_id", ForeignKey("signals.id"), primary_key=True),
    Column("org_id", ForeignKey("organizations.id"), primary_key=True),
    Column("role", Text, primary_key=True),  # buyer | winner | owner | contractor
)

icp_relevance = Table(
    "icp_relevance",
    metadata,
    Column("signal_id", ForeignKey("signals.id"), primary_key=True),
    Column("icp_category", Text, primary_key=True),
    Column("score", SmallInteger),
    Column("reasoning", Text),
)

enriched_contacts = Table(
    "enriched_contacts",
    metadata,
    Column("id", _PK, primary_key=True, autoincrement=True),
    Column("org_id", ForeignKey("organizations.id")),
    Column("full_name", Text),
    Column("job_title", Text),
    Column("email", Text),
    Column("phone", Text),
    Column("linkedin_url", Text),
    Column("source", Text, server_default="fullenrich"),
    Column("raw", JSON),
    Column("enriched_at", DateTime(timezone=True), server_default=func.now()),
)

outreach_drafts = Table(
    "outreach_drafts",
    metadata,
    Column("id", _PK, primary_key=True, autoincrement=True),
    Column("signal_id", ForeignKey("signals.id")),
    Column("contact_id", ForeignKey("enriched_contacts.id")),
    Column("subject", Text),
    Column("body", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


def get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        Path("data").mkdir(exist_ok=True)
        url = "sqlite:///data/gtm.db"
    return create_engine(url)


def init_db(engine=None):
    engine = engine or get_engine()
    metadata.create_all(engine)
    return engine


if __name__ == "__main__":
    eng = init_db()
    print(f"Schema created on {eng.url}")
