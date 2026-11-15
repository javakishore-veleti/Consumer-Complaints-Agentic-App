"""Maps AppEndpointDao rows to portal-safe entries (#156)."""

from app.core.common.dtos.app_endpoint_dtos import AppEndpointCtx, AppEndpointRecord, AppEndpointReq
from app.core.common.dtos.app_endpoint_list_dtos import AppEndpointEntry, AppEndpointListCtx
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.app_endpoint_list_service import AppEndpointListService


def _entry(r: AppEndpointRecord) -> AppEndpointEntry:
    return AppEndpointEntry(
        id=r.id,
        name=r.name,
        category=r.category,
        from_dataset_location_id=r.from_dataset_location_id,
        from_env_var_name=r.from_env_var_name,
        to_dataset_location_id=r.to_dataset_location_id,
        to_env_var_name=r.to_env_var_name,
        credentials_ref=r.credentials_ref,
        description=r.description,
        enabled=r.enabled,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


class AppEndpointListServiceImpl(AppEndpointListService):
    def list(self, ctx: AppEndpointListCtx) -> int:
        dao_ctx = AppEndpointCtx(
            req=AppEndpointReq(category=ctx.req.category, enabled=ctx.req.enabled, name=ctx.req.name)
        )
        code = DaoObjectsFactory.get_app_endpoint_dao().list(dao_ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        ctx.resp.entries = [_entry(r) for r in dao_ctx.resp.records]
        ctx.resp.code = SUCCESS
        return SUCCESS

    def get(self, ctx: AppEndpointListCtx) -> int:
        dao_ctx = AppEndpointCtx(req=AppEndpointReq(id=ctx.req.id))
        code = DaoObjectsFactory.get_app_endpoint_dao().get(dao_ctx)
        if code != SUCCESS:
            ctx.resp.code = code
            return code
        ctx.resp.entries = [_entry(r) for r in dao_ctx.resp.records]
        ctx.resp.code = SUCCESS
        return SUCCESS
