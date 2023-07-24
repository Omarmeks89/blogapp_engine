from abc import abstractmethod
from typing import TypeAlias
from typing import Union
from typing import Generator
from typing import Literal
from enum import Enum

from .base_models import AbsPublication
from .exceptions import PublicationError


class PostStatus(int, Enum):
    """Post FSM."""
    DRAFT: int = 0
    MODERATION: int = 1
    PUBLISHED: int = 2
    ACCEPTED: int = 4
    REJECTED: int = 8
    DELETED: int = 16


class CommentStatus(int, Enum):
    """Comment FSM."""
    DRAFT: int = 0
    MODERATION: int = 1
    PUBLISHED: int = 2
    DELETED: int = 4


PubFSM_T: TypeAlias = Union[CommentStatus, PostStatus]
StateKwargT = Literal["state"]


class BasePublication(AbsPublication):

    _fsm: PubFSM_T

    def __init__(self, *args, **kwargs) -> None:
        state = kwargs.get(StateKwargT)
        if state is None:
            self._state = self._fsm.DRAFT
        else:
            self._state = state
        try:
            from collections import deque
            self._events = deque()
        except ImportError as err:
            raise PublicationError(f"Can`t import collections module: {err}")

    def events(self) -> Generator:
        """return events by one."""
        while self._events:
            yield self._events.popleft()

    def edit(self) -> None:
        """edit post. Get content blocks to edit."""
        if self._state != self._fsm.DRAFT:
            raise PublicationError("Can`t edit locked publication")

    @abstractmethod
    def remove(self) -> None:
        """remove current publication."""
        pass

    @abstractmethod
    def moderate(self) -> None:
        """send to publication"""
        pass
