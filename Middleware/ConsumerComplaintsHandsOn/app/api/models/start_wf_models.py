"""Request and response models of POST /workflows/{workflow_id}/start (D68).

Every endpoint method takes exactly one request object, never separate arguments (DESIGN.md, D37)."""

from pydantic import BaseModel, ConfigDict


class StartWfBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mio_id: str | None = None
    dataset_location_id: str | None = None


class StartWfReq(BaseModel):
    """The workflow id in the path plus optional body fields."""

    workflow_id: str
    body: StartWfBody = StartWfBody()


class StartWfOut(BaseModel):
    execution_id: str
