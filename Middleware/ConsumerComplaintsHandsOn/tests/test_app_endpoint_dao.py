"""DAO tests for app_endpoints (D85 / M04 #155)."""

from app.core.common.dtos.app_endpoint_dtos import AppEndpointCtx, AppEndpointReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

HTTP_LOCATION_ID = "776fc47e-efe7-59e6-b213-549261919d79"
LOCAL_LOCATION_ID = "2fc79860-7a4a-58b0-a0eb-45f994cfbace"
SEEDED_ID = "ccbce57d-bd9f-56fe-a258-fa2deb9dd393"


def _ctx(**fields) -> AppEndpointCtx:
    return AppEndpointCtx(req=AppEndpointReq(**fields))


def test_seed_source_endpoint_exists(data_dir):
    dao = DaoObjectsFactory.get_app_endpoint_dao()
    ctx = _ctx(id=SEEDED_ID)
    assert dao.get(ctx) == SUCCESS
    row = ctx.resp.records[0]
    assert row.name == "cfpb_source_http_to_local"
    assert row.category == "source"
    assert row.from_dataset_location_id == HTTP_LOCATION_ID
    assert row.to_dataset_location_id == LOCAL_LOCATION_ID
    assert row.from_env_var_name is None and row.to_env_var_name is None
    assert row.enabled is True


def test_create_list_update_delete(data_dir):
    dao = DaoObjectsFactory.get_app_endpoint_dao()
    created = _ctx(
        name="test_ingest_local_to_env",
        category="ingest",
        from_dataset_location_id=LOCAL_LOCATION_ID,
        to_env_var_name="CCA_MONGO_OPERATIONAL_URL",
        description="test",
    )
    assert dao.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.id and row.enabled is True

    listed = _ctx(category="ingest")
    assert dao.list(listed) == SUCCESS
    assert any(r.id == row.id for r in listed.resp.records)

    updated = _ctx(id=row.id, description="moved", enabled=False)
    assert dao.update(updated) == SUCCESS
    assert updated.resp.records[0].description == "moved"
    assert updated.resp.records[0].enabled is False

    deleted = _ctx(id=row.id)
    assert dao.delete(deleted) == SUCCESS
    assert dao.get(_ctx(id=row.id)) == NOT_FOUND


def test_invalid_category_and_xor(data_dir):
    dao = DaoObjectsFactory.get_app_endpoint_dao()
    assert (
        dao.create(
            _ctx(
                name="bad_cat",
                category="cloud",
                from_dataset_location_id=HTTP_LOCATION_ID,
                to_dataset_location_id=LOCAL_LOCATION_ID,
            )
        )
        == INVALID_INPUT
    )
    assert (
        dao.create(
            _ctx(
                name="both_from",
                category="source",
                from_dataset_location_id=HTTP_LOCATION_ID,
                from_env_var_name="X",
                to_dataset_location_id=LOCAL_LOCATION_ID,
            )
        )
        == INVALID_INPUT
    )
    assert (
        dao.create(
            _ctx(
                name="missing_to",
                category="source",
                from_dataset_location_id=HTTP_LOCATION_ID,
            )
        )
        == INVALID_INPUT
    )


def test_unknown_location_and_duplicate_name(data_dir):
    dao = DaoObjectsFactory.get_app_endpoint_dao()
    assert (
        dao.create(
            _ctx(
                name="missing_loc",
                category="source",
                from_dataset_location_id="00000000-0000-0000-0000-000000000000",
                to_dataset_location_id=LOCAL_LOCATION_ID,
            )
        )
        == NOT_FOUND
    )
    assert (
        dao.create(
            _ctx(
                name="cfpb_source_http_to_local",
                category="source",
                from_dataset_location_id=HTTP_LOCATION_ID,
                to_dataset_location_id=LOCAL_LOCATION_ID,
            )
        )
        == CONFLICT
    )
