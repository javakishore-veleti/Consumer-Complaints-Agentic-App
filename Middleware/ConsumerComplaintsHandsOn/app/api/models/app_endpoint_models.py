"""Request/response models for GET /app-endpoints (#156)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppEndpointListQuery(BaseModel):
    category: str | None = None
    enabled: bool | None = None
    name: str | None = None


class AppEndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    from_dataset_location_id: str | None = None
    from_env_var_name: str | None = None
    to_dataset_location_id: str | None = None
    to_env_var_name: str | None = None
    credentials_ref: str | None = None
    description: str | None = None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class AppEndpointIdPath(BaseModel):
    """Path `{id}` for GET /app-endpoints/{id}."""

    id: str = Field(..., min_length=1, max_length=36)
