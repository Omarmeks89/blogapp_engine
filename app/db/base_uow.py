from abc import ABC, abstractmethod
from typing import Generator
from typing import TypeVar
from typing import Generic
from typing import Any
from asyncio import create_task
from typing import Protocol

from base_tools.base_types import SysMsgT
from .sessions import AbcSessionFactory, Session


AnyMsgInvarT = TypeVar("AnyMsgInvarT", bound=Any)
RepoCV = TypeVar("RepoCV", contravariant=True)
SessionCV = TypeVar("SessionCV", contravariant=True)
UOWProtoT = TypeVar("UOWProtoT", bound="UOWProto", contravariant=True)
T = TypeVar("T", bound="UOWProto", covariant=True)


class UOWProto(ABC, Generic[RepoCV, SessionCV]):
    """UOW type configuration. Build from Repo and Session."""

    @abstractmethod
    def __init__(self, repo: RepoCV, session: SessionCV) -> None: pass

    @property
    @abstractmethod
    def storage(self) -> RepoCV: pass

    @abstractmethod
    def fetch_event(self, event: SysMsgT) -> None: pass

    @abstractmethod
    def get_events(self) -> Generator: pass

    @abstractmethod
    async def __aenter__(self: T) -> T: pass

    @abstractmethod
    async def __aexit__(self, *args) -> None: pass

    @abstractmethod
    async def commit(self) -> None: pass

    @abstractmethod
    async def rollback(self) -> None: pass


class Repository(Protocol):
    """Implementation for Duck typing in UOW."""

    def attach_session(self, session: Session) -> None: ...

    def detach_session(self) -> None: ...


class BaseUOW(UOWProto):

    def __init__(
            self,
            repo: Repository,
            session: AbcSessionFactory,
            ) -> None:
        self._repository = repo
        self._ses_fct = session
        self._curr_ses = None
        try:
            from collections import deque
            self._events: deque[SysMsgT] = deque()
        except ImportError:
            raise Exception

    async def __aenter__(self: T) -> T:
        self._curr_ses = self._ses_fct()
        self._repository.attach_session(self._curr_ses)
        return self

    async def __aexit__(self, *args) -> None:
        self._repository.detach_session()
        if self._curr_ses and hasattr(self._curr_ses, "close"):
            await self._curr_ses.close()
        return None

    @property
    @abstractmethod
    def storage(self) -> Repository:
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


class Handler(ABC, Generic[UOWProtoT]):
    """Handler interface."""

    @abstractmethod
    def __init__(self, uow: UOWProtoT) -> None: pass

    @property
    @abstractmethod
    def events(self) -> Generator[SysMsgT]: pass

    @abstractmethod
    async def handle(self, cmd: AnyMsgInvarT) -> None: pass


class BaseCmdHandler(Handler):

    def __init__(self, uow: UOWProto) -> None:
        self._uow: UOWProto[Repository, Session] = uow
        self._task = create_task

    @property
    def events(self) -> Generator:
        """redirect events upper."""
        return self._uow.get_events()

    @abstractmethod
    async def handle(self, cmd: AnyMsgInvarT) -> None:
        """one command = one handler"""
        pass
