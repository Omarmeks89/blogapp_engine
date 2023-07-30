from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeAlias
import json

from .exceptions import SerializationError


JSONFmt: TypeAlias = str
StateAttr: str = "_state"


class ModerationRes(str, Enum):
    NOT_SET: str = "not_set"
    DECLINED: str = "declined"
    ACCEPTED: str = "accepted"


class _Serializable(ABC):
    """INterface for serializable objects."""

    @abstractmethod
    def to_json(self) -> JSONFmt:
        """convert inst to json str."""
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, j_str: JSONFmt) -> "_Serializable":
        """remoderation as example."""
        pass


class _Moderatable(ABC):
    """interface for moderation. FSM"""

    @abstractmethod
    def accept(self) -> None:
        """accept this object."""
        pass

    @abstractmethod
    def decline(self) -> None:
        """decline this object."""
        pass


class Serializable(_Serializable):
    """INterface for serializable objects."""

    def to_json(self) -> JSONFmt:
        return json.dumps(self.__dict__, indent=4)

    @classmethod
    def from_json(cls, j_str: JSONFmt) -> "_Serializable":
        """remoderation as example."""
        try:
            return cls(**json.loads(j_str))
        except json.decoder.JSONDecodeError as err:
            raise SerializationError from err


class ModeratableBlock(_Moderatable):
    """interface for moderation. FSM"""

    _state: ModerationRes = ModerationRes.NOT_SET

    def accept(self) -> None:
        if hasattr(self, StateAttr) and self._state != ModerationRes.DECLINED:
            self._state = ModerationRes.ACCEPTED

    def decline(self) -> None:
        if hasattr(self, StateAttr) and self._state != ModerationRes.ACCEPTED:
            self._state = ModerationRes.DECLINED
