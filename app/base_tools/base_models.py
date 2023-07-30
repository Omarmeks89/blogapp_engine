from abc import ABC, abstractmethod
from typing import TypeVar, Generator, Any

from .base_moderation import _ContentBlock


ContentT = TypeVar("ContentT", bound="AbsContent", contravariant=True)
ContentVT = TypeVar("ContentVT", bound="AbsContent", covariant=True)
AnyPayloadT = TypeVar("AnyPayloadT", bound=Any, contravariant=True)


class Model:
    """empty root type."""
    pass


class AbsPublication(ABC):
    """interface for posts and comments"""

    @abstractmethod
    def events(self) -> Generator:
        """return events by one."""
        pass

    @abstractmethod
    def remove(self) -> None:
        """remove current publication."""
        pass

    @abstractmethod
    def moderate(self) -> None:
        """send to publication"""
        pass


class AbsContent(ABC):
    """Content interface."""

    @classmethod
    @abstractmethod
    def make_block(cls, mcode: str) -> _ContentBlock:
        """return content_block for moderation purp."""
        pass

    @property
    @abstractmethod
    def kind(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def set_body(self, payload: AnyPayloadT) -> None:
        """payload can be text or link -> all are strings."""
        pass
