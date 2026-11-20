"""Request/response models for /ingestion-logs/{zone} (M55-0011 / #391)."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import Body, Path, Query
from pydantic import BaseModel, ConfigDict, Field

ZoneName = Literal["raw", "refined", "curated", "taxonomy", "chroma"]


class ZoneIngestLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ZoneIngestLogCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    partition_key: str
    data_tech: Literal["iceberg", "s3", "database"]
    source_end_point_id: str
    dest_end_point_id: str
    workflow_execution_id: str | None = None
    configs_json: str | None = None


class ZoneIngestLogUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    partition_key: str | None = None
    data_tech: Literal["iceberg", "s3", "database"] | None = None
    source_end_point_id: str | None = None
    dest_end_point_id: str | None = None
    workflow_execution_id: str | None = None
    status: Literal["pending", "in_progress", "done", "failed"] | None = None
    configs_json: str | None = None


class ZoneIngestLogClaimBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=5, ge=1, le=5)


class ZoneIngestLogCompleteBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["done", "failed"]
    configs_json: str | None = None


class ZoneIngestLogListHttpReq(BaseModel):
    zone: Annotated[ZoneName, Path()]
    limit: Annotated[int | None, Query(ge=0, le=30)] = 30
    offset: Annotated[int | None, Query(ge=0)] = 0
    status: Annotated[str | None, Query()] = None
    partition_key: Annotated[str | None, Query()] = None
    workflow_execution_id: Annotated[str | None, Query()] = None
    status_updated_from: Annotated[datetime | None, Query()] = None
    status_updated_to: Annotated[datetime | None, Query()] = None


class ZoneIngestLogCreateHttpReq(BaseModel):
    zone: Annotated[ZoneName, Path()]
    body: Annotated[ZoneIngestLogCreateBody, Body()]


class ZoneIngestLogIdHttpReq(BaseModel):
    zone: Annotated[ZoneName, Path()]
    id: Annotated[str, Path()]


class ZoneIngestLogUpdateHttpReq(BaseModel):
    zone: Annotated[ZoneName, Path()]
    id: Annotated[str, Path()]
    body: Annotated[ZoneIngestLogUpdateBody, Body()]


class ZoneIngestLogClaimHttpReq(BaseModel):
    zone: Annotated[ZoneName, Path()]
    body: Annotated[ZoneIngestLogClaimBody, Body()]


class ZoneIngestLogCompleteHttpReq(BaseModel):
    zone: Annotated[ZoneName, Path()]
    id: Annotated[str, Path()]
    body: Annotated[ZoneIngestLogCompleteBody, Body()]
