from abc import abstractmethod
from typing import TypeAlias
from typing import Union
from typing import Generator
from enum import Enum
from dataclasses import dataclass, field

from .base_models import AbsPublication, AbsContent
from .base_moderation import _ContentBlock
from .base_types import IntervalT
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
StateKwarg: str = "state"


class BasePublication(AbsPublication):

    _fsm: PubFSM_T

    def __init__(self, *args, **kwargs) -> None:
        state = kwargs.get(StateKwarg)
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

    @abstractmethod
    def remove(self) -> None:
        """remove current publication."""
        pass

    @abstractmethod
    def moderate(self) -> None:
        """send to publication"""
        pass


@dataclass
class BaseContentPreset(AbsContent):
    uid: str
    pub_id: str
    creation_dt: IntervalT
    body: str = field(default_factory=str)

    def set_body(self, payload: str) -> str:
        self.body = payload

    @classmethod
    @abstractmethod
    def make_block(cls, mcode: str) -> _ContentBlock:
        """return content_block for moderation purp."""
        pass
