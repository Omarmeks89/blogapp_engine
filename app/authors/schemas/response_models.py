from pydantic import BaseModel


class ShowUser(BaseModel):
    """base model for display user."""
    uid: str
    login: str
