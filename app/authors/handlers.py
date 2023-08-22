import asyncio
import logging

from db.base_uow import BaseCmdHandler
from .storage.models import Author
from .security.passwd_hashing import PasslibCrypt
from tasks.email import LOGIN, send_email
from .messages import (
        RegisterNewAuthor,
        ActivateAuthor,
        )
from base_tools.sys_messages import (
        PostAccepted,
        PostRejected,
        NotifyAuthor,
        )


crypt = PasslibCrypt()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
str_handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(levelname)s %(asctime)s %(message)s")
str_handler.setFormatter(formatter)
logger.addHandler(str_handler)


class NotifyAuthorsHandler(BaseCmdHandler):
    """let`s move it to notification service later."""

    async def handle(self, cmd: NotifyAuthor) -> None:
        """for bus test only."""
        try:
            send_email.delay(LOGIN, cmd.email, cmd.msg)
        except Exception as err:
            logger.error(err)
            pass
        return None


class PostAcceptedHandler(BaseCmdHandler):

    async def handle(self, event: PostAccepted) -> None:
        async with self._uow as operator:
            authors = operator.storage
            author = await authors.get_author_by_id(event.author)
            if author is None:
                logger.error("No author")
                raise Exception(f"Author {event.author} not found.")
            msg = (
                    f" Dear {author.login}!\nYour post {event.title} "
                    "was successfully moderated."
                    )
            self._uow.fetch_event(
                    NotifyAuthor(
                        email=author.email,
                        msg=msg,
                        ),
                    )
            await operator.rollback()
            return None


class PostRejectedHandler(BaseCmdHandler):

    async def handle(self, event: PostRejected) -> None:
        async with self._uow as operator:
            authors = operator.storage
            author = await authors.get_author_by_id(event.author)
            if author is None:
                logger.error("No author")
                raise Exception(f"Author {event.author} not found.")
            reasons = "\n".join(event.reasons)
            msg = (
                    f" Dear {author.login}!\nYour post {event.title} "
                    "was rejected. Please, look at the reasons:\n"
                    f"{reasons}\n"
                    )
            self._uow.fetch_event(
                    NotifyAuthor(
                        email=author.email,
                        msg=msg,
                        ),
                    )
            await operator.rollback()
            return None


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
