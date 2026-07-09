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

# Offer copy: Marathon by Ferlam brochure v1 (source: ferlam-technologies.fr,
# no invented specs). Brand: Ferlam orange #f7941d / red #d93a26 / dark #24282e.
OFFER = """**Marathon by Ferlam — Solutions textiles haute température pour l'extrusion d'aluminium**
FerlaBelt · FerlaTape · FerlaFelt · FerlaBraid — www.ferlam-technologies.fr

**Le convoyage du profilé chaud, sans marquage.** Sur une table d'extrusion, une bande trop aérée et mal dimensionnée s'écrase sous le poids des profilés lourds. En intégrant les technologies de tissage haute densité de Marathon Belting, Ferlam Technologies produit des bandes plus denses et plus compactes que les standards du marché, associées à ses gammes historiques de feutres, bandes et joints haute température de 200 à 1000 °C.

**Une solution à chaque poste de votre ligne, de la presse à l'emballage :**
- Gamme PBO Marathon — hot-end, au plus près de la presse (jusqu'à 600 °C)
- Bandes sans fin Marathon — PBO ou aramide, tissage haute densité, tables de sortie, zéro marquage
- FerlaBelt 600 — bande multicouche inox + aramide régénéré, stabilité dimensionnelle (jusqu'à 1400 °C inox)
- FerlaTape Contact — habillage des rouleaux de transport, évite marques et défauts de convoyage
- FerlaFelt Préox / SS — feutres découpés sur mesure pour barres de transfert et zones de refroidissement

**Vous utilisiez les solutions de Marathon Belting Ltd ? Votre référence Marathon existe toujours.** Depuis l'acquisition des machines haute température de Marathon Belting (janvier 2025), la technologie, la recette et la qualité de la marque britannique perdurent dans les ateliers Ferlam à Roubaix.

**L'alliance de deux savoir-faire** : +50 ans d'expertise thermique Ferlam (PBO, para-aramide, préox) × la technologie de tissage Marathon. Fabrication 100 % française, 600 références, 300 clients. Chaque référence est fabriquée sur mesure : largeur, longueur, épaisseur et fibre adaptées à votre ligne.

**Votre contact : Sébastien Paillet, Managing Director — paillet@ferlam-technologies.com — Ferlam Technologies, 85 rue Monge, 59100 Roubaix — +33 (0)3 20 65 96 96**"""


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
    return f"""# Marathon by Ferlam — Brief de rencontre : {p['name']}
Solutions textiles haute température pour l'extrusion d'aluminium · {p.get('city') or ''} · priorité : {p.get('gtm_priority') or 'watch'}
---
# Pourquoi maintenant — leur projet
{signal}
C'est la fenêtre : les décisions autour de ce projet se prennent maintenant. Arriver avec ce contexte, c'est la différence entre un appel fournisseur et une conversation d'égal à égal.
---
# Qui vous rencontrez
{who}
---
# L'offre Marathon by Ferlam, mappée sur leur ligne
{OFFER}
---
# Angles de conversation
- Ouvrir sur LEUR projet (l'investissement ci-dessus), pas sur nous, dans la première minute.
- Si leur ligne utilisait des références Marathon Belting : elles existent toujours, fabriquées à Roubaix.
- Marché fini : l'objectif du rendez-vous est la relation, pas le closing.
- Next step à proposer : envoi des caractéristiques de leur ligne au bureau d'études, ou visite de site calée sur leur calendrier projet.
---
# À propos de ce document
Généré par le GTM engine depuis les données CRM live (signal daté, contacts, preuves). Copy produit : brochure Marathon by Ferlam (source ferlam-technologies.fr). Aucune spec inventée.
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
                              "additionalInstructions": "Brand: Marathon by Ferlam. Colors: orange #f7941d as primary accent, red #d93a26 sparingly, dark #24282e for headings, light background. Industrial textile/aluminium-extrusion imagery only (conveyor belts, extrusion lines, technical weaving). French language. Keep every product name, temperature spec, name and figure EXACTLY as written."})
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
