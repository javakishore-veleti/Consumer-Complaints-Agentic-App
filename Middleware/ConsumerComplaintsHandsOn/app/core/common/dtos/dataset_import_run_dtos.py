"""Ctx for dataset_import_runs registry (M11)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx

STATUS_LANDED = "landed"
STATUS_INGESTING = "ingesting"
STATUS_INGESTED = "ingested"
STATUS_FAILED = "failed"
STATUS_STAGING = "staging"

LOCATION_LOCAL_PATH = "local_path"

ELIGIBLE_FOR_INGEST = frozenset({STATUS_LANDED, STATUS_FAILED})


@dataclass
class DatasetImportRunRecord:
    id: str
    run_folder_name: str
    location_kind: str
    location_ref: str
    source_snapshot_start: datetime
    source_snapshot_end: datetime
    status: str
    workflow_started_at: datetime
    workflow_completed_at: datetime | None
    ingested_at: datetime | None
    mio_id: str | None
    execution_id: str | None
    part_count: int | None
    message: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetImportRunReq:
    id: str | None = None
    run_folder_name: str | None = None
    location_kind: str | None = None
    location_ref: str | None = None
    source_snapshot_start: datetime | None = None
    source_snapshot_end: datetime | None = None
    status: str | None = None
    workflow_started_at: datetime | None = None
    workflow_completed_at: datetime | None = None
    ingested_at: datetime | None = None
    mio_id: str | None = None
    execution_id: str | None = None
    part_count: int | None = None
    message: str | None = None
    eligible_only: bool | None = None
    limit: int | None = None
    offset: int | None = None
    ids: list[str] | None = None


@dataclass
class DatasetImportRunResp:
    records: list[DatasetImportRunRecord] = field(default_factory=list)
    code: int = 0


@dataclass
class DatasetImportRunCtx(TransactionalCtx):
    req: DatasetImportRunReq = field(default_factory=DatasetImportRunReq)
    resp: DatasetImportRunResp = field(default_factory=DatasetImportRunResp)
