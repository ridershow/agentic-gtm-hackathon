"""Meeting brochure generator — arms the rep before meeting a lead.

Takes a HubSpot account, composes a meeting brief/brochure grounded ONLY in
CRM data (real signal, real contacts, evidence), generates it with Gamma and
posts the URL back on the company as a note. No invented specs, ever.

The Lovable "Prepare meeting" button triggers this flow.

The supplier's brand and offer copy are CONFIG, not code: set BROCHURE_BRAND /
BROCHURE_BRAND_STYLE in .env and drop the real offer copy in
backend/agents/offer.local.md (gitignored). Without them, a fictional sample
offer is used so the flow stays demoable.

Usage:
    python -m backend.agents.brochure --company "Sepalumic"
"""

import argparse
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

HS = "https://api.hubapi.com"
GAMMA = "https://public-api.gamma.app/v1.0/generations"

BRAND = os.environ.get("BROCHURE_BRAND", "Atelier Nordal (sample brand)")
TAGLINE = os.environ.get("BROCHURE_TAGLINE",
                         "Composants haute température pour lignes d'extrusion")
BRAND_STYLE = os.environ.get(
    "BROCHURE_BRAND_STYLE",
    "Neutral industrial brand. Dark slate headings, one restrained accent color, "
    "light background. Industrial imagery only (conveyor lines, extrusion, technical "
    "textiles). French language. Keep every product name, spec, name and figure "
    "EXACTLY as written.")

# Real offer copy lives in offer.local.md (gitignored, per client/supplier).
# The fallback below is FICTIONAL sample copy — demo plumbing, not a real offer.
_OFFER_FILE = Path(__file__).with_name("offer.local.md")
SAMPLE_OFFER = """**{brand} — {tagline}**

**Le convoyage du profilé chaud, sans marquage.** Bandes, feutres et joints haute
température fabriqués sur mesure pour chaque poste de la ligne, de la presse à
l'emballage.

**Une solution à chaque poste de votre ligne :**
- Bandes sans fin haute densité — tables de sortie, zéro marquage
- Habillage de rouleaux — évite marques et défauts de convoyage
- Feutres découpés sur mesure — barres de transfert et zones de refroidissement

**Sur mesure** : largeur, longueur, épaisseur et matière adaptées à votre ligne.

*(Copy d'exemple fictive — remplacer par l'offre réelle du fournisseur dans
offer.local.md.)*"""

OFFER = (_OFFER_FILE.read_text() if _OFFER_FILE.exists()
         else SAMPLE_OFFER.format(brand=BRAND, tagline=TAGLINE))


def hs_headers():
    return {"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
            "Content-Type": "application/json"}


def fetch_account(client, name):
    r = client.post(f"{HS}/crm/v3/objects/companies/search", headers=hs_headers(), json={
        "filterGroups": [{"filters": [{"propertyName": "name", "operator": "CONTAINS_TOKEN", "value": name}]}],
        "properties": ["name", "domain", "city", "description", "gtm_signal", "gtm_signal_date", "gtm_priority"],
        "limit": 1})
    results = r.json()["results"]
    if not results:
        raise SystemExit(f"no company matching '{name}'")
    comp = results[0]
    a = client.get(f"{HS}/crm/v4/objects/companies/{comp['id']}/associations/contacts",
                   headers=hs_headers()).json()
    contacts = []
    for assoc in a.get("results", [])[:3]:
        cr = client.get(f"{HS}/crm/v3/objects/contacts/{assoc['toObjectId']}"
                        "?properties=firstname,lastname,jobtitle,email,gtm_provenance",
                        headers=hs_headers()).json()
        contacts.append(cr["properties"])
    return comp, contacts


def compose(comp, contacts):
    p = comp["properties"]
    who = "\n".join(f"- **{c.get('firstname','')} {c.get('lastname','')}** — {c.get('jobtitle') or 'role tbc'}"
                    + (f" · {c['email']}" if c.get("email") else " · phone/email via manual search")
                    for c in contacts) or "- Decision-makers flagged for manual search"
    signal = p.get("gtm_signal") or "No dated signal on file — discovery meeting."
    return f"""# {BRAND} — Brief de rencontre : {p['name']}
{TAGLINE} · {p.get('city') or ''} · priorité : {p.get('gtm_priority') or 'watch'}
---
# Pourquoi maintenant — leur projet
{signal}
C'est la fenêtre : les décisions autour de ce projet se prennent maintenant. Arriver avec ce contexte, c'est la différence entre un appel fournisseur et une conversation d'égal à égal.
---
# Qui vous rencontrez
{who}
---
# L'offre {BRAND}, mappée sur leur ligne
{OFFER}
---
# Angles de conversation
- Ouvrir sur LEUR projet (l'investissement ci-dessus), pas sur nous, dans la première minute.
- Marché fini : l'objectif du rendez-vous est la relation, pas le closing.
- Next step à proposer : envoi des caractéristiques de leur ligne au bureau d'études, ou visite de site calée sur leur calendrier projet.
---
# À propos de ce document
Généré par le GTM engine depuis les données CRM live (signal daté, contacts, preuves). Copy produit : fournie par le fournisseur (offer.local.md). Aucune spec inventée.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", required=True)
    args = ap.parse_args()
    with httpx.Client(timeout=60) as client:
        comp, contacts = fetch_account(client, args.company)
        text = compose(comp, contacts)
        r = client.post(GAMMA, headers={"X-API-KEY": os.environ["GAMMA_API_KEY"]},
                        json={"inputText": text, "textMode": "preserve", "format": "document",
                              "numCards": 6,
                              "additionalInstructions": f"Brand: {BRAND}. {BRAND_STYLE}"})
        gid = r.json()["generationId"]
        print("generation", gid)
        url = None
        for _ in range(30):
            time.sleep(10)
            g = client.get(f"{GAMMA}/{gid}", headers={"X-API-KEY": os.environ["GAMMA_API_KEY"]}).json()
            if g.get("status") == "completed":
                url = g["gammaUrl"]
                break
            print("  ...", g.get("status"))
        if not url:
            raise SystemExit("gamma generation did not complete")
        client.post(f"{HS}/crm/v3/objects/notes", headers=hs_headers(), json={
            "properties": {"hs_note_body": f"Meeting brochure generated: {url}",
                           "hs_timestamp": int(time.time() * 1000)},
            "associations": [{"to": {"id": comp["id"]},
                              "types": [{"associationCategory": "HUBSPOT_DEFINED",
                                         "associationTypeId": 190}]}]})
        print(f"BROCHURE {comp['properties']['name']}: {url} (note posted on the account)")


if __name__ == "__main__":
    main()
