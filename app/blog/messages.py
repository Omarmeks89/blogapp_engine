from datetime import datetime

from base_tools.base_content import ContentTypes
from base_tools.base_types import Command, Event


class StartModeration(Command):
    pub_id: str
    author_id: str
    act_dt: datetime
    blocks: dict[str, ContentTypes]


class PostAccepted(Event):
    pub_id: str


class PostRejected(Event):
    pub_id: str


class PostDeleted(Event):
    pub_id: str


class PostRolledToDraft(Event):
    pub_id: str


class PostPublished(Event):
    pub_id: str


class ActivateLater(Command):
    pub_id: str
    delay_dt: datetime


class SetModerationResult(Command):
    """fix new state in MCR."""
    mcr_id: str
    block_id: str
    state: str
    report: str


class ModerationStarted(Event):
    pub_id: str
    author_id: str
    pub_title: str


class CommentDeleted(Event):
    """
    pub_id: publication id,
    uid: unique id for comment.
    """
    pub_id: str
    uid: str


class StartCommentModeration(Command):
    """send current comment to moderation.
    pub_id: publication id;
    uid: unique comment id.
    """
    pub_id: str
    uid: str


class CommentPublished(Event):
    pub_id: str
    uid: str


class CommentRejected(Event):
    """event for notify service.
    pub_id: publication id;
    uid: unique comment id.
    """
    pub_id: str
    uid: str


class SaveNewPost(Command):
    """move to schemas.py"""
    author_id: str
    title: str


class CreateNewPost(Command):
    uid: str
    author_id: str
    title: str


class NotifyAuthor(Command):
    uid: str
    msg: str
