"""Claim ≤5 pending zone ingest_log partitions via Middleware (M55-0011 / #391)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

CLAIM_LIMIT_MAX = 5


def claim_zone_partitions(
    *,
    api_base_url: str,
    zone: str,
    limit: int = CLAIM_LIMIT_MAX,
    timeout_s: float = 30.0,
) -> list[dict[str, Any]]:
    """POST /ingestion-logs/{zone}/claim — returns claimed rows (may be empty)."""
    capped = max(1, min(int(limit), CLAIM_LIMIT_MAX))
    url = f"{api_base_url.rstrip('/')}/ingestion-logs/{zone}/claim"
    body = json.dumps({"limit": capped}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"claim {zone} failed HTTP {exc.code}: {detail}") from exc
    if not isinstance(payload, list):
        raise RuntimeError(f"claim {zone} expected list, got {type(payload).__name__}")
    return payload


def partition_keys_from_claim(rows: list[dict[str, Any]]) -> list[str]:
    return [str(r["partition_key"]) for r in rows if r.get("partition_key") is not None]
