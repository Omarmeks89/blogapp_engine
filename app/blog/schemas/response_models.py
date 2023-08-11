from datetime import datetime

from pydantic import BaseModel


class ContentSchema(BaseModel):
    """use like submodel into PublicationCreated."""
    header: str = "set header"
    body: str = "set body"
    tags: list[str] = []
    max_header_len: int = 256
    max_body_len: int = 2048


class PublicatedContent(BaseModel):
    """submodel for PublicatedPost.
    Represents active and moderated content."""
    header: str
    body: str


class PublicationStat(BaseModel):
    """publication statistic."""
    watches: int
    likes: int
    dislikes: int
    reposts: int
    comments: int


class PublicationCreated(BaseModel):
    """returns after creation new blanc post."""
    uid: str
    author_id: str
    content: ContentSchema
    title: str = ""


class PublicatedPost(BaseModel):
    pub_id: str
    author_id: str
    my_grade: str  # LIKE / DISLIKE
    tags: list[str] = []
    pub_dt: datetime
    content: PublicatedContent
    stat: PublicationStat
