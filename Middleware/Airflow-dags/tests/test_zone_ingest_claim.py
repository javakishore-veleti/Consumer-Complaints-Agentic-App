"""Unit tests for ccaa.zone_ingest_claim (M55-0011 / #391)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ccaa.zone_ingest_claim import CLAIM_LIMIT_MAX, claim_zone_partitions, partition_keys_from_claim


def test_partition_keys_from_claim():
    assert partition_keys_from_claim(
        [{"partition_key": "0"}, {"partition_key": "1"}, {"partition_key": None}]
    ) == ["0", "1"]


def test_claim_caps_limit_and_posts_json():
    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                [{"id": "a", "partition_key": "p0", "status": "in_progress"}]
            ).encode()

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode())
        captured["timeout"] = timeout
        return _Resp()

    with patch("ccaa.zone_ingest_claim.urllib.request.urlopen", side_effect=fake_urlopen):
        rows = claim_zone_partitions(api_base_url="http://api:8000", zone="curated", limit=99)

    assert captured["url"] == "http://api:8000/ingestion-logs/curated/claim"
    assert captured["body"] == {"limit": CLAIM_LIMIT_MAX}
    assert rows[0]["partition_key"] == "p0"
