"""Meeting brochure generator — arms the rep before meeting a lead.

Takes a HubSpot account, composes a meeting brief/brochure grounded ONLY in
CRM data (real signal, real contacts, evidence), generates it with Gamma and
posts the URL back on the company as a note. No invented specs, ever.

The Lovable "Prepare meeting" button triggers this flow.

Usage:
    python -m backend.agents.brochure --company "Sepalumic"
"""

import argparse
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

HS = "https://api.hubapi.com"
GAMMA = "https://public-api.gamma.app/v1.0/generations"

# Offer copy: the supplier brochure v1 (source: example.invalid,
# no invented specs). Brand: the supplier orange #f7941d / red #d93a26 / dark #24282e.
OFFER = """**the supplier — Solutions textiles haute température pour l'extrusion d'aluminium**
ProductA · ProductB · ProductC · ProductD — example.invalid

**Le convoyage du profilé chaud, sans marquage.** Sur une table d'extrusion, une bande trop aérée et mal dimensionnée s'écrase sous le poids des profilés lourds. En intégrant les technologies de tissage haute densité de a partner brand, the supplier produit des bandes plus denses et plus compactes que les standards du marché, associées à ses gammes historiques de feutres, bandes et joints haute température de 200 à 1000 °C.

**Une solution à chaque poste de votre ligne, de la presse à l'emballage :**
- Gamme PBO la gamme partenaire — hot-end, au plus près de la presse (jusqu'à 600 °C)
- Bandes sans fin la gamme partenaire — PBO ou aramide, tissage haute densité, tables de sortie, zéro marquage
- ProductA 600 — bande multicouche inox + aramide régénéré, stabilité dimensionnelle (jusqu'à 1400 °C inox)
- ProductB Contact — habillage des rouleaux de transport, évite marques et défauts de convoyage
- ProductC Préox / SS — feutres découpés sur mesure pour barres de transfert et zones de refroidissement

**Vous utilisiez les solutions de a partner brand ? Votre référence la gamme partenaire existe toujours.** Depuis l'acquisition des machines haute température de a partner brand (janvier 2025), la technologie, la recette et la qualité de la marque britannique perdurent dans les ateliers the supplier à France.

**L'alliance de deux savoir-faire** : +50 ans d'expertise thermique the supplier (PBO, para-aramide, préox) × la technologie de tissage la gamme partenaire. Fabrication 100 % française, 600 références, 300 clients. Chaque référence est fabriquée sur mesure : largeur, longueur, épaisseur et fibre adaptées à votre ligne.

**Votre contact : ***removed***, Managing Director — ***removed*** — the supplier, ***removed*** — ***removed*****"""


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
    return f"""# the supplier — Brief de rencontre : {p['name']}
Solutions textiles haute température pour l'extrusion d'aluminium · {p.get('city') or ''} · priorité : {p.get('gtm_priority') or 'watch'}
---
# Pourquoi maintenant — leur projet
{signal}
C'est la fenêtre : les décisions autour de ce projet se prennent maintenant. Arriver avec ce contexte, c'est la différence entre un appel fournisseur et une conversation d'égal à égal.
---
# Qui vous rencontrez
{who}
---
# L'offre the supplier, mappée sur leur ligne
{OFFER}
---
# Angles de conversation
- Ouvrir sur LEUR projet (l'investissement ci-dessus), pas sur nous, dans la première minute.
- Si leur ligne utilisait des références a partner brand : elles existent toujours, fabriquées à France.
- Marché fini : l'objectif du rendez-vous est la relation, pas le closing.
- Next step à proposer : envoi des caractéristiques de leur ligne au bureau d'études, ou visite de site calée sur leur calendrier projet.
---
# À propos de ce document
Généré par le GTM engine depuis les données CRM live (signal daté, contacts, preuves). Copy produit : brochure the supplier (source example.invalid). Aucune spec inventée.
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
                              "additionalInstructions": "Brand: the supplier. Colors: orange #f7941d as primary accent, red #d93a26 sparingly, dark #24282e for headings, light background. Industrial textile/aluminium-extrusion imagery only (conveyor belts, extrusion lines, technical weaving). French language. Keep every product name, temperature spec, name and figure EXACTLY as written."})
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
