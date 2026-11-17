"""Ctx for DAG execution context lookup (ops config without DAG→Postgres)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DagContextReq:
    execution_id: str | None = None
    app_endpoint_name: str | None = None


@dataclass
class DagContextResp:
    code: int = 0
    config_used: dict[str, Any] | None = None
    dataset_locations: dict[str, Any] | None = None
    app_endpoint: dict[str, Any] | None = None


@dataclass
class DagContextCtx:
    req: DagContextReq = field(default_factory=DagContextReq)
    resp: DagContextResp = field(default_factory=DagContextResp)
