from abc import ABC, abstractmethod
from typing import Generator
from typing import TypeVar
from typing import Generic
from typing import Any
from asyncio import create_task
from typing import Protocol
from enum import Enum

from base_tools.base_types import SysMsgT
from sqlalchemy.orm import Session


AnyMsgInvarT = TypeVar("AnyMsgInvarT", bound=Any)
RepoCV = TypeVar("RepoCV", contravariant=True)
SessionCV = TypeVar("SessionCV", contravariant=True)
UOWProtoT = TypeVar("UOWProtoT", bound="UOWProto", contravariant=True)
T = TypeVar("T", bound="UOWProto", covariant=True)


class UOW_FSM(int, Enum):
    READY: int = 0
    TRANSACTION: int = 1
    COMMITED: int = 2
    ROLLEDBACK: int = 4


class UOWProto(ABC, Generic[RepoCV, SessionCV]):
    """UOW type configuration. Build from Repo and Session."""

    _work_state: UOW_FSM

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

    _work_state: UOW_FSM = UOW_FSM

    def __init__(
            self,
            repo: Repository,
            session: Session,
            ) -> None:
        self._repository = repo
        self._ses_fct = session
        self._curr_ses = None
        self._state = type(self)._work_state.READY
        try:
            from collections import deque
            self._events: deque[SysMsgT] = deque()
        except ImportError:
            raise Exception

    async def __aenter__(self: T) -> T:
        if self._state is not type(self)._work_state.READY:
            err_msg = (
                    f"In module {__name__}, uow_type: {type(self).__name__} "
                    f"external access for running transaction. {self._state}."
                    )
            raise Exception(err_msg)
        self._curr_ses = self._ses_fct()
        self._repository.attach_session(self._curr_ses)
        self._state = type(self)._work_state.TRANSACTION
        return self

    async def __aexit__(self, *args) -> None:
        self._repository.detach_session()
        if self._curr_ses and hasattr(self._curr_ses, "close"):
            self._curr_ses.close()
        self._state = type(self)._work_state.READY
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
        if (
                hasattr(self._curr_ses, "commit")
                and self._state is type(self)._work_state.TRANSACTION
                ):
            self._curr_ses.commit()
            self._state = type(self)._work_state.COMMITED
        return None

    async def rollback(self) -> None:
        if (
                hasattr(self._curr_ses, "rollback")
                and self._state is type(self)._work_state.TRANSACTION
                ):
            self._curr_ses.rollback()
            self._state = type(self)._work_state.ROLLEDBACK
        return None


class Handler(ABC, Generic[UOWProtoT]):
    """Handler interface."""

    @abstractmethod
    def __init__(self, uow: UOWProtoT) -> None: pass

    @property
    @abstractmethod
    def events(self) -> Generator: pass

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
