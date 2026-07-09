"""FullEnrich v2 wrapper — tested live 09/07 (key valid, 2,505 credits).

Usage:
    python -m backend.enrich.fullenrich verify
    python -m backend.enrich.fullenrich credits
    python -m backend.enrich.fullenrich test                # zero-credit wiring test
    python -m backend.enrich.fullenrich enrich '<json array of contacts>'
    python -m backend.enrich.fullenrich result <enrichment_id>

Contact shape: {"first_name","last_name","domain","company_name","linkedin_url",
                "enrich_fields":["contact.work_emails","contact.phones"]}
Credits: work email=1, phone=10, personal email=3, search=0.25/result.
Only charged on found results. Enrich emails by default; phones only on hot accounts.
Docs: https://docs.fullenrich.com/llms.txt (append .md to any docs URL for clean markdown)
"""

import json
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE = "https://app.fullenrich.com/api/v2"

TEST_CONTACT = {
    "first_name": "Grégoire",
    "last_name": "Démogé",
    "domain": "fullenrich.com",
    "company_name": "FullEnrich",
    "linkedin_url": "https://www.linkedin.com/in/demoge/",
    "enrich_fields": ["contact.work_emails"],
}


def _headers() -> dict:
    key = os.environ.get("FULLENRICH_API_KEY")
    if not key:
        sys.exit("FULLENRICH_API_KEY not set (.env)")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def call(method: str, path: str, body=None) -> dict:
    r = httpx.request(method, BASE + path, headers=_headers(), json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def verify() -> dict:
    return call("GET", "/account/keys/verify")


def credits() -> dict:
    return call("GET", "/account/credits")


def enrich(contacts: list[dict], name: str = "agentic-gtm batch") -> dict:
    """Start a bulk enrichment (<=100 contacts). Returns {"enrichment_id": ...}."""
    return call("POST", "/contact/enrich/bulk", {"name": name, "data": contacts})


def result(enrichment_id: str) -> dict:
    """Poll a bulk enrichment result. status FINISHED when done."""
    return call("GET", f"/contact/enrich/bulk/{enrichment_id}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "verify":
        out = verify()
    elif cmd == "credits":
        out = credits()
    elif cmd == "test":
        out = enrich([TEST_CONTACT], name="wiring test (0 credits)")
    elif cmd == "enrich":
        out = enrich(json.loads(sys.argv[2]))
    elif cmd == "result":
        out = result(sys.argv[2])
    else:
        sys.exit(__doc__)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
