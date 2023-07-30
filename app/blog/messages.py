from dataclasses import dataclass
from datetime import datetime

from base_tools.base_content import ContentTypes
from base_tools.base_types import Command, Event


@dataclass
class StartModeration(Command):
    pub_id: str
    author_id: str
    act_dt: datetime
    blocks: dict[str, ContentTypes]


@dataclass
class PostAccepted(Event):
    pub_id: str


@dataclass
class PostRejected(Event):
    pub_id: str


@dataclass
class PostDeleted(Event):
    pub_id: str


@dataclass
class PostRolledToDraft(Event):
    pub_id: str


@dataclass
class PostPublished(Event):
    pub_id: str


@dataclass
class ActivateLater(Command):
    pub_id: str
    delay_dt: datetime


@dataclass
class SetModerationResult(Command):
    """fix new state in MCR."""
    mcr_id: str
    block_id: str
    state: str
    report: str


@dataclass
class ModerationStarted(Event):
    pub_id: str
    author_id: str
    pub_title: str


@dataclass
class CommentDeleted(Event):
    """
    pub_id: publication id,
    uid: unique id for comment.
    """
    pub_id: str
    uid: str


@dataclass
class StartCommentModeration(Command):
    """send current comment to moderation.
    pub_id: publication id;
    uid: unique comment id.
    """
    pub_id: str
    uid: str


@dataclass
class CommentPublished(Event):
    pub_id: str
    uid: str


@dataclass
class CommentRejected(Event):
    """event for notify service.
    pub_id: publication id;
    uid: unique comment id.
    """
    pub_id: str
    uid: str
