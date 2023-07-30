from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import Metadata, Table

from base_tools.base_models import Model
from base_tools.exceptions import RepositoryError
from sessions import AbcSession


class AbcRepository(ABC):

    @abstractmethod
    async def init_model(self, model: Model) -> None:
        """add model to metadata."""
        pass

    @abstractmethod
    def attach_session(self, session: AbcSession) -> None:
        """set new session for new connections."""
        pass

    @abstractmethod
    def detach_session(self) -> None:
        """forget current session."""
        pass


class SQLALCHBaseRepo(AbcRepository):
    """Base impl for sqlalchemy repository."""

    def __init__(
            self,
            meta: Metadata,
            table: Table,
            ) -> None:
        self._meta = meta
        self._table = table
        self._session: Optional[AbcSession] = None
        self._attached = False
        self._model: Optional[Model] = None

    async def init_model(self, model: Model) -> None:
        """model have to be a class, not instance."""
        if self._model is not None:
            return None
        try:
            from sqlalchemy.orm import mapper
            if not issubclass(type(model), Model):
                raise RepositoryError("Can`t map instance, need class.")
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
