import asyncio
import logging

from db.base_uow import BaseCmdHandler
from .storage.models import Author
from .security.passwd_hashing import PasslibCrypt
from .messages import (
        RegisterNewAuthor,
        ActivateAuthor,
        )


crypt = PasslibCrypt()
logger = logging.getLogger("AUTH_HANDLERS")


class CreateNewAuthorHandler(BaseCmdHandler):

    async def handle(self, cmd: RegisterNewAuthor) -> None:
        async with self._uow as operator:
            authors = operator.storage
            author = Author(
                    uid=cmd.uid,
                    login=cmd.login,
                    email=cmd.email,
                    hpasswd=crypt.hash(cmd.passwd),
                    )
            task = self._task(authors.create_new_author(author))
            try:
                await asyncio.gather(task)
                await operator.commit()
            except Exception as err:
                logger.error(err)
                await operator.rollback()
            return None


class ActivateAuthorHandler(BaseCmdHandler):
    """activate user after email confirmation."""

    async def handle(self, cmd: ActivateAuthor) -> None:
        async with self._uow as operator:
            authors = operator.storage
            author = await authors.get_author_by_id(cmd.uid)
            if author is None:
                raise Exception("HandlerError")
            author.activate()
            try:
                await authors.update_author_state(author)
                await operator.commit()
            except Exception as err:
                logger.error(f"ERROR in {__name__}: {err=}")
                await operator.rollback()
                raise Exception("HandlerError")
            return None
