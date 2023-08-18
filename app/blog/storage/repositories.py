import logging
from typing import TypeVar
from typing import Type

from sqlalchemy import Table
from sqlalchemy import update, select

from db.base_repositories import BaseRepository, RepoState
from base_tools.base_content import PostStatus
from .models import BlogPost
from ..content_types import TextContent


StatusT = TypeVar("StatusT", PostStatus, str)


logger = logging.getLogger("BLOG_LOG")


class PostsRepository(BaseRepository):

    _model: Type[BlogPost] = BlogPost
    _state: RepoState = RepoState.NOTSET

    def __init__(
            self,
            table: Table,
            *,
            run_test: bool = False,
            ) -> None:
        super().__init__(table, run_test=run_test)

    def create_new_post(self, post: BlogPost) -> None:
        self._check_session_attached()
        self._session.add(post)
        return None

    async def update_state(self, model: BlogPost) -> None:
        self._check_session_attached()
        upd_state = (
            update(BlogPost)
            .where(BlogPost.uid == model.uid)
            .values(state=model.state)
            .execution_options(syncronize_session=False)
            )
        self._session.execute(upd_state)
        return None

    async def update_title(self, pub_id: str, title: str) -> None:
        self._check_session_attached()
        upd_title = (
            update(BlogPost)
            .where(BlogPost.uid == pub_id)
            .values(title=title)
            .execution_options(syncronize_session=False)
            )
        self._session.execute(upd_title)
        return None

    def get_post_by_uid(self, pub_id: str) -> BlogPost:
        self._check_session_attached()
        post = (
                select(BlogPost)
                .where(BlogPost.uid == pub_id)
                )
        return self._session.execute(post).scalar()

    async def get_all_posts_by_author(self, auth_id: str) -> list[BlogPost]:
        self._check_session_attached()
        posts = (
            select(BlogPost)
            .where(BlogPost.author_id == auth_id)
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
            .where(BlogPost.author_id == author_id, BlogPost.state == state)
            )
        # scalars -> we will get python classes.
        posts_items = self._session.execute(posts).scalars().all()
        return posts_items


class ContentRepository(BaseRepository):

    _model: Type[TextContent] = TextContent
    _state: RepoState = RepoState.NOTSET

    def __init__(
            self,
            table: Table,
            *,
            run_test: bool = False,
            ) -> None:
        super().__init__(table, run_test=run_test)

    async def create_new_content(self, content: TextContent) -> None:
        self._check_session_attached()
        self._session.add(content)
        return None

    async def create_many_content_trans(self, cont: list[TextContent]) -> None:
        self._check_session_attached()
        self._session.begin()
        for content in cont:
            self._session.add(content)
        return None

    async def get_content_by_id(self, content_uid: str) -> TextContent:
        self._check_session_attached()
        content = (
                select(TextContent)
                .where(TextContent.uid == content_uid)
                )
        return self._session.execute(content).scalar()

    async def update_body(self, uid: str, pub_id: str, body: str) -> None:
        self._check_session_attached()
        upd_body = (
            update(TextContent)
            .where(TextContent.uid == uid, TextContent.pub_id == pub_id)
            .values(body=body)
            .execution_options(syncronize_session=False)
            )
        self._session.execute(upd_body)
        return None

    async def get_all_post_content(self, pub_id: str) -> list[TextContent]:
        self._check_session_attached()
        all_content = (
                select(TextContent)
                .where(TextContent.pub_id == pub_id)
                )
        content_items = self._session.execute(all_content).scalars().all()
        return content_items
