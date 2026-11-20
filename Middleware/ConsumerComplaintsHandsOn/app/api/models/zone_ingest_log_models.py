"""Request/response models for /ingestion-logs/{zone} (M55-0011 / #391)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ZoneIngestLogOut(BaseModel):
    id: str
    zone: str
    partition_key: str
    data_tech: str
    source_end_point_id: str
    dest_end_point_id: str
    workflow_execution_id: str | None = None
    status: str
    status_on: datetime
    status_updated_on: datetime
    configs_json: str | None = None


class ZoneIngestLogCreateIn(BaseModel):
    partition_key: str
    data_tech: Literal["iceberg", "s3", "database"]
    source_end_point_id: str
    dest_end_point_id: str
    workflow_execution_id: str | None = None
    configs_json: str | None = None


class ZoneIngestLogUpdateIn(BaseModel):
    partition_key: str | None = None
    data_tech: Literal["iceberg", "s3", "database"] | None = None
    source_end_point_id: str | None = None
    dest_end_point_id: str | None = None
    workflow_execution_id: str | None = None
    status: Literal["pending", "in_progress", "done", "failed"] | None = None
    configs_json: str | None = None


class ZoneIngestLogClaimIn(BaseModel):
    limit: int = Field(default=5, ge=1, le=5)


class ZoneIngestLogCompleteIn(BaseModel):
    status: Literal["done", "failed"]
    configs_json: str | None = None
