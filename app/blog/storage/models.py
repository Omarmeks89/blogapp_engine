from typing import Optional
from pydantic import BaseModel

from base_tools.base_types import IntervalT
from base_tools.base_content import PostStatus, BasePublication
from base_tools.base_content import CommentStatus
from base_tools.exceptions import PublicationError
from blog.messages import (
        PostDeleted,
        PostRolledToDraft,
        ModerationStarted,
        PostAccepted,
        PostRejected,
        PostPublished,
        ActivateLater,
        CommentDeleted,
        CommentPublished,
        CommentRejected,
        StartCommentModeration,
        )


class FoundedPost(BaseModel):
    """Test model."""
    uid: str
    author_id: str
    title: str


class BlogPost(BasePublication):
    """Can build from ORM model."""

    _fsm: PostStatus = PostStatus.INIT

    def __init__(
            self,
            uid: str,
            author_id: str,
            title: str,
            creation_dt: IntervalT,
            *,
            state: Optional[PostStatus] = None,
            ) -> None:
        super().__init__()
        self.uid = uid
        self.author_id = author_id
        self.title = title
        self.creation_dt = creation_dt

    def remove(self) -> None:
        if self._state in (self._fsm.DELETED, self._fsm.MODERATION):
            raise PublicationError("Can`t delete removed or processed post.")
        self._state = self._fsm.DELETED
        self._events.append(
            PostDeleted(pub_id=self._uid),
            )

    def rollback_to_draft(self) -> None:
        """we can rollback from each state after moderation."""
        if self._state in (self._fsm.REJECTED, self._fsm.ACCEPTED):
            self._state = self._fsm.DRAFT
            self._events.append(
                PostRolledToDraft(pub_id=self._uid),
                )
        return None

    def moderate(self) -> None:
        """set on moderation + add event to
        notify author about process started."""
        if self._state == self._fsm.DRAFT:
            self._state = self._fsm.MODERATION
            self._events.append(
                    ModerationStarted(
                            pub_id=self._uid,
                            author_id=self._author_id,
                            pub_title=self._title,
                        ),
                )
            return None
        raise PublicationError(
                f"Can`t set on moderation. Curr status: {self._state}",
                )

    def accept(self) -> None:
        """mark post as accepted to finish moderation."""
        if self._state == self._fsm.MODERATION:
            self._state = self._fsm.ACCEPTED
            self._events.append(
                    PostAccepted(pub_id=self._uid),
                )
            return None
        raise PublicationError("Can`t accept post that isn`t on moderation.")

    def decline(self) -> None:
        """Mark post as rejected."""
        if self._state == self._fsm.MODERATION:
            self._state = self._fsm.REJECTED
            self._events.append(
                    PostRejected(pub_id=self._uid),
                )
            return None
        raise PublicationError("Can`t decline post that isn`t on moderation.")

    def activate(
            self,
            *,
            act_dt_interval: Optional[IntervalT] = None,
            ) -> None:
        if self._state == self._fsm.ACCEPTED:
            self._state = self._fsm.PUBLISHED
            if act_dt_interval is None:
                self._events.append(PostPublished(pub_id=self._uid))
            else:
                self._events.append(
                    ActivateLater(pub_id=self._uid, delay_dt=act_dt_interval),
                    )
            return None
        raise PublicationError("Can`t activate post that wasn`t accepted.")


class BlogComment(BasePublication):
    """not copied to repo."""

    _fsm: CommentStatus = CommentStatus.INIT

    def __init__(
            self,
            uid: str,
            pub_id: str,
            author_id: str,
            creation_dt: IntervalT,
            *,
            state: Optional[CommentStatus] = None,
            ) -> None:
        """set model from ORM model."""
        super().__init__()
        self._uid = uid
        self._pub_id = pub_id
        self._author_id = author_id
        self._creation_dt = creation_dt

    def remove(self) -> None:
        """remove current publication."""
        if self._state in (self._fsm.DRAFT, self._fsm.PUBLISHED):
            self._state = self._fsm.DELETED
            self._events.append(
                    CommentDeleted(pub_id=self._pub_id, uid=self._uid),
                )
        raise Exception("Can`t remove comment")

    def moderate(self) -> None:
        """send to publication"""
        if self._state == self._fsm.DRAFT:
            self._state = self._fsm.MODERATION
            self._events.append(
                    StartCommentModeration(pub_id=self._pub_id, uid=self._uid),
                )
            return None
        raise Exception(f"Can`t moderate comment with state: {self._state}")

    def accept(self) -> None:
        if self._state == self._fsm.MODERATION:
            self._state = self._fsm.PUBLISHED
            self._events.append(
                    CommentPublished(pub_id=self._pub_id, uid=self._uid),
                )
            return None
        raise Exception("Can`t accept comment that isn`t on moderation.")

    def decline(self) -> None:
        """rollback to draft for correct content."""
        if self._state == self._fsm.MODERATION:
            self._state = self._fsm.DRAFT
            self._events.append(
                    CommentRejected(pub_id=self._pub_id, uid=self._uid),
                )
            return None
