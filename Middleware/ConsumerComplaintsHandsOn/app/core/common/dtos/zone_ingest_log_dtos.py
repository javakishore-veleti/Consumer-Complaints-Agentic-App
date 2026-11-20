"""Ctx/Req/Resp for zone ingest_log_* tables (M55-0011 / #391)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx

ZONE_INGEST_LOG_ZONES = frozenset({"raw", "refined", "curated", "taxonomy", "chroma"})
ZONE_INGEST_LOG_STATUSES = frozenset({"pending", "in_progress", "done", "failed"})
ZONE_INGEST_LOG_DATA_TECHS = frozenset({"iceberg", "s3", "database"})
LIST_LIMIT_MAX = 30
CLAIM_LIMIT_MAX = 5


@dataclass
class ZoneIngestLogRecord:
    id: str
    zone: str
    partition_key: str
    data_tech: str
    source_end_point_id: str
    dest_end_point_id: str
    workflow_execution_id: str | None
    status: str
    status_on: datetime
    status_updated_on: datetime
    configs_json: str | None


@dataclass
class ZoneIngestLogReq:
    zone: str | None = None
    id: str | None = None
    partition_key: str | None = None
    data_tech: str | None = None
    source_end_point_id: str | None = None
    dest_end_point_id: str | None = None
    workflow_execution_id: str | None = None
    status: str | None = None
    configs_json: str | None = None
    status_updated_from: datetime | None = None
    status_updated_to: datetime | None = None
    limit: int | None = None
    offset: int | None = None
    claim_limit: int | None = None


@dataclass
class ZoneIngestLogResp:
    records: list[ZoneIngestLogRecord] = field(default_factory=list)


@dataclass
class ZoneIngestLogCtx(TransactionalCtx):
    req: ZoneIngestLogReq = field(default_factory=ZoneIngestLogReq)
    resp: ZoneIngestLogResp = field(default_factory=ZoneIngestLogResp)
