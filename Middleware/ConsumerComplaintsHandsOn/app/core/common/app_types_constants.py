"""Every type list of the app (DESIGN.md, D55). Each list is an enum whose parent is AppTypeEnum.

Add the next list (dataset location types, statuses, ...) here as one more subclass.
"""

from enum import Enum


class AppTypeEnum(str, Enum):
    """Parent of every type list. It has no members of its own."""

    @classmethod
    def values(cls) -> list[str]:
        """The allowed string values, in definition order. Callers check `value in EngineType.values()`."""
        return [member.value for member in cls]


class EngineType(AppTypeEnum):
    """The workflow engines (D52). M02 runs only apache_airflow."""

    APACHE_AIRFLOW = "apache_airflow"
    AWS_STEP_FUNCTIONS = "aws_step_functions"
