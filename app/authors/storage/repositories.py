from sqlalchemy import Table
from sqlalchemy import update, select

from db.base_repositories import BaseRepository
from .models import Author


class AuthorsRepository(BaseRepository):
    ...
