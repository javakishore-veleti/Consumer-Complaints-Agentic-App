"""Request and response bodies of the data ingest log endpoints (these produce the OpenAPI schema)."""

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
