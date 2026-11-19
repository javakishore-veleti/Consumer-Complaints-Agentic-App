"""Mode 2 rules classifier helpers (M47-0001 / #325)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

MONEY_TOPICS = [
    "Auto Loans",
    "Bank Accounts & Services",
    "Credit Cards",
    "Credit Reports & Scores",
    "Debt Collection",
    "Fraud & Scams",
    "Money Transfers",
    "Mortgages",
    "Payday Loans",
    "Prepaid Cards",
    "Private Student Loans",
    "Reverse Mortgages",
]

FRAUD_RE = re.compile(
    r"fraud|scam|phish|unauthorized|identity.?theft|impersonat|spoof",
    re.I,
)
TRANSFER_RE = re.compile(
    r"\bwire\b|money.?transfer|remittance|zelle|venmo|cash.?app|wallet|virtual.?currency",
    re.I,
)


def _norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def registry_signature_id(
    product: object = "",
    sub_product: object = "",
    issue: object = "",
    sub_issue: object = "",
    tags: object = "",
) -> str:
    payload = "||".join(
        [
            _norm(product),
            _norm(sub_product),
            _norm(issue),
            _norm(sub_issue),
            _norm(tags),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def primary_topic_from_product(product: object, sub_product: object = "") -> str:
    p = (product or "").strip()
    sp = (sub_product or "").strip()
    pl = p.lower()
    spl = sp.lower()

    if "vehicle loan" in pl or "vehicle lease" in pl:
        return "Auto Loans"
    if "reverse mortgage" in spl:
        return "Reverse Mortgages"
    if pl.startswith("mortgage") or pl == "Mortgage" or "mortgage" in pl:
        return "Mortgages"
    if "credit card" in pl and "prepaid" not in pl:
        return "Credit Cards"
    if "prepaid" in pl:
        return "Prepaid Cards"
    if "payday" in pl or "title loan" in pl or "personal loan" in pl or "advance loan" in pl:
        return "Payday Loans"
    if "student loan" in pl:
        return "Private Student Loans"
    if "debt collection" in pl:
        return "Debt Collection"
    if "credit reporting" in pl or "personal consumer report" in pl:
        return "Credit Reports & Scores"
    if "money transfer" in pl or "virtual currency" in pl or "money service" in pl:
        return "Money Transfers"
    if "checking" in pl or "savings" in pl:
        return "Bank Accounts & Services"
    if "debt or credit management" in pl:
        if "credit repair" in spl:
            return "Credit Reports & Scores"
        if "student loan" in spl:
            return "Private Student Loans"
        if "mortgage" in spl or "foreclosure" in spl:
            return "Mortgages"
        return "Payday Loans"
    return "Credit Reports & Scores"  # conservative default for unknown bundling


def classify_signature(
    product: object,
    sub_product: object = "",
    issue: object = "",
    sub_issue: object = "",
    tags: object = "",
) -> dict[str, Any]:
    primary = primary_topic_from_product(product, sub_product)
    blob = " ".join([str(x or "") for x in (issue, sub_issue, tags, product, sub_product)])
    is_fraud = bool(FRAUD_RE.search(blob))
    is_xfer = bool(TRANSFER_RE.search(blob))
    secondary = None
    if is_fraud and primary != "Fraud & Scams":
        secondary = "Fraud & Scams"
    elif is_xfer and primary != "Money Transfers":
        secondary = "Money Transfers"
    confidence = "HIGH"
    if primary == "Credit Reports & Scores" and "credit reporting" not in (product or "").lower():
        confidence = "MEDIUM"
    if is_fraud or is_xfer:
        confidence = "MEDIUM"
    return {
        "signature_id": registry_signature_id(product, sub_product, issue, sub_issue, tags),
        "primary_money_topic": primary,
        "secondary_money_topic": secondary,
        "is_fraud_scam": is_fraud,
        "is_money_transfer": is_xfer,
        "confidence": confidence,
        "classifier_version": "mode2-rules-v1",
    }
