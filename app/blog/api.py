import asyncio
import json
from typing import Optional
from typing import Union
from fastapi import APIRouter, HTTPException
from fastapi import Depends, Response
from fastapi.responses import RedirectResponse

from .messages import CreateNewPost, UpdateHeader, UpdateBody
from base_tools.base_moderation import generate_mcode, McodeSize
from base_tools.bus import MsgBus
from .schemas.response_models import PublicationCreated, PublicatedPost
from .schemas.response_models import ContentSchema, set_schema
from .schemas.request_models import UpdateHeaderRequest, UpdateBodyRequest
from .schemas.request_models import StartModerationRequest
from config.config import get_bus, mod_uow, cont_uow
from cache import CacheEngine, get_cache_engine


__all__ = [
        "main",
        "author",
        ]


main = APIRouter(prefix="/main")  # rename to main
author = APIRouter(prefix="/main/{user_id}")  # for registered users


#  -----------------> "/{user_id}"


@author.post("/new")
async def create_new_post(
        user_id: str,
        title: str,
        bus: MsgBus = Depends(get_bus),
        ) -> RedirectResponse:
    """TODO -> add /{author_id}/..."""
    pub_id = generate_mcode(symblos_cnt=McodeSize.MIN_16S)
    int_cmd = CreateNewPost(
            uid=pub_id,
            author_id=user_id,
            title=title,
            )
    bus_task = asyncio.create_task(bus.handle(int_cmd))
    await asyncio.gather(bus_task)
    return RedirectResponse(f"/main/{user_id}/edit/{pub_id}", status_code=303)


@author.get("/edit/{pub_id}", response_model=None)
async def get_post_by_id(
        pub_id: str,
        user_id: str,
        redis: CacheEngine = Depends(get_cache_engine),
        ) -> Union[PublicationCreated, Response]:
    """get author`s post by post_id."""
    post = redis.get_temp_obj(pub_id)
    if post:
        redis.set_temp_obj(pub_id, post, 600)
        response = json.loads(post)
        return response
    d_schema: Optional[ContentSchema] = None
    async with mod_uow as uow:
        post = uow.storage.get_post_by_uid(pub_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Not found...")
        async with cont_uow as cont_provider:
            repo = cont_provider.storage
            content = await repo.get_all_post_content(pub_id)
            if content is None:
                raise HTTPException(status_code=404, detail="Try later")
            d_schema = ContentSchema()
            set_schema(d_schema, content)
        return PublicationCreated(
                uid=post.uid,
                author_id=post.author_id,
                content=d_schema,
                title=post.title,
                )


@author.patch("/edit/{pub_id}/update_header")
async def update_header(
        request: UpdateHeaderRequest,
        bus: MsgBus = Depends(get_bus),
        ) -> Response:
    """update current post header."""
    upd_header = UpdateHeader(
            uid=request.header_id,
            pub_id=request.pub_id,
            payload=request.payload,
            )
    upd_task = asyncio.create_task(bus.handle(upd_header))
    try:
        await asyncio.gather(upd_task)
        return Response(status_code=200)
    except Exception as err:
        if not upd_task.done():
            upd_task.cancel()
        raise HTTPException(status_code=404, detail=f"{err=}")


@author.patch("/edit/{pub_id}/update_text")
async def update_body(
        request: UpdateBodyRequest,
        bus: MsgBus = Depends(get_bus),
        ) -> Response:
    """update current post text body."""
    upd_body = UpdateBody(
            uid=request.header_id,
            pub_id=request.pub_id,
            payload=request.payload,
            )
    upd_task = asyncio.create_task(bus.handle(upd_body))
    try:
        await asyncio.gather(upd_task)
        return Response(status_code=200)
    except Exception as err:
        if not upd_task.done():
            upd_task.cancel()
        raise HTTPException(status_code=404, detail=f"{err=}")


@author.post("/edit/{pub_id}/add_tags")
async def add_tags() -> None:
    """add tags to post."""
    ...


@author.patch("/edit/{pub_id}/pub")
async def pub(
        cmd: StartModerationRequest,
        bus: MsgBus = Depends(get_bus),
        ) -> None:
    """send post to moderation."""
    ...


@author.patch("/moderated/{pub_id}/activate")
async def activate_moderated_post() -> None:
    """activate post if it was successfully moderated."""
    ...


@author.get("/rejected")
async def show_rejected_main() -> None:
    """show all rejected main."""
    ...


@author.get("/rejected/{pub_id}")
async def get_rejected_post() -> None:
    """show current rejected post."""
    ...


@author.post("/rejected/{pub_id}/correct")
async def correct_rejected_post() -> RedirectResponse:
    """rollback post to template for correction."""
    ...
    pub_id = None
    user_id = None
    return RedirectResponse(f"/main/{user_id}/edit/{pub_id}", status_code=303)


#  ----------------------------------> "/main"


@main.get("/")
async def show_rated_main_previews() -> None:
    """show all rated main previews.
    From most common watched."""
    ...


@main.get("/{auth_id}/all")
async def get_all_authors_main(auth_id: str) -> list[PublicatedPost]:
    """get all main, created by current user."""
    ...
    raise HTTPException(status_code=404, detail="No author found.")


@main.get("/{pub_id}")
async def get_selected_post(pub_id: str) -> PublicatedPost:
    """get selected post (on main page) by id. Redirect (watch action)"""
    ...


@main.patch("/{pub_id}/like")
async def like(pub_id: str, bus: MsgBus = Depends(get_bus)) -> None:
    """like current post (from main or inside a post)."""
    # cmd = LikeThisPost(uid=pub_id, produser=user_id)
    # like_task = asyncio.create_task(bus.handle(cmd))
    # ch_cache = asyncio.create_task(cache_keeper.get_post_stat(pub_id))
    # await asyncio.gather(like_task, ch_cache)
    # return ch_cache.result()
    return None


@main.patch("/{pub_id}/dislike")
async def dislike() -> None:
    """the same as like."""
    ...


@main.post("/{pub_id}/new_comment")
async def comment_current_post() -> None:
    """comment current post (inside, not from main)."""
    ...


@main.post("/{pub_id}/{comment_id}/new_comment")
async def comment_current_comment() -> None:
    """comment current comment."""
    ...


@main.get("/{pub_id}/repost")
async def repost() -> None:
    ...


@main.get("/moderation/posts/{post_id}/{c_uid}")
async def get_content_for_moderation(post_id: str, c_uid: str) -> None:
    ...
