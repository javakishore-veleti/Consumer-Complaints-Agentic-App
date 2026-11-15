"""Interface of the DAO for the app_endpoints table (D85)."""

from abc import abstractmethod

from app.core.common.dtos.app_endpoint_dtos import AppEndpointCtx
from app.core.common.singleton import SingletonMeta


class AppEndpointDao(metaclass=SingletonMeta):
    """Singleton DAO. Methods take one AppEndpointCtx and return an integer code.

    From and to each need exactly one of a datasets_location id or an env-var name (never a value).
    Categories are AppEndpointCategory. No DB FKs; DAO checks location parents. credentials_ref is a name.
    """

    @abstractmethod
    def create(self, ctx: AppEndpointCtx) -> int: ...

    @abstractmethod
    def get(self, ctx: AppEndpointCtx) -> int: ...

    @abstractmethod
    def list(self, ctx: AppEndpointCtx) -> int: ...

    @abstractmethod
    def update(self, ctx: AppEndpointCtx) -> int: ...

    @abstractmethod
    def delete(self, ctx: AppEndpointCtx) -> int: ...
