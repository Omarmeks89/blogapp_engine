import asyncio
from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.responses import RedirectResponse

from .messages import CreateNewPost, SaveNewPost
from base_tools.base_moderation import generate_mcode, McodeSize
from base_tools.bus import MsgBus
from db.sessions import Session
from .storage.repositories import PostsRepository
from db.tables import publications
from .storage.models import FoundedPost
from config.config import get_bus


__all__ = [
        "posts",
        ]


posts = APIRouter(prefix="/posts")
session = Session()
repo = PostsRepository(publications)


@posts.post("/new")
async def create_new_post(
        cmd: SaveNewPost,
        bus: MsgBus = Depends(get_bus),
        ) -> RedirectResponse:
    int_cmd = CreateNewPost(
            uid=generate_mcode(symblos_cnt=McodeSize.MIN_16S),
            author_id=cmd.author_id,
            title=cmd.title,
            )
    bus_task = asyncio.create_task(bus.handle(int_cmd))
    await asyncio.gather(bus_task)
    return RedirectResponse(f"/posts/{int_cmd.uid}", status_code=303)


@posts.get("/{pub_id}")
async def get_post_by_id(pub_id: str) -> FoundedPost:
    session = Session()
    repo.attach_session(session)
    post = repo.get_post_by_uid(pub_id)
    if post:
        founded = FoundedPost(
                uid=post.uid,
                author_id=post.author_id,
                title=post.title,
                )
        session.commit()
        repo.detach_session()
        return founded
    raise HTTPException(status_code=404, detail="BlogPost wasn`t found in DB")


@posts.get("/")
async def get_posts_by_author(auth_id: str) -> list[FoundedPost]:
    """get all posts, created by current user."""
    session = Session()
    repo.attach_session(session)
    posts = await repo.get_all_posts_by_author(auth_id)
    if posts:
        founded = []
        for post in posts:
            f_post = FoundedPost(
                    uid=post.uid,
                    author_id=post.author_id,
                    title=post.title,
                    )
            founded.append(f_post)
        session.commit()
        repo.detach_session()
        return founded
    raise HTTPException(status_code=404, detail="BlogPost wasn`t found in DB")
