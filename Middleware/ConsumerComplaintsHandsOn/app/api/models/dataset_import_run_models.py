"""HTTP models for dataset import runs (M11)."""

from datetime import datetime
from typing import Annotated

from fastapi import Body, Path, Query
from pydantic import BaseModel, ConfigDict


class DatasetImportRunCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    run_folder_name: str
    location_kind: str
    location_ref: str
    source_snapshot_start: datetime
    source_snapshot_end: datetime
    workflow_started_at: datetime
    status: str | None = None
    execution_id: str | None = None
    mio_id: str | None = None
    part_count: int | None = None
    message: str | None = None


class DatasetImportRunUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    workflow_completed_at: datetime | None = None
    ingested_at: datetime | None = None
    part_count: int | None = None
    message: str | None = None
    execution_id: str | None = None


class DatasetImportRunCreateReq(BaseModel):
    body: Annotated[DatasetImportRunCreateBody, Body()]


class DatasetImportRunUpdateReq(BaseModel):
    import_id: Annotated[str, Path()]
    body: Annotated[DatasetImportRunUpdateBody, Body()]


class DatasetImportRunListReq(BaseModel):
    eligible_only: Annotated[bool | None, Query()] = None
    status: Annotated[str | None, Query()] = None
    limit: Annotated[int | None, Query(ge=0)] = None
    offset: Annotated[int | None, Query(ge=0)] = None


class DatasetImportRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_folder_name: str
    location_kind: str
    location_ref: str
    source_snapshot_start: datetime
    source_snapshot_end: datetime
    status: str
    workflow_started_at: datetime
    workflow_completed_at: datetime | None = None
    ingested_at: datetime | None = None
    mio_id: str | None = None
    execution_id: str | None = None
    part_count: int | None = None
    message: str | None = None
    created_at: datetime
    updated_at: datetime
