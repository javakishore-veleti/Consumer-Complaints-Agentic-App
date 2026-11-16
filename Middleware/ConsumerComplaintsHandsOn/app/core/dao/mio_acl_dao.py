"""Interface of the DAO for the mios_acl table (D89)."""

from abc import abstractmethod

from app.core.common.dtos.mio_acl_dtos import MioAclCtx
from app.core.common.singleton import SingletonMeta


class MioAclDao(metaclass=SingletonMeta):
    @abstractmethod
    def create(self, ctx: MioAclCtx) -> int:
        """Needs req.mio_id and req.audience. NOT_FOUND if MIO missing; CONFLICT if duplicate."""

    @abstractmethod
    def list(self, ctx: MioAclCtx) -> int:
        """Optional filters: req.mio_id, req.audience."""

    @abstractmethod
    def delete(self, ctx: MioAclCtx) -> int:
        """Needs req.id."""
