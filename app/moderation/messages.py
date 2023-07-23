from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ContentTypes(str, Enum):
    TEXT: str = "text"
    VIDEO: str = "video"
    AUDIO: str = "audio"
    IMAGE: str = "image"


@dataclass
class StartModeration:
    """block example (ContentBlockT):
    {block_id: block_type}
    We use author_id and pub_id
    to create path for S3 server.
    We`ll getting content from S3,
    not from DB. If text is bigger
    as 2048 bytes, it will be saved as
    text file on S3 server to.
    """
    pub_id: str
    author_id: str
    act_dt: datetime
    blocks: list[dict[str, ContentTypes]]


@dataclass
class PostAccepted:
    pub_id: str


@dataclass
class PostRejected:
    pub_id: str


@dataclass
class SetModerationResult:
    mcr_id: str
    block_id: str
    state: str
    report: str
