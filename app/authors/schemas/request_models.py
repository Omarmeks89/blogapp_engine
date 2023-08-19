from pydantic import BaseModel


class NewAuthor(BaseModel):
    """request on new author creation."""
    login: str
    email: str
    passwd: str
