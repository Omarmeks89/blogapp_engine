import asyncio
import logging
from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse

from .auth.auth import create_access_token, get_uid_from_token
from .schemas.request_models import NewAuthor
from .security.passwd_hashing import PasslibCrypt
from config.config import authors_uow, get_bus
from base_tools.bus import MsgBus
from base_tools.base_moderation import generate_mcode
from .messages import (
        RegisterNewAuthor,
        ActivateAuthor,
        )


__all__ = (
        "users",
        )


passwd_crypt = PasslibCrypt()
users = APIRouter(prefix="/users")
logger = logging.getLogger(__name__)


@users.post("/new")
async def create_new_author(
        author: NewAuthor = Depends(),
        bus: MsgBus = Depends(get_bus),
        ) -> RedirectResponse:
    """create new user author_ in system."""
    author_uid = generate_mcode()
    create_author = RegisterNewAuthor(
            uid=author_uid,
            login=author.login,
            email=author.email,
            passwd=author.passwd,
            )
    reg_task = asyncio.create_task(bus.handle(create_author))
    try:
        await asyncio.gather(reg_task)
    except Exception as err:
        msg = f"Expected error: {err=}"
        logger.error(msg)
        raise HTTPException(status_code=503, detail="Unfamiliar error.")
    return RedirectResponse("/main", status_code=303)


@users.patch("/activate")
async def activate_author(
        uid: str = Depends(get_uid_from_token),
        bus: MsgBus = Depends(get_bus),
        ) -> Response:
    activate = ActivateAuthor(uid=uid)
    task = asyncio.create_task(bus.handle(activate))
    try:
        await asyncio.gather(task)
        # needed RedirectResponse
        return Response(status_code=200)
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Not found")


@users.post("/token")
async def login(
        form: OAuth2PasswordRequestForm = Depends(),
        ) -> dict[str, str]:
    async with authors_uow as operator:
        authors = operator.storage
        author = await authors.get_author_by_login(form.username)
        if author is None:
            raise HTTPException(status_code=400, detail="login or password")
        if not passwd_crypt.verify(form.password, author.hpasswd):
            raise HTTPException(status_code=400, detail="login or password")
        token_exp = timedelta(minutes=30)
        token = create_access_token(
                data={"sub": author.uid, "login": author.login},
                exp_time=token_exp,
                )
        return {"access_token": token, "token_type": "bearer"}
