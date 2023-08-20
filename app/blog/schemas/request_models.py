from datetime import datetime

from pydantic import BaseModel

from base_tools.base_content import ContentTypes


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


class StartModerationRequest(BaseModel):
    """start post moderation process."""
    pub_id: str
    start_dt: datetime
    blocks: dict[str, ContentTypes]


class SetContentCheckResult(BaseModel):
    """set moderation result for current content block."""
    mcr_id: str
    mcode: str
    state: str
    report: str
