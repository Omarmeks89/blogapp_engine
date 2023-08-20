from abc import abstractmethod
from typing import TypeAlias
from typing import Union
from typing import Generator
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from .base_models import AbsPublication, AbsContent, Model
from .base_moderation import _ContentBlock


__all__ = (
        "PostStatus",
        "CommentStatus",
        "ContentTypes",
        "BasePublication",
        "BaseContentPreset",
        )


class PostStatus(int, Enum):
    """Post FSM."""
    DRAFT: int = 0
    MODERATION: int = 1
    PUBLISHED: int = 2
    ACCEPTED: int = 4
    REJECTED: int = 8
    DELETED: int = 16
    INIT: int = 128


class CommentStatus(int, Enum):
    """Comment FSM."""
    DRAFT: int = 0
    MODERATION: int = 1
    PUBLISHED: int = 2
    DELETED: int = 4
    INIT: int = 64


class ContentTypes(str, Enum):
    NONE: str = "none"
    TEXT: str = "text"
    VIDEO: str = "video"
    AUDIO: str = "audio"
    IMAGE: str = "image"


class ContentRoles(str, Enum):
    NOTSET: str = "notset"
    HEADER: str = "header"
    BODY: str = "body"


PubFSM_T: TypeAlias = Union[CommentStatus, PostStatus]
StateKwarg: str = "state"


class BasePublication(AbsPublication, Model):

    _fsm: PubFSM_T

    def __init__(self, *args, **kwargs) -> None:
        state = kwargs.get(StateKwarg)
        if state is None:
            self._state = self._fsm.DRAFT
        else:
            self._state = state

    @property
    def state(self) -> PubFSM_T:
        return self._state

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
    creation_dt: datetime
    body: str = field(default_factory=str)
    _kind: ContentTypes = ContentTypes.NONE
    _role: ContentRoles = ContentRoles.NOTSET

    @abstractmethod
    def __post_init__(self) -> None:
        """define exact _kind."""
        pass

    def set_role(self, role: ContentRoles) -> None:
        """set new role for content."""
        if self._role is ContentRoles.NOTSET:
            self._role = role

    @property
    def kind(self) -> ContentTypes:
        return self._kind

    @property
    def description(self) -> dict[str, ContentTypes]:
        return {self.uid: self._kind}

    def set_body(self, payload: str) -> None:
        self.body = payload
        return None

    @classmethod
    @abstractmethod
    def make_block(cls, mcode: str) -> _ContentBlock:
        """return content_block for moderation purp."""
        pass
