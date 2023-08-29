from datetime import datetime
from typing import Any

from base_tools.base_content import ContentTypes
from base_tools.base_types import Command, Event
from .content_types import TextContent


class StartModeration(Command):
    pub_id: str
    author_id: str
    act_dt: datetime
    # {content_id: content_type} -> {"12534": "TEXT"}
    blocks: dict[str, ContentTypes]


class SetModerationResult(Command):
    """fix new state in MCR."""
    mcr_id: str
    block_id: str
    state: str
    report: str


class CheckModerationResult(Command):
    """check results stored in cache after moderation."""
    pub_id: str


class ModerationFailed(Event):
    """if any of blocks rejected or mcr expired."""
    pub_id: str
    reasons: list[str]


class ModerationDoneSuccess(Event):
    pub_id: str


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


class CreateContentForNewPost(Command):
    """raised when new empty post was created."""
    post: Any


class AddHeaderForPost(Command):
    """add Header (TextContent) for new post."""
    post: Any
    content: list[TextContent] = []


class AddBodyForPost(Command):
    """add Body (TextContent) for new post."""
    post: Any
    content: list[TextContent] = []


class SaveAllNewPostContent(Command):
    """save all content at the end of pipeline."""
    post: Any
    content: list[TextContent] = []


class UpdateHeader(Command):
    """update Header for currentpost.
    uid -> header-content id;
    pub_id -> current post id;
    payload -> new text payload."""
    uid: str
    pub_id: str
    payload: str


class UpdateBody(Command):
    uid: str
    pub_id: str
    payload: str


class AddToCache(Command):
    """add any item to cache."""
    skey: str
    obj: str


class RegisterMCR(Command):
    """register control record in cache."""
    skey: str
    obj: str
    blocks: dict


class UpdateMCR(Command):
    """update serialized MCR string with setted mod
    results."""
    skey: str
    obj: str


class DeleteMCR(Command):
    """remove control record after
    moderation finish."""
    pub_id: str


class LockContent(Command):
    """lock moderated content on editing."""
    content: list[dict]


class ModerateContent(Command):
    """send content-block to moderation.
    :uid: content id in DB;
    :mcode: unique command code (str)."""
    uid: str
    mcode: str
    pub_id: str
