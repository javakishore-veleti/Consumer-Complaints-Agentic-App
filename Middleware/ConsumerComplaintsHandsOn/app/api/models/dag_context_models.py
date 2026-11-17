from typing import Annotated, Any

from fastapi import Path, Query
from pydantic import BaseModel, Field


class DagContextGetReq(BaseModel):
    """Path execution_id plus optional app_endpoint query (D37: one request object)."""

    execution_id: Annotated[str, Path(min_length=1)]
    app_endpoint: Annotated[str | None, Query()] = None


class DagContextOut(BaseModel):
    execution_id: str
    config_used: dict[str, Any] = Field(default_factory=dict)
    dataset_locations: dict[str, Any] | None = None
    app_endpoint: dict[str, Any] | None = None
