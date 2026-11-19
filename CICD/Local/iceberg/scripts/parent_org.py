"""Parent org normalization helpers (M48-0001 / #326)."""

from __future__ import annotations

import hashlib
import re

_PUNCT = re.compile(r"[^a-z0-9\s]+")
_SPACE = re.compile(r"\s+")

# Known alias → canonical display name (same parent_org_id).
ORG_ALIASES = {
    "capital one": "CAPITAL ONE FINANCIAL CORPORATION",
    "capital one financial corporation": "CAPITAL ONE FINANCIAL CORPORATION",
    "capital one bank": "CAPITAL ONE FINANCIAL CORPORATION",
    "capital one n a": "CAPITAL ONE FINANCIAL CORPORATION",
    "capital one na": "CAPITAL ONE FINANCIAL CORPORATION",
    "jpmorgan chase": "JPMORGAN CHASE & CO.",
    "jpmorgan chase co": "JPMORGAN CHASE & CO.",
    "chase bank": "JPMORGAN CHASE & CO.",
    "wells fargo": "WELLS FARGO & COMPANY",
    "wells fargo company": "WELLS FARGO & COMPANY",
    "equifax": "EQUIFAX, INC.",
    "equifax inc": "EQUIFAX, INC.",
}


def normalize_company_key(company: object) -> str:
    if company is None:
        return ""
    s = str(company).strip().lower()
    s = _PUNCT.sub(" ", s)
    s = _SPACE.sub(" ", s).strip()
    return s


def canonical_parent_org_name(company: object) -> str:
    key = normalize_company_key(company)
    if not key:
        return "UNKNOWN"
    if key in ORG_ALIASES:
        return ORG_ALIASES[key]
    # Title-ish keep original trimmed upper for unknown
    return str(company).strip() or "UNKNOWN"


def parent_org_id_from_company(company: object) -> str:
    name = canonical_parent_org_name(company)
    key = normalize_company_key(name)
    if not key:
        key = "unknown"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
