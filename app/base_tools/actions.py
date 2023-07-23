from abc import ABC
from enum import Enum
from typing import TypeVar, TypeAlias, Literal
import json

from .exceptions import SerializationError


JSONFmt: TypeAlias = str
_SerializableT = TypeVar("_SerializableT", covariant=True)
StateAttr = Literal["state"]


class ModerationRes(str, Enum):
    NOT_SET: str = "not_set"
    DECLINED: str = "declined"
    ACCEPTED: str = "accepted"


class _Serializable(ABC):
    """INterface for serializable objects."""

    def to_json(self) -> JSONFmt:
        return json.dumps(self.__dict__, indent=4)

    @classmethod
    def from_json(cls, j_str: JSONFmt) -> _SerializableT:
        """remoderation as example."""
        try:
            return cls(**json.loads(j_str))
        except json.decoder.JSONDecodeError as err:
            raise SerializationError from err


class _Moderatable(ABC):
    """interface for moderation. FSM"""

    state: ModerationRes = ModerationRes.NOT_SET

    def accept(self) -> None:
        if self.state != ModerationRes.DECLINED and hasattr(self, StateAttr):
            self.state = ModerationRes.ACCEPTED

    def decline(self) -> None:
        if self.state != ModerationRes.ACCEPTED and hasattr(self, StateAttr):
            self.state = ModerationRes.DECLINED
