from datetime import datetime
from typing import Any
from typing import List
from typing import TypeVar

from pydantic import BaseModel


SchemaT = TypeVar("SchemaT", bound="ContentSchema")


class Header(BaseModel):
    uid: str = ""
    body: str = ""
    max_len: int = 256


class Body(BaseModel):
    uid: str = ""
    body: str = ""
    max_len: int = 2048


def set_schema(schema: SchemaT, content: List[Any]) -> None:
    for c in content:
        match c._role:
            case "header":
                schema.header = Header(uid=c.uid, body=c.body)
            case "body":
                schema.body = Body(uid=c.uid, body=c.body)
            case _:
                continue


class ContentSchema(BaseModel):
    """use like submodel into PublicationCreated."""
    header: Header = Header()
    body: Body = Body()
    tags: list[str] = []


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
