from abc import ABC, abstractmethod
from typing import TypeVar, Optional


ContentT = TypeVar("ContentT", bound="AbsContent", contravariant=True)
ContentVT = TypeVar("ContentVT", bound="AbsContent", covariant=True)


class _Moderatable(ABC):
    """interface for users activity - like, comment, etc
    Like, dislike, comment should use that interface."""

    @abstractmethod
    async def accept(self) -> None:
        """send exact event type to system bus."""
        pass

    @abstractmethod
    async def decline(self) -> None:
        """decline action and send exact event to bus."""
        pass


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
    @property
    @abstractmethod
    async def content(self) -> ContentVT:
        """show content to moderator."""
        pass

    @abstractmethod
    async def add_content(self, content: ContentT) -> None:
        """add content to created comment or post"""
        pass

    @abstractmethod
    async def remove_content(self) -> None:
        """remove all content block from publication at all."""
        pass

    @abstractmethod
    async def remove(self) -> None:
        """remove current publication."""
        pass

    @abstractmethod
    async def save_as_template(self) -> None:
        """save current publication template."""
        pass

    @abstractmethod
    async def publish(self, *, cov_letter: Optional[ContentT] = None) -> None:
        """send to publication, can add cover letter or text preview."""
        pass
