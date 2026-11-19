from abc import abstractmethod

from app.core.common.dtos.query_ast_facade_dtos import QueryAstFacadeCtx
from app.core.common.singleton import SingletonMeta


class QueryAstFacade(metaclass=SingletonMeta):
    @abstractmethod
    def run(self, ctx: QueryAstFacadeCtx) -> int: ...
