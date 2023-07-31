import asyncio

from .services import mod_service
from db.base_uow import BaseCmdHandler
from base_tools.exceptions import DBError, HandlerError, ModerationError
from .servises import PublicationModerator as Moderator
from .messages import (
        PostRejected,
        PostAccepted,
        StartModeration,
        SetModerationResult,
        )


class SetPostModerationResHandler(BaseCmdHandler):

    async def handle(self, cmd: SetModerationResult) -> None:
        """Set block moderation result"""
        async with self._uow as operator:
            mcr = await operator.cache.get(cmd.mcr_id)
            try:
                await mod_service.set_moderation_result(cmd, mcr)
            except ModerationError as err:
                raise HandlerError from err
            for _ in range(len(mod_service.events)):
                self._uow.fetch_event(mod_service.dump_event())
        return None


class BeginPostModerationHandler(BaseCmdHandler):
    """ react on Task Accepted."""

    async def handle(self, cmd: StartModeration) -> None:
        """We`re waiting and react on StartModeration command.

            *mcr -> moderation_ctrl_block.
        """
        async with self._uow as operator:
            moderator = Moderator()
            blocks = self._task(moderator.build_content_blocks(
                pub_id=cmd.pub_id,
                blocks=cmd.blocks,
                ))
            mcr = self._task(moderator.make_mcr(pub_id=cmd.pub_id))
            tasks = (mcr, blocks)
            try:
                await asyncio.gather(*tasks)
            except ModerationError as err:
                for t in tasks:
                    if not t.cancelled():
                        t.cancel()
                raise HandlerError(err)
            try:
                model = await operator.storage.get_pub_by_id(pub_id=cmd.pub_id)
                upd_model = await moderator.set_on_moderation(model)
                await operator.storage.update(upd_model)
            except (DBError, ModerationError) as err:
                raise HandlerError from err
            for _ in range(len(moderator.events)):
                self._uow.fetch_event(moderator.dump_event())
        return None


class FixPostAcceptedHandler(BaseCmdHandler):
    """react if PostAccepted event was produced."""

    async def handle(self, event: PostAccepted) -> None:
        async with self._uow as operator:
            upd_state_task = self._task(
                operator.storage.set_as_accepted(event.pub_id),
                )
            accept = self._task(mod_service.accept_publication(event.pub_id))
            tasks = (upd_state_task, accept)
            try:
                await asyncio.gather(*tasks)
            except DBError as err:
                await operator.storage.rollback_last()
                for t in tasks:
                    if not t.done():
                        t.cancel()
                raise HandlerError from err
            for _ in range(len(mod_service.events)):
                self._uow.fetch_event(mod_service.dump_event())
        return None


class FixPostRejectedHandler(BaseCmdHandler):
    """react if PostRejected event was produced."""

    async def handle(self, event: PostRejected) -> None:
        async with self._uow as operator:
            upd_state_task = self._task(
                operator.storage.set_as_rejected(event.pub_id),
                )
            reject = self._task(mod_service.reject_publication(event.pub_id))
            tasks = (upd_state_task, reject)
            try:
                await asyncio.gather(*tasks)
            except DBError as err:
                await operator.storage.rollback_last()
                raise HandlerError from err
            for _ in range(len(mod_service.events)):
                self._uow.fetch_event(mod_service.dump_event())
        return None
