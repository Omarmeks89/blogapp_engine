from abc import ABC, abstractmethod
from typing import TypeAlias, Any
from asyncio import create_task

from .base_types import CVEventT, CEventT
from .db_types import BaseRepository
from .db_types import BaseCache


InvariantCmd: TypeAlias = Any


class BaseUOW(ABC):

    def __init__(
            self,
            repository: InvariantCmd,
            cache: InvariantCmd,
            ) -> None:
        self._repository = repository
        self._cache = cache
        try:
            from collections import deque
            self._events = deque()
        except ImportError:
            self._events = []

    async def __aenter__(self) -> "BaseUOW":
        return self

    async def __aexit__(
            self,
            exc: Any,
            exc_type: Any,
            msg: Any,
            ) -> None:
        return None

    @property
    @abstractmethod
    def storage(self) -> BaseRepository:
        """return instance of repository."""
        pass

    @property
    @abstractmethod
    def cache(self) -> BaseCache:
        """return instance of cache."""
        pass

    @abstractmethod
    def fetch_event(self, event: CVEventT) -> None:
        pass

    @abstractmethod
    def get_event(self) -> CEventT:
        """pop event from queue."""
        pass


class BaseCmdHandler(ABC):

    def __init__(self, uow: BaseUOW) -> None:
        self._uow = uow
        self._task = create_task

    @abstractmethod
    async def handle(self, cmd: InvariantCmd) -> None:
        """one command = one handler"""
        pass
