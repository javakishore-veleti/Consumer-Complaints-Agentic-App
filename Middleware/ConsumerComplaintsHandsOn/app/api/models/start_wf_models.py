"""Request and response models of POST /workflows/{workflow_id}/start (D68 / D89).

Every endpoint method takes exactly one request object, never separate arguments (DESIGN.md, D37)."""

from typing import Annotated

from fastapi import Body, Header, Path
from pydantic import BaseModel, ConfigDict


class StartWfBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mio_id: str | None = None
    dataset_location_id: str | None = None
    import_ids: list[str] | None = None
    mode: str | None = None
    source_snapshot_start: str | None = None
    source_snapshot_end: str | None = None


class StartWfReq(BaseModel):
    """The workflow id in the path, optional body fields, and ACL audience header (D89)."""

    workflow_id: Annotated[str, Path()]
    body: Annotated[StartWfBody, Body()] = StartWfBody()
    audience: Annotated[str, Header(alias="X-CCA-Audience")] = "internal"


class StartWfOut(BaseModel):
    execution_id: str
