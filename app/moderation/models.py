from typing import Optional
from typing import TypeVar
from datetime import datetime

from base_tools.base_content import PostStatus, BasePublication, PubFSM_T
from base_tools.exceptions import PublicationError
from base_tools.actions import _Moderatable
from .types import (
        PostDeleted,
        PostRolledToDraft,
        ModerationStarted,
        PostAccepted,
        PostRejected,
        PostPublished,
        ActivateLater,
        )


IntervalT = TypeVar("IntervalT", bound=datetime,  contravariant=True)


class BlogPost(_Moderatable, BasePublication):
    """Can build from ORM model."""

    _fsm: PubFSM_T = PostStatus

    def __init__(
            self,
            uid: str,
            author_id: str,
            title: str,
            creation_dt: datetime,
            *,
            state: Optional[PostStatus] = None,
            ) -> None:
        """set model from ORM model."""
        super().__init__()
        self._uid = uid
        self._author_id = author_id
        self._title = title
        self._creation_dt = creation_dt

    def remove(self) -> None:
        if self._state in (self._fsm.DELETED, self._fsm.MODERATION):
            raise PublicationError("Can`t delete removed or processed post.")
        self._state = self._fsm.DELETED
        self._events.append(
            PostDeleted(uid=self._uid),
            )

    def rollback_to_draft(self) -> None:
        """we can rollback from each state after moderation."""
        if self._state in (self._fsm.REJECTED, self._fsm.ACCEPTED):
            self._state = self._fsm.DRAFT
            self._events.append(
                PostRolledToDraft(uid=self._uid),
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
                f"Can`t set on moderation. Curr status: {self._status}",
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
                self._events.append(PostPublished(uid=self._uid))
            else:
                self._events.append(
                    ActivateLater(uid=self._uid, delay_dt=act_dt_interval),
                    )
            return None
        raise PublicationError("Can`t activate post that wasn`t accepted.")
