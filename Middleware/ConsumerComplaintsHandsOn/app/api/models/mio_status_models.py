"""Request and response models of GET /mios/status (D61; these produce the OpenAPI schema).

The endpoint takes exactly one request object, never separate arguments (DESIGN.md, D37)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.api.models.wf_exec_callback_models import AppWfExecLogOut


class MioStatusListReq(BaseModel):
    """Optional query: mio_id selects one MIO."""

    mio_id: str | None = None


class MioStatusIngestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mio_id: str
    status: str
    message: str | None = None
    rows_loaded: int | None = None
    batch_count: int | None = None
    increment_marker: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    executions: list[AppWfExecLogOut] = []


class MioStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    latest_ingest: MioStatusIngestOut | None = None
