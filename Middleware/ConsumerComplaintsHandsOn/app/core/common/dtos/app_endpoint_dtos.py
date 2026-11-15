"""Ctx, Req and Resp for the app_endpoints table (D85)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class AppEndpointRecord:
    id: str
    name: str
    category: str
    from_dataset_location_id: str | None
    from_env_var_name: str | None
    to_dataset_location_id: str | None
    to_env_var_name: str | None
    credentials_ref: str | None
    description: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class AppEndpointReq:
    """A field left as None means "not given". id identifies one row (get, update, delete)."""

    id: str | None = None
    name: str | None = None
    category: str | None = None
    from_dataset_location_id: str | None = None
    from_env_var_name: str | None = None
    to_dataset_location_id: str | None = None
    to_env_var_name: str | None = None
    credentials_ref: str | None = None
    description: str | None = None
    enabled: bool | None = None


@dataclass
class AppEndpointResp:
    records: list[AppEndpointRecord] = field(default_factory=list)


@dataclass
class AppEndpointCtx(TransactionalCtx):
    req: AppEndpointReq = field(default_factory=AppEndpointReq)
    resp: AppEndpointResp = field(default_factory=AppEndpointResp)
