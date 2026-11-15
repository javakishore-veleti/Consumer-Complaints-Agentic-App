"""Request and response models of GET /workflows (D66)."""

from pydantic import BaseModel, ConfigDict


class WfListReq(BaseModel):
    """No query fields for MVP."""


class WfListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_name: str
    engine_type: str
    engine_workflow_id: str
    enabled: bool
