from abc import ABC, abstractmethod
from typing import Optional
from typing import TypeVar
from typing import Generic
from typing import Type

from sqlalchemy import MetaData, Table

from base_tools.base_models import Model
from base_tools.exceptions import RepositoryError
from sessions import AbcSession


DBMetaT = TypeVar("DBMetaT", bound=MetaData, contravariant=True)
DBTableT = TypeVar("DBTableT", bound=Table, contravariant=True)


class Repository(ABC, Generic[DBMetaT, DBTableT]):
    """Repository interface / type."""

    @abstractmethod
    def __init__(self, meta: DBMetaT, table: DBTableT) -> None: pass

    @abstractmethod
    async def init_model(self, model: Type[Model]) -> None: pass

    @abstractmethod
    def attach_session(self, session: AbcSession) -> None: pass

    @abstractmethod
    def detach_session(self) -> None: pass


class SQLALCHBaseRepo(Repository):
    """Base impl for sqlalchemy repository."""

    def __init__(
            self,
            meta: MetaData,
            table: Table,
            ) -> None:
        self._meta = meta
        self._table = table
        self._session: Optional[AbcSession] = None
        self._attached = False
        self._model: Optional[Type[Model]] = None

    async def init_model(self, model: Type[Model]) -> None:
        """model have to be a class, not instance."""
        if self._model is not None:
            return None
        try:
            from sqlalchemy.orm import mapper
            if not issubclass(type(model), Model):
                raise RepositoryError("Invalid type.")
        except ImportError as err:
            raise RepositoryError from err
        mapper(model, self._table)
        self._model = model

    def attach_session(self, session: AbcSession) -> None:
        if not self._attached:
            self._session = session
            self._attached = True

    def detach_session(self) -> None:
        if self._attached:
            self._session = None
            self._attached = False
