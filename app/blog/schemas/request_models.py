from pydantic import BaseModel


class UpdateHeaderRequest(BaseModel):
    """update header data after edition."""
    pub_id: str
    header_id: str
    payload: str


class UpdateBodyRequest(BaseModel):
    """update text body for current post."""
    pub_id: str
    body_id: str
    payload: str
