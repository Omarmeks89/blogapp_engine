from pydantic import BaseModel


class ContentSchema(BaseModel):
    header: str = ""
    body: str = ""
    tags: list[str] = []


class PublicationCreated(BaseModel):
    uid: str
    author_id: str
    content: ContentSchema = ContentSchema()
    title: str = ""
