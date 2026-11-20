"""HTTP models for GET /workflow-logs (M55-0012 / #394; M56-0001 / #396)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WorkflowLogCategory = Literal[
    "import", "db_ingest", "raw", "refined", "curated", "taxonomy", "chroma"
]


class WorkflowLogListHttpReq(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: WorkflowLogCategory | None = None
    status: str | None = None
    engine_type: str | None = Field(default=None, max_length=32)
    engine_run_id: str | None = Field(default=None, max_length=128)
    requested_after: datetime | None = None
    requested_before: datetime | None = None
    limit: int = Field(default=60, ge=1, le=60)
    offset: int = Field(default=0, ge=0)


class WorkflowLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    workflow_name: str
    engine_type: str
    engine_label: str
    engine_workflow_id: str
    engine_run_id: str | None = None
    status: str
    display_status: str
    message: str | None = None
    mios_ingest_log_id: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    wf_engine_data_json: dict | None = None
    wf_exec_data_json: dict | None = None
