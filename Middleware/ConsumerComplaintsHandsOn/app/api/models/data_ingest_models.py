"""Request and response models of the data ingest log endpoints (these produce the OpenAPI schema).

Every endpoint method takes exactly one of these request objects, never separate arguments (DESIGN.md, D37)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Status = Literal["requested", "started", "completed", "failed"]


class DataIngestLogCreate(BaseModel):
    purpose: str
    status: Status | None = None
    run_id: str | None = None
    message: str | None = None


class DataIngestLogUpdate(BaseModel):
    status: Status | None = None
    run_id: str | None = None
    message: str | None = None


class DataIngestLogIdReq(BaseModel):
    """The id in the path of get and delete."""

    log_id: str


class DataIngestLogUpdateReq(BaseModel):
    """The id in the path plus the changes in the body of update."""

    log_id: str
    body: DataIngestLogUpdate


class DataIngestLogListReq(BaseModel):
    """The filters and paging in the query string of list."""

    purpose: str | None = None
    status: Status | None = None
    limit: int | None = None
    offset: int | None = None


class DataIngestLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    purpose: str
    status: str
    run_id: str | None = None
    message: str | None = None
    requested_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
