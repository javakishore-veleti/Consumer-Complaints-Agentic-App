from app.core.common.app_types_constants import AppTypeEnum, EngineType


def test_engine_type_values_are_the_short_codes():
    assert EngineType.values() == ["apache_airflow", "aws_step_functions"]


def test_engine_type_members_are_plain_strings():
    assert EngineType.APACHE_AIRFLOW == "apache_airflow"
    assert "aws_step_functions" in EngineType.values()
    assert "bogus" not in EngineType.values()


def test_the_parent_has_no_members_and_every_type_list_extends_it():
    assert list(AppTypeEnum) == []
    assert issubclass(EngineType, AppTypeEnum)
