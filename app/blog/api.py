import asyncio
import logging
from datetime import datetime
from typing import Optional
from typing import Union
from fastapi import APIRouter, HTTPException
from fastapi import Depends, Response
from fastapi.responses import RedirectResponse

from .messages import CreateNewPost, UpdateHeader, UpdateBody
from .messages import StartModeration, SetModerationResult
from base_tools.base_moderation import generate_mcode, McodeSize
from base_tools.base_moderation import ModerationControlRecord as MCR
from base_tools.bus import MsgBus
from .schemas.response_models import PublicationCreated, PublicatedPost
from .schemas.response_models import ContentSchema, set_schema
from .schemas.request_models import UpdateHeaderRequest, UpdateBodyRequest
from .schemas.request_models import StartModerationRequest
from .schemas.request_models import SetContentCheckResult
from config.config import get_bus, mod_uow, cont_uow
from cache import CacheEngine, get_cache_engine
from authors.auth.auth import get_uid_from_token


__all__ = [
        "main",
        "author",
        ]


main = APIRouter(prefix="/main")  # rename to main
author = APIRouter(prefix="/main/{user_id}")  # for registered users

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
str_handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(levelname)s %(asctime)s %(message)s")
str_handler.setFormatter(formatter)
logger.addHandler(str_handler)


@author.post("/new")
async def create_new_post(
        title: str,
        user_id: str = Depends(get_uid_from_token),
        bus: MsgBus = Depends(get_bus),
        ) -> RedirectResponse:
    pub_id = generate_mcode(symblos_cnt=McodeSize.MIN_16S)
    # check user permissions here
    int_cmd = CreateNewPost(
            uid=pub_id,
            author_id=user_id,
            title=title,
            )
    bus_task = asyncio.create_task(bus.handle(int_cmd))
    try:
        await asyncio.gather(bus_task)
        return RedirectResponse(
                f"/main/{user_id}/edit/{pub_id}",
                status_code=303,
                )
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Not found.")


@author.get("/edit/{pub_id}", response_model=None)
async def get_post_by_id(
        pub_id: str,
        user_id: str = Depends(get_uid_from_token),
        ) -> Union[PublicationCreated, Response]:
    """get author`s post by post_id."""
    d_schema: Optional[ContentSchema] = None
    async with mod_uow as uow:
        post = await uow.storage.get_post_by_uid(pub_id)
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
        user_id: str = Depends(get_uid_from_token),
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
        logger.error(err)
        raise HTTPException(status_code=404, detail="Not found.")


@author.patch("/edit/{pub_id}/update_text")
async def update_body(
        request: UpdateBodyRequest,
        user_id: str = Depends(get_uid_from_token),
        bus: MsgBus = Depends(get_bus),
        ) -> Response:
    """update current post text body."""
    upd_body = UpdateBody(
            uid=request.body_id,
            pub_id=request.pub_id,
            payload=request.payload,
            )
    upd_task = asyncio.create_task(bus.handle(upd_body))
    try:
        await asyncio.gather(upd_task)
        return Response(status_code=200)
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Not found.")


@author.patch("/edit/{pub_id}/pub")
async def pub(
        cmd: StartModerationRequest,
        user_id: str = Depends(get_uid_from_token),
        bus: MsgBus = Depends(get_bus),
        ) -> Response:
    """send post to moderation."""
    # check user permissions
    start_moderation = StartModeration(
            pub_id=cmd.pub_id,
            author_id=user_id,
            act_dt=datetime.utcnow(),
            blocks=cmd.blocks,
            )
    start_task = asyncio.create_task(bus.handle(start_moderation))
    try:
        await asyncio.gather(start_task)
        return Response(status_code=200)
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Ups.. sth was wrong...")


@author.patch("/moderated/{pub_id}/activate")
async def activate_moderated_post() -> None:
    """activate post if it was successfully moderated."""
    ...


@author.get("/rejected")
async def show_my_rejected_posts(
        user_id: str = Depends(get_uid_from_token),
        ) -> None:
    """show all rejected main."""
    ...


@author.get("/rejected/{pub_id}")
async def get_rejected_post(
        user_id: str = Depends(get_uid_from_token),
        ) -> None:
    """show current rejected post."""
    ...


@author.post("/rejected/{pub_id}/correct")
async def correct_rejected_post(
        user_id: str = Depends(get_uid_from_token),
        ) -> RedirectResponse:
    """rollback post to template for correction."""
    ...
    pub_id = None
    user_id = None
    return RedirectResponse(f"/main/{user_id}/edit/{pub_id}", status_code=303)


@main.get("/")
async def show_rated_main_previews() -> None:
    """show all rated main previews.
    From most common watched."""
    return Response(status_code=201)


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
async def like(
        pub_id: str,
        user_id: str = Depends(get_uid_from_token),
        bus: MsgBus = Depends(get_bus),
        ) -> None:

    """like current post (from main or inside a post)."""
    # cmd = LikeThisPost(uid=pub_id, produser=user_id)
    # like_task = asyncio.create_task(bus.handle(cmd))
    # ch_cache = asyncio.create_task(cache_keeper.get_post_stat(pub_id))
    # await asyncio.gather(like_task, ch_cache)
    # return ch_cache.result()
    return None


@main.patch("/{pub_id}/dislike")
async def dislike(
        pub_id: str,
        user_id: str = Depends(get_uid_from_token),
        bus: MsgBus = Depends(get_bus),
        ) -> None:
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


@main.get("/moderation/posts", include_in_schema=False)
async def get_content_for_moderation(
        pub_id: str,
        rkey: str,
        c_uid: str,
        redis: CacheEngine = Depends(get_cache_engine),
        ) -> dict[str, str]:
    mcr = redis.get_temp_obj(pub_id)
    logger.debug(mcr)
    if mcr is None:
        raise HTTPException(status_code=404, detail="MCR not found.")
    mcr = MCR.from_json(mcr)
    if not mcr.mcode_registered(rkey):
        raise HTTPException(status_code=403, detail="Forbidden.")
    async with cont_uow as content_provider:
        storage = content_provider.storage
        try:
            content = await storage.get_content_by_id(c_uid)
            return {rkey: content.body}
        except Exception as err:
            logger.error(err)
            raise HTTPException(status_code=404, detail="Not found.")
        return None


@main.post("/moderation/posts/set", include_in_schema=False)
async def set_moderation_result(
        request: SetContentCheckResult,
        bus: MsgBus = Depends(get_bus),
        ) -> Response:
    result = SetModerationResult(
            mcr_id=request.mcr_id,
            block_id=request.mcode,
            state=request.state,
            report=request.report,
            )
    task = asyncio.create_task(bus.handle(result))
    try:
        await asyncio.gather(task)
        return Response(status_code=200)
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Ups! Sth went wrong...")
