"""Build DAG context from ops DAOs (replaces Airflow CCA_DB_URL lookups)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.common.dtos.app_endpoint_dtos import AppEndpointCtx, AppEndpointReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.dag_context_dtos import DagContextCtx
from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.dag_context_service import DagContextService


@dataclass
class _EndpointSideReq:
    location_id: str | None = None
    env_var_name: str | None = None


def _side_from_endpoint(side: _EndpointSideReq) -> dict[str, Any]:
    if side.location_id and side.env_var_name:
        raise ValueError("side cannot set both location_id and env_var_name")
    if side.location_id:
        loc_ctx = DatasetLocationCtx(req=DatasetLocationReq(id=side.location_id))
        code = DaoObjectsFactory.get_dataset_location_dao().get(loc_ctx)
        if code != SUCCESS or not loc_ctx.resp.records:
            raise LookupError(f"datasets_location not found: {side.location_id}")
        loc = loc_ctx.resp.records[0]
        if loc.path:
            return {"kind": "path", "path": loc.path, "location_type": loc.location_type}
        if loc.local_env_var_name:
            return {
                "kind": "env",
                "env_var_name": loc.local_env_var_name,
                "location_type": loc.location_type,
            }
        raise ValueError(f"location {side.location_id} has neither path nor local_env_var_name")
    if side.env_var_name:
        return {"kind": "env", "env_var_name": side.env_var_name}
    raise ValueError("side requires location_id or env_var_name")


class DagContextServiceImpl(DagContextService):
    def get(self, ctx: DagContextCtx) -> int:
        execution_id = (ctx.req.execution_id or "").strip()
        if not execution_id:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT

        exec_ctx = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
        code = DaoObjectsFactory.get_app_wf_exec_log_dao().get(exec_ctx)
        if code != SUCCESS or not exec_ctx.resp.records:
            ctx.resp.code = NOT_FOUND if code == NOT_FOUND else code
            return ctx.resp.code

        raw = exec_ctx.resp.records[0].config_used
        if raw is None:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        config = dict(raw) if isinstance(raw, dict) else {}
        ctx.resp.config_used = config

        dataset_code = str(config.get("dataset_code") or "").strip()
        if dataset_code:
            ds_list = DatasetCtx(req=DatasetReq())
            list_code = DaoObjectsFactory.get_dataset_dao().list(ds_list)
            if list_code != SUCCESS:
                ctx.resp.code = list_code
                return list_code
            match = next((r for r in ds_list.resp.records if r.code == dataset_code), None)
            if match is None:
                ctx.resp.code = NOT_FOUND
                return NOT_FOUND
            loc_ctx = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=match.id))
            loc_code = DaoObjectsFactory.get_dataset_location_dao().list(loc_ctx)
            if loc_code != SUCCESS:
                ctx.resp.code = loc_code
                return loc_code
            out: dict[str, Any] = {}
            for loc in loc_ctx.resp.records:
                out[loc.location_type] = {
                    "path": loc.path,
                    "local_env_var_name": loc.local_env_var_name,
                }
            if "http" not in out or not out["http"].get("path"):
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT
            if "local" not in out or not out["local"].get("local_env_var_name"):
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT
            ctx.resp.dataset_locations = out

        ep_name = (ctx.req.app_endpoint_name or "").strip() or str(config.get("app_endpoint_name") or "").strip()
        if ep_name:
            ep_ctx = AppEndpointCtx(req=AppEndpointReq(name=ep_name))
            ep_code = DaoObjectsFactory.get_app_endpoint_dao().list(ep_ctx)
            if ep_code != SUCCESS:
                ctx.resp.code = ep_code
                return ep_code
            records = [r for r in ep_ctx.resp.records if r.name == ep_name]
            if not records:
                ctx.resp.code = NOT_FOUND
                return NOT_FOUND
            ep = records[0]
            if not ep.enabled:
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT
            try:
                frm = _side_from_endpoint(
                    _EndpointSideReq(
                        location_id=ep.from_dataset_location_id,
                        env_var_name=ep.from_env_var_name,
                    )
                )
                to = _side_from_endpoint(
                    _EndpointSideReq(
                        location_id=ep.to_dataset_location_id,
                        env_var_name=ep.to_env_var_name,
                    )
                )
            except LookupError:
                ctx.resp.code = NOT_FOUND
                return NOT_FOUND
            except ValueError:
                ctx.resp.code = INVALID_INPUT
                return INVALID_INPUT
            ctx.resp.app_endpoint = {
                "name": ep.name,
                "from": frm,
                "to": to,
                "endpoint": {
                    "id": ep.id,
                    "name": ep.name,
                    "category": ep.category,
                    "enabled": ep.enabled,
                },
            }

        ctx.resp.code = SUCCESS
        return SUCCESS
