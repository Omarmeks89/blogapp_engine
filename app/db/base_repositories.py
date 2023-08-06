from abc import ABC, abstractmethod
from typing import TypeVar
from typing import Generic
from typing import Any
from typing import Type
from enum import Enum

from sqlalchemy import MetaData, Table
from sqlalchemy.orm import Session


DBMetaT = TypeVar("DBMetaT", bound=MetaData, contravariant=True)
DBTableT = TypeVar("DBTableT", bound=Table, contravariant=True)
SessionT = TypeVar("SessionT", bound=Session, contravariant=True)
AnyModelT = TypeVar("AnyModelT", bound=Any)


class RepoState(int, Enum):
    NOTSET: int = 0
    ISSET: int = 1


class Repository(ABC, Generic[DBMetaT, DBTableT]):
    """Repository interface / type."""
    _model: Type[AnyModelT]
    _state: RepoState

    @abstractmethod
    def __init__(self, meta: DBMetaT, table: DBTableT) -> None: pass

    @abstractmethod
    def attach_session(self, session: SessionT) -> None: pass

    @abstractmethod
    def detach_session(self) -> None: pass
