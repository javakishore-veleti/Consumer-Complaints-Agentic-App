"""Chroma catalog docs from semantic_signatures (shared with M49 iceberg scripts)."""

from __future__ import annotations

from typing import Any, Mapping

COLLECTION_NAME = "cfpb_semantic_signatures"


def signature_catalog_text(row: Mapping[str, Any]) -> str:
    parts = [
        str(row.get("product") or ""),
        str(row.get("sub_product") or ""),
        str(row.get("issue") or ""),
        str(row.get("sub_issue") or ""),
        str(row.get("tags") or ""),
        str(row.get("primary_money_topic") or ""),
    ]
    return " | ".join(p for p in parts if p.strip())


def signature_catalog_metadata(row: Mapping[str, Any]) -> dict[str, str | bool]:
    return {
        "signature_id": str(row.get("signature_id") or ""),
        "primary_money_topic": str(row.get("primary_money_topic") or ""),
        "secondary_money_topic": str(row.get("secondary_money_topic") or ""),
        "product": str(row.get("product") or ""),
        "is_fraud_scam": bool(row.get("is_fraud_scam") or False),
        "is_money_transfer": bool(row.get("is_money_transfer") or False),
    }


def signature_to_catalog_doc(
    row: Mapping[str, Any],
    *,
    hash_embedding,
    dim: int = 32,
) -> dict[str, Any]:
    sid = str(row.get("signature_id") or "").strip()
    if not sid:
        raise ValueError("signature_id is required")
    text = signature_catalog_text(row)
    return {
        "id": sid,
        "text": text,
        "embedding": hash_embedding(text, dim=dim),
        "metadata": signature_catalog_metadata(row),
    }
