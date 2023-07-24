from abc import ABC, abstractmethod
from typing import TypeVar, Generator


ContentT = TypeVar("ContentT", bound="AbsContent", contravariant=True)
ContentVT = TypeVar("ContentVT", bound="AbsContent", covariant=True)


class AbsContent(ABC):
    """Content interface."""

    @abstractmethod
    async def add_new_block(self, content: ContentT) -> None:
        """add new block of text, video or picture content
        to post or comment."""
        pass

    @abstractmethod
    async def remove_block(self, c_block: ContentT) -> None:
        """remove selected content block."""
        pass

    @abstractmethod
    async def save(self) -> None:
        """save current content state."""
        pass

    @abstractmethod
    async def edit(self) -> None:
        """edit current content block."""
        pass


class AbsPublication(ABC):
    """interface for posts and comments"""

    @abstractmethod
    def events(self) -> Generator:
        """return events by one."""
        pass

    @abstractmethod
    def edit(self) -> None:
        """edit post. Get content blocks to edit."""
        pass

    @abstractmethod
    def remove(self) -> None:
        """remove current publication."""
        pass

    @abstractmethod
    def moderate(self) -> None:
        """send to publication"""
        pass
