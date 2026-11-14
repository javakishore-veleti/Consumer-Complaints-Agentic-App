"""Download a stratified sample of complaints from the CFPB public API.

The database is 88% credit-reporting complaints, so a plain "newest N" sample would make every question look
alike. We sample per (month, product) cell instead, and a random page inside each cell.

The API has no narrative text (the `Consumer complaint narrative` column is not in the database any more), only
the structured fields from the field reference. We keep them all.
"""
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import httpx

from .config import COMPLAINTS_PATH, DATA_DIR

API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
MAX_WINDOW = 10_000  # Elasticsearch: frm + size must stay under this


def _none(value):
    return None if value in (None, "", "None", "N/A") else value


def normalise(hit: dict) -> dict:
    s = hit["_source"]
    tags = _none(s.get("tags"))
    return {
        "complaint_id": str(s["complaint_id"]),
        "date_received": s["date_received"][:10],
        "date_sent_to_company": (s.get("date_sent_to_company") or "")[:10] or None,
        "product": _none(s.get("product")),
        "sub_product": _none(s.get("sub_product")),
        "issue": _none(s.get("issue")),
        "sub_issue": _none(s.get("sub_issue")),
        "company": _none(s.get("company")),
        "company_public_response": _none(s.get("company_public_response")),
        "company_response": _none(s.get("company_response")),
        "state": _none(s.get("state")),
        "zip_code": _none(s.get("zip_code")),
        "tags": tags,
        "submitted_via": _none(s.get("submitted_via")),
        "timely": {"Yes": True, "No": False}.get(s.get("timely")),
    }


def month_windows(n_months: int, today: date | None = None) -> list[tuple[date, date]]:
    """The last `n_months` calendar months, newest first, not counting the month in progress."""
    today = today or date.today()
    first = today.replace(day=1)
    out = []
    for _ in range(n_months):
        last = first - timedelta(days=1)
        first = last.replace(day=1)
        out.append((first, last))
    return out


def _get(client: httpx.Client, params: dict, tries: int = 5) -> dict:
    for attempt in range(tries):
        try:
            r = client.get(API, params=params)
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, ValueError):
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


def top_products(client: httpx.Client, n: int, start: date, end: date) -> list[str]:
    data = _get(client, {"size": 0, "date_received_min": start, "date_received_max": end})
    return [b["key"] for b in data["aggregations"]["product"]["product"]["buckets"][:n]]


def fetch_cell(client: httpx.Client, product: str, start: date, end: date, n: int, seed: int) -> list[dict]:
    base = {"product": product, "date_received_min": start, "date_received_max": end,
            "no_aggs": "true", "sort": "created_date_desc"}
    total = _get(client, {**base, "size": 0})["hits"]["total"]["value"]
    if total == 0:
        return []
    top = max(0, min(total, MAX_WINDOW) - n)
    frm = random.Random(seed).randint(0, top)
    hits = _get(client, {**base, "size": n, "frm": frm})["hits"]["hits"]
    return [normalise(h) for h in hits]


def ingest(months: int = 24, products: int = 8, per_cell: int = 12, seed: int = 7, workers: int = 4) -> int:
    """Write `data/complaints.jsonl`. About months * products * per_cell records (2,304 by default)."""
    DATA_DIR.mkdir(exist_ok=True)
    windows = month_windows(months)
    with httpx.Client(timeout=60, headers={"User-Agent": "ccrag-learning-project"}) as client:
        names = top_products(client, products, windows[-1][0], windows[0][1])
        cells = [(p, s, e) for (s, e) in windows for p in names]
        print(f"{len(cells)} cells: {len(names)} products x {len(windows)} months, {per_cell} complaints each")
        with ThreadPoolExecutor(workers) as pool:
            batches = list(pool.map(lambda ic: fetch_cell(client, *ic[1], per_cell, seed + ic[0]), enumerate(cells)))
    records = {r["complaint_id"]: r for batch in batches for r in batch}
    with COMPLAINTS_PATH.open("w", encoding="utf-8") as f:
        for r in sorted(records.values(), key=lambda r: r["complaint_id"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} complaints to {COMPLAINTS_PATH}")
    return len(records)


def load_complaints() -> list[dict]:
    if not COMPLAINTS_PATH.exists():
        raise FileNotFoundError(f"{COMPLAINTS_PATH} not found. Run: ccrag ingest")
    return [json.loads(line) for line in COMPLAINTS_PATH.read_text(encoding="utf-8").splitlines()]
