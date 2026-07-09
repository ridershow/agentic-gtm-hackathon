"""Classification worker — Claude scores each RFP signal against the 5 ICP categories.

Reads signals where processed_at IS NULL, batches them into one Claude call
(forced tool use = validated JSON), writes back structured fields + icp_relevance rows.

Usage:
    python -m backend.workers.classify --limit 50 --batch-size 15
"""

import argparse
import json
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.db import get_engine, icp_relevance, init_db, signals

load_dotenv()

MODEL = "claude-sonnet-4-6"

ICP_CATEGORIES = ["equipment", "envelope", "installer", "services", "distributor"]

SYSTEM_PROMPT = """\
Tu analyses des annonces de marchés publics français (BOAMP) pour un outil de prospection \
destiné aux PME industrielles B2B qui vendent aux usines, entrepôts et bâtiments.

Les 5 catégories de PME utilisatrices (ICP) :
- equipment : fabricants d'équipements industriels (rayonnages, portes industrielles, convoyeurs, \
lignes d'emballage, levage, froid industriel). Cible : projets où de l'équipement sera acheté/installé.
- envelope : spécialistes de l'enveloppe du bâtiment (sols industriels, toiture/bardage, quais de \
chargement, protection incendie, clôtures). Cible : constructions/rénovations où ils doivent être prescrits tôt.
- installer : installateurs et intégrateurs techniques (électricité industrielle, automatisme, \
tuyauterie, ventilation, air comprimé). Cible : lots techniques, sous-traitance du titulaire.
- services : services et maintenance industriels (contrats de maintenance, nettoyage industriel, \
métrologie, rétrofit, efficacité énergétique). Cible : sites entrant en exploitation, renouvellements.
- distributor : distributeurs techniques (fournitures industrielles, composants, EPI, consommables). \
Cible : nouveaux sites dans leur zone de livraison.

Pour chaque annonce, évalue la pertinence 0-100 par catégorie. Ne retourne que les catégories \
avec un score >= 30. Une annonce sans lien avec le monde industriel/bâtiment (ex: prestations \
intellectuelles, denrées alimentaires) n'a aucune catégorie pertinente : retourne une liste vide.
Le résumé doit être en français simple, 1-2 phrases, compréhensible par un dirigeant de PME non technique."""

CLASSIFY_TOOL = {
    "name": "record_classifications",
    "description": "Enregistre la classification structurée de chaque annonce du lot.",
    "input_schema": {
        "type": "object",
        "properties": {
            "classifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_id": {"type": "string"},
                        "project_type": {
                            "type": "string",
                            "enum": ["construction", "extension", "renovation", "equipment_purchase",
                                     "maintenance", "infrastructure", "other"],
                        },
                        "building_type": {
                            "type": "string",
                            "enum": ["warehouse", "factory", "logistics", "public_facility",
                                     "office", "infrastructure", "other", "none"],
                        },
                        "works": {"type": "array", "items": {"type": "string"}},
                        "summary_fr": {"type": "string"},
                        "icp_categories": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category": {"type": "string", "enum": ICP_CATEGORIES},
                                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                    "reasoning": {"type": "string"},
                                },
                                "required": ["category", "score", "reasoning"],
                            },
                        },
                    },
                    "required": ["source_id", "project_type", "building_type", "works",
                                 "summary_fr", "icp_categories"],
                },
            }
        },
        "required": ["classifications"],
    },
}


def extract_amount(raw: dict) -> float | None:
    """Dig the eForms payload for a total/estimated amount (EUR)."""
    donnees = raw.get("donnees")
    if isinstance(donnees, str):
        try:
            donnees = json.loads(donnees)
        except json.JSONDecodeError:
            return None

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("cbc:TotalAmount", "cbc:EstimatedOverallContractAmount", "cbc:AmountAmount"):
                    text = value.get("#text") if isinstance(value, dict) else value
                    try:
                        amount = float(text)
                        if amount > 0:
                            return amount
                    except (TypeError, ValueError):
                        pass
                found = walk(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = walk(item)
                if found is not None:
                    return found
        return None

    return walk(donnees) if donnees else None


def compact_announcement(row) -> dict:
    raw = row.raw if isinstance(row.raw, dict) else json.loads(row.raw)
    return {
        "source_id": row.source_id,
        "objet": raw.get("objet"),
        "acheteur": raw.get("nomacheteur"),
        "descripteurs": raw.get("descripteur_libelle"),
        "type_marche": raw.get("type_marche"),
        "nature": raw.get("nature_categorise_libelle"),  # Avis de marché/ vs Résultat de marché/
        "departement": row.departement,
    }


def classify_batch(client: anthropic.Anthropic, batch: list[dict]) -> list[dict]:
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "record_classifications"},
        messages=[{
            "role": "user",
            "content": f"Classifie ces {len(batch)} annonces :\n\n{json.dumps(batch, ensure_ascii=False)}",
        }],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input["classifications"]
    return []


def save_classification(conn, signal_id: int, result: dict, est_value: float | None):
    conn.execute(
        signals.update()
        .where(signals.c.id == signal_id)
        .values(
            project_type=result["project_type"],
            building_type=result["building_type"],
            works=result["works"],
            summary_fr=result["summary_fr"],
            est_value_eur=est_value,
            processed_at=datetime.now(timezone.utc),
        )
    )
    dialect_insert = pg_insert if conn.dialect.name == "postgresql" else sqlite_insert
    for cat in result["icp_categories"]:
        stmt = dialect_insert(icp_relevance).values(
            signal_id=signal_id,
            icp_category=cat["category"],
            score=cat["score"],
            reasoning=cat["reasoning"],
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["signal_id", "icp_category"],
            set_={"score": stmt.excluded.score, "reasoning": stmt.excluded.reasoning},
        )
        conn.execute(stmt)


def run(limit: int, batch_size: int):
    engine = init_db(get_engine())
    client = anthropic.Anthropic()

    with engine.connect() as conn:
        rows = conn.execute(
            select(signals.c.id, signals.c.source_id, signals.c.departement, signals.c.raw)
            .where(signals.c.processed_at.is_(None))
            .limit(limit)
        ).fetchall()

    if not rows:
        print("Nothing to classify — all signals processed.")
        return
    print(f"Classifying {len(rows)} signals (batches of {batch_size}, model {MODEL})")

    by_source_id = {row.source_id: row for row in rows}
    done = relevant = 0
    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        batch = [compact_announcement(row) for row in chunk]
        results = classify_batch(client, batch)

        with engine.begin() as conn:
            for result in results:
                row = by_source_id.get(result["source_id"])
                if row is None:  # hallucinated id — the real one stays unprocessed, retried next run
                    continue
                raw = row.raw if isinstance(row.raw, dict) else json.loads(row.raw)
                save_classification(conn, row.id, result, extract_amount(raw))
                done += 1
                if result["icp_categories"]:
                    relevant += 1
        print(f"  {done}/{len(rows)} classified ({relevant} ICP-relevant)")

    print(f"Done. {done} classified, {relevant} relevant to at least one ICP category.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify unprocessed signals with Claude")
    parser.add_argument("--limit", type=int, default=200, help="Max signals this run (default: 200)")
    parser.add_argument("--batch-size", type=int, default=15, help="Announcements per Claude call (default: 15)")
    args = parser.parse_args()
    run(args.limit, args.batch_size)
