"""Request and response models of the status callback an engine calls (D60; these produce the OpenAPI schema).

The endpoint takes exactly one request object, never separate arguments (DESIGN.md, D37)."""

from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import Body, Path
from pydantic import BaseModel, ConfigDict, Field

ReportedStatus = Literal["started", "completed", "failed"]


class WfExecStatusReport(BaseModel):
    """The body: what the engine reports. engine_run_id and message go to the execution; the volume fields go to its
    MIO ingest row and are ignored when it has none. Optional invoked_configs / invoked_info append to
    wf_engine_data_json only when at least one is non-null (M57-0001). Unknown fields are refused."""

    model_config = ConfigDict(extra="forbid")

    status: ReportedStatus
    engine_run_id: str | None = Field(default=None, max_length=128)
    message: str | None = None
    rows_loaded: int | None = Field(default=None, ge=0, strict=True)
    batch_count: int | None = Field(default=None, ge=0, strict=True)
    increment_marker: str | None = Field(default=None, max_length=255)
    invoked_configs: dict[str, Any] | None = None
    invoked_info: dict[str, Any] | None = None


class WfExecStatusReportReq(BaseModel):
    """The execution id in the path plus the report in the body."""

    execution_id: Annotated[str, Path()]
    body: Annotated[WfExecStatusReport, Body()]


class AppWfExecLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    engine_run_id: str | None = None
    status: str
    message: str | None = None
    mios_ingest_log_id: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    wf_engine_data_json: dict[str, Any] | None = None
    wf_exec_data_json: dict[str, Any] | None = None


class MioIngestLogOut(BaseModel):
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


class WfExecStatusOut(BaseModel):
    """The execution and its MIO ingest row (null when it has none) after the call."""

    execution: AppWfExecLogOut
    ingest: MioIngestLogOut | None = None
