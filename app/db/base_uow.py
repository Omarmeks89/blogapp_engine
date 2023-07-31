from abc import ABC, abstractmethod
from typing import Generator
from typing import TypeAlias, Any
from asyncio import create_task
from contextlib import AbstractAsyncContextManager as AACM
from typing import Protocol

from base_tools.base_types import SysMsgT
from .sessions import AbcSessionFactory, Session


AnyMsgInvarT: TypeAlias = Any


class AbstractUOW(AACM):

    @abstractmethod
    def fetch_event(self, event: SysMsgT) -> None:
        pass

    @abstractmethod
    def get_events(self) -> Generator:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass


class RepositoryProto(Protocol):
    """Implementation for Duck typing in UOW."""

    def attach_session(self, session: Session) -> None: ...

    def detach_session(self) -> None: ...


class BaseUOW(AbstractUOW):

    def __init__(
            self,
            repository: RepositoryProto,
            session_factory: AbcSessionFactory,
            ) -> None:
        self._repository = repository
        self._ses_fct = session_factory
        self._curr_ses = None
        try:
            from collections import deque
            self._events: deque[SysMsgT] = deque()
        except ImportError:
            raise Exception

    async def __aenter__(self) -> "BaseUOW":
        self._curr_ses = self._ses_fct()
        self._repository.attach_session(self._curr_ses)
        return self

    async def __aexit__(self, *args) -> None:
        self._repository.detach_session()
        if self._curr_ses and hasattr(self._curr_ses, "close"):
            await self._curr_ses.close()
        await super().__aexit__(*args)
        return None

    @property
    @abstractmethod
    def storage(self) -> RepositoryProto:
        """return instance of repository."""
        pass

    @abstractmethod
    def fetch_event(self, event: SysMsgT) -> None:
        pass

    def get_events(self) -> Generator:
        """to handle and fetch events lazy."""
        while self._events:
            yield self._events.popleft()

    async def commit(self) -> None:
        if hasattr(self._curr_ses, "commit"):
            await self._curr_ses.commit()
        return None

    async def rollback(self) -> None:
        if hasattr(self._curr_ses, "rollback"):
            await self._curr_ses.rollback()
        return None


class BaseCmdHandler(ABC):

    def __init__(self, uow: BaseUOW) -> None:
        self._uow = uow
        self._task = create_task

    @property
    def events(self) -> Generator:
        """redirect events upper."""
        return self._uow.get_events()

    @abstractmethod
    async def handle(self, cmd: AnyMsgInvarT) -> None:
        """one command = one handler"""
        pass
