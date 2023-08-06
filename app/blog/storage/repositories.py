from typing import Optional
from typing import TypeVar
from typing import Type

from sqlalchemy import Table
from sqlalchemy import update, select
from sqlalchemy.orm import Session

from db.base_repositories import Repository, RepoState
from base_tools.exceptions import RepositoryError
from base_tools.base_content import PostStatus
from .models import BlogPost


StatusT = TypeVar("StatusT", PostStatus, str)


class PostsRepository(Repository):

    _model: Type[BlogPost] = BlogPost
    _state: RepoState = RepoState.NOTSET

    @classmethod
    def _set_repo(cls) -> None:
        """switch state to ISSET."""
        cls._state = RepoState.ISSET

    @classmethod
    def _unset_repo(cls) -> None:
        """switch state to NOTSET."""
        cls._state = RepoState.NOTSET

    @classmethod
    def _attach_model_to_table(cls, tbl: Table, *, test: bool = False) -> None:
        if cls._state is RepoState.ISSET:
            return None
        try:
            from sqlalchemy.orm import registry
            from sqlalchemy import inspect
        except ImportError as err:
            raise RepositoryError from err
        mapper = registry()
        mapper.map_imperatively(cls._model, tbl)
        if test:
            from sys import stdout
            m_info = inspect(BlogPost)
            stdout.write(
                    f"\tRepo: {cls.__name__}, module: {__name__}.\n"
                    f"fields: {m_info.all_orm_descriptors.keys()}.\n"
                )
            stdout.flush()
        cls._set_repo()
        return None

    def __init__(
            self,
            table: Table,
            *,
            run_test: bool = False,
            ) -> None:
        self._attach_model_to_table(table, test=run_test)
        self._session: Optional[Session] = None
        self._attached = False

    def attach_session(self, session: Session) -> None:
        if not self._attached:
            self._session = session
            self._attached = True
        return None

    def detach_session(self) -> None:
        if self._attached:
            self._session = None
            self._attached = False
        return None

    def _check_session_attached(self) -> Optional[None]:
        if not self._attached:
            raise RepositoryError("Session wasn`t attached to repository.")
        return None

    def create_new_post(self, post: BlogPost) -> None:
        """for a test."""
        self._check_session_attached()
        self._session.add(post)
        return None

    async def update_state(self, pub_id: str, state: StatusT) -> None:
        self._check_session_attached()
        upd_state = (
            update(BlogPost)
            .where(BlogPost.uid == pub_id)
            .values(state=state)
            .execution_options(syncronize_session="fetch")
            )
        self._session.execute(upd_state)
        return None

    async def update_title(self, pub_id: str, title: str) -> None:
        self._check_session_attached()
        upd_title = (
            update(BlogPost)
            .where(BlogPost.uid == pub_id)
            .values(title=title)
            .execution_options(syncronize_session="fetch")
            )
        self._session.execute(upd_title)
        return None

    def get_post_by_uid(self, pub_id: str) -> BlogPost:
        """for a test."""
        self._check_session_attached()
        post = (
                select(BlogPost)
                .where(BlogPost.uid == pub_id)
                )
        return self._session.execute(post).scalar()

    async def get_all_posts_by_author(self, author_id: str) -> list[BlogPost]:
        self._check_session_attached()
        posts = (
            select(BlogPost)
            .where(author_id == author_id)
            )
        # scalars -> we will get python classes.
        posts_items = self._session.execute(posts).scalars().all()
        return posts_items

    async def get_posts_by_author_with_state(
            self,
            author_id: str,
            state: str,
            ) -> list[BlogPost]:
        """return all author`s posts by wished state."""
        self._check_session_attached()
        posts = (
            select(BlogPost)
            .where(author_id == author_id, state=state)
            )
        # scalars -> we will get python classes.
        posts_items = self._session.execute(posts).scalars().all()
        return posts_items
