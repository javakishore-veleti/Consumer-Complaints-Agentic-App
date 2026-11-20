from app.core.common.app_types_constants import (
    AppEndpointCategory,
    AppTypeEnum,
    DatasetLocationType,
    EngineType,
    ExecStatus,
    MioAudience,
)


def test_engine_type_values_are_the_short_codes():
    assert EngineType.values() == [
        "apache_airflow",
        "aws_step_functions",
        "spring_batch",
        "bpmn",
        "spark_job",
        "aws_emr",
    ]


def test_engine_type_members_are_plain_strings():
    assert EngineType.APACHE_AIRFLOW == "apache_airflow"
    assert "aws_step_functions" in EngineType.values()
    assert "spring_batch" in EngineType.values()
    assert "bogus" not in EngineType.values()


def test_the_parent_has_no_members_and_every_type_list_extends_it():
    assert list(AppTypeEnum) == []
    assert issubclass(EngineType, AppTypeEnum)


def test_exec_status_values_in_the_order_of_a_normal_run():
    assert ExecStatus.values() == ["requested", "started", "completed", "failed"]
    assert ExecStatus.STARTED == "started"
    assert issubclass(ExecStatus, AppTypeEnum)


def test_exec_status_allowed_moves_follow_d30():
    assert ExecStatus.REQUESTED.next_statuses == (ExecStatus.STARTED, ExecStatus.FAILED)
    assert ExecStatus.STARTED.next_statuses == (ExecStatus.COMPLETED, ExecStatus.FAILED)
    assert ExecStatus.COMPLETED.next_statuses == ()
    assert ExecStatus.FAILED.next_statuses == ()


def test_only_completed_and_failed_are_final():
    assert [s for s in ExecStatus if s.is_final] == [ExecStatus.COMPLETED, ExecStatus.FAILED]


def test_dataset_location_type_values_are_the_short_codes():
    assert DatasetLocationType.values() == [
        "local",
        "http",
        "github",
        "s3",
        "azure_blob",
        "gcs",
        "google_drive",
        "ftp",
    ]
    assert DatasetLocationType.LOCAL == "local"
    assert "dropbox" not in DatasetLocationType.values()
    assert issubclass(DatasetLocationType, AppTypeEnum)


def test_app_endpoint_category_values():
    assert AppEndpointCategory.values() == ["source", "ingest", "index", "db"]
    assert AppEndpointCategory.SOURCE == "source"
    assert issubclass(AppEndpointCategory, AppTypeEnum)


def test_mio_audience_values():
    assert MioAudience.values() == ["internal", "partner", "user"]
    assert MioAudience.INTERNAL == "internal"
    assert issubclass(MioAudience, AppTypeEnum)
