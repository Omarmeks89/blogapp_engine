from abc import ABC, abstractmethod
from typing import TypeVar
from typing import Generic
from typing import Any
from typing import Type
from typing import Optional
from enum import Enum

from base_tools.exceptions import RepositoryError
from sqlalchemy import Table
from sqlalchemy.orm import Session


DBTableT = TypeVar("DBTableT", bound=Table, contravariant=True)
SessionT = TypeVar("SessionT", bound=Session, contravariant=True)
AnyModelT = TypeVar("AnyModelT", bound=Any)


class RepoState(int, Enum):
    NOTSET: int = 0
    ISSET: int = 1


class Repository(ABC, Generic[DBTableT]):
    """Repository interface / type."""
    _model: Type[AnyModelT]
    _state: RepoState

    @abstractmethod
    def __init__(self, table: DBTableT) -> None: pass

    @abstractmethod
    def attach_session(self, session: SessionT) -> None: pass

    @abstractmethod
    def detach_session(self) -> None: pass


class BaseRepository(Repository):
    """base interface for repository obj."""

    _model: Type[AnyModelT]
    _state: RepoState

    @classmethod
    def _set_repo(cls) -> None:
        """switch state to ISSET."""
        cls._state = RepoState.ISSET

    @classmethod
    def _unset_repo(cls) -> None:
        """switch state to NOTSET."""
        cls._state = RepoState.NOTSET

    @classmethod
    def _attach_model_to_table(cls, tbl: Table, *, test: bool = False) -> None:
        if cls._state is RepoState.ISSET:
            return None
        try:
            from sqlalchemy.orm import registry
            from sqlalchemy import inspect
        except ImportError as err:
            raise RepositoryError from err
        mapper = registry()
        mapper.map_imperatively(cls._model, tbl)
        if test:
            from sys import stdout
            m_info = inspect(cls._model)
            stdout.write(
                    f"\tRepo: {cls.__name__}, module: {__name__}.\n"
                    f"fields: {m_info.all_orm_descriptors.keys()}.\n"
                )
            stdout.flush()
        cls._set_repo()
        return None

    def __init__(
            self,
            table: Table,
            *,
            run_test: bool = False,
            ) -> None:
        self._attach_model_to_table(table, test=run_test)
        self._session: Optional[Session] = None
        self._attached = False

    def attach_session(self, session: Session) -> None:
        if not self._attached:
            self._session = session
            self._attached = True
        return None

    def detach_session(self) -> None:
        if self._attached:
            self._session = None
            self._attached = False
        return None

    def _check_session_attached(self) -> Optional[None]:
        if not self._attached:
            raise RepositoryError("Session wasn`t attached to repository.")
        return None
