from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import HTTPException

from base_tools.base_models import BaseAuthor
from base_tools.services import get_msg_bus, BaseChannel
from base_tools.urls import urls
from base_tools.dbengine import get_db_engine
from base_tools.dbengine import BaseDBAdapter, DBEngineError, DBSearchError
from .services import auth_service
from .messages import PublishNewPost, ShowMyPostsRequest
from .messages import SetModerationResult, PostsPreview


__all__ = [
        "posts",
        ]


posts = APIRouter(prefix="/posts")


@posts.post("/{post_id}")
async def publish_new_post(
        author: BaseAuthor = Depends(),
        pub_cmd: PublishNewPost = Depends(),
        msg_bus: BaseChannel = Depends(get_msg_bus),
        ) -> RedirectResponse:
    """send new post for moderation."""
    if not await auth_service.is_authorized(author):
        # redirect for auth
        return RedirectResponse("https://127.0.0.1:8000/")
    await msg_bus.register(pub_cmd)
    return RedirectResponse(url="https://127.0.0.1:8000/")


@posts.get("/{user_id}")  # [+] posts stat = active, mod, etc
async def show_user_posts(
        author: BaseAuthor = Depends(),
        request: ShowMyPostsRequest = Depends(),
        storage: BaseDBAdapter = Depends(get_db_engine),
        ) -> PostsPreview:
    """show my posts."""
    if not await auth_service.is_authorized(author):
        return RedirectResponse(url=urls.AUTH_PAGE)
    try:
        posts = await storage.get_posts(author.uid)
    except DBEngineError:
        raise HTTPException(
                status_code=503,
        )
    except DBSearchError:
        raise HTTPException(
                status_code=404,
        )
    return posts


@posts.get("/")
async def show_posts(
        author: BaseAuthor = Depends(),
        storage: BaseDBAdapter = Depends(get_db_engine),
        ) -> PostsPreview:
    """show all posts with pagination. auth nevermind"""
    try:
        posts = await storage.get_posts(author.uid)
    except DBEngineError:
        raise HTTPException(
                status_code=404,
        )
    return posts


@posts.post("/{post_id}/finalize")
async def finalize_moderation(
        fin_cmd: SetModerationResult = Depends(),
        msg_bus: BaseChannel = Depends(get_msg_bus),
        ) -> JSONResponse:
    """fetch moderation result responce for part of content from external
        service."""
    await msg_bus.register(fin_cmd)
    return JSONResponse({"res": 200}, status_code=200)
