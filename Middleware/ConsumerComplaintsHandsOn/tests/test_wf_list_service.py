"""Every registered workflow without config (D66)."""

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListReq
from app.core.common.dtos.wf_list_facade_dtos import WfListFacadeCtx
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED = [
    "download_cfpb_all",
    "filter_cfpb_3_months",
    "index_cfpb_all",
    "index_cfpb_chroma",
    "index_cfpb_pgvector",
    "index_cfpb_redis",
    "ingest_cfpb_all",
    "ingest_cfpb_imports_wrapper",
]


def _list() -> WfListCtx:
    ctx = WfListCtx(req=WfListReq())
    ServicesObjectsFactory.get_wf_list_service().list(ctx)
    return ctx


def test_seeded_registry_lists_download_cfpb_all(data_dir):
    ctx = _list()
    assert ctx.resp.code == SUCCESS
    assert [e.workflow_name for e in ctx.resp.entries] == SEEDED
    assert all(not hasattr(e, "config") for e in ctx.resp.entries)


def test_lists_every_workflow_ordered_by_name_without_config(data_dir):
    for name, enabled in (("t_b", True), ("t_a", False), ("t_c", True)):
        ctx = AppWfCtx(
            req=AppWfReq(
                workflow_name=name,
                engine_type="apache_airflow",
                engine_workflow_id=f"dag_{name}",
                enabled=enabled,
                config={"secretish": "nope"},
            )
        )
        assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS

    ctx = _list()
    assert ctx.resp.code == SUCCESS
    assert [e.workflow_name for e in ctx.resp.entries] == [*SEEDED, "t_a", "t_b", "t_c"]
    by_name = {e.workflow_name: e for e in ctx.resp.entries}
    assert [by_name[n].enabled for n in ("t_a", "t_b", "t_c")] == [False, True, True]
    assert all(e.engine_type == "apache_airflow" for e in ctx.resp.entries)
    assert [by_name[n].engine_workflow_id for n in ("t_a", "t_b", "t_c")] == [
        "dag_t_a",
        "dag_t_b",
        "dag_t_c",
    ]
    assert all(not hasattr(e, "config") for e in ctx.resp.entries)
    assert all(e.id for e in ctx.resp.entries)


def test_facade_hands_the_list_on(data_dir):
    made = AppWfCtx(
        req=AppWfReq(workflow_name="t_facade", engine_type="apache_airflow", engine_workflow_id="d")
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    ctx = WfListFacadeCtx(req=WfListReq())
    assert FacadesObjectsFactory.get_wf_list_facade().list(ctx) == SUCCESS
    assert [e.workflow_name for e in ctx.resp.entries] == [*SEEDED, "t_facade"]
