"""Deterministic signature_id + ZIP-3 helpers (M46-0001 / #324)."""

from __future__ import annotations

import hashlib
import re

SIGNATURE_FIELDS = (
    "product",
    "sub_product",
    "issue",
    "sub_issue",
    "tags",
    "company_response_to_consumer",
)


def _norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def signature_id_from_fields(
    product: object = "",
    sub_product: object = "",
    issue: object = "",
    sub_issue: object = "",
    tags: object = "",
    company_response_to_consumer: object = "",
) -> str:
    parts = [
        _norm(product),
        _norm(sub_product),
        _norm(issue),
        _norm(sub_issue),
        _norm(tags),
        _norm(company_response_to_consumer),
    ]
    payload = "||".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def zip3_from_zip_code(zip_code: object) -> str:
    if zip_code is None:
        return "UNK"
    digits = re.sub(r"\D", "", str(zip_code))
    if len(digits) < 3:
        return "UNK"
    return digits[:3]
