from typing import Type

from sqlalchemy import Table
from sqlalchemy import update, select

from db.base_repositories import BaseRepository, RepoState
from .models import Author


class AuthorsRepository(BaseRepository):

    _model: Type[Author] = Author
    _state: RepoState = RepoState.NOTSET

    def __init__(
            self,
            table: Table,
            *,
            run_test: bool = False,
            ) -> None:
        super().__init__(table, run_test=run_test)

    async def create_new_author(self, author: Author) -> None:
        self._check_session_attached()
        self._session.add(author)
        return None

    async def update_author_state(self, author: Author) -> None:
        self._check_session_attached()
        upd_state = (
                update(Author)
                .where(Author.uid == author.uid)
                .values(_state=author.state)
                .execution_options(syncronize_session=False)
                )
        self._session.execute(upd_state)
        return None

    async def get_author_by_id(self, uid: str) -> Author:
        self._check_session_attached()
        author = (
                select(Author)
                .where(Author.uid == uid)
                )
        return self._session.execute(author).scalar()

    async def get_author_by_login(self, login: str) -> Author:
        self._check_session_attached()
        author = (
                select(Author)
                .where(Author.login == login)
                )
        return self._session.execute(author).scalar()
