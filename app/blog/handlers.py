import asyncio
import logging
from datetime import datetime

from db.base_uow import BaseCmdHandler
from base_tools.exceptions import HandlerError, ModerationError
from .storage.models import BlogPost
from tasks.moderation import fetch_content
from base_tools.base_moderation import generate_mcode, McodeSize
from base_tools.base_content import ContentRoles
from .content_types import TextContent
from .schemas.response_models import PublicationCreated
from .schemas.response_models import ContentSchema, set_schema
from .services import PublicationModerator
from cache import get_cache_engine
from .messages import (
        StartModeration,
        SetModerationResult,
        CreateNewPost,
        AddHeaderForPost,
        AddBodyForPost,
        SaveAllNewPostContent,
        UpdateHeader,
        UpdateBody,
        AddToCache,
        ModerateContent,
        ModerationFailed,
        ModerationDoneSuccess,
        RegisterMCR,
        UpdateMCR,
        DeleteMCR,
        CheckModerationResult,
        LockContent,
        )


ctime = datetime.now

h_logger = logging.getLogger(__name__)
h_logger.setLevel(logging.DEBUG)
str_handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(levelname)s %(asctime)s %(message)s")
str_handler.setFormatter(formatter)
h_logger.addHandler(str_handler)


class StartModerationNotifyHandler(BaseCmdHandler):

    async def handle(self, cmd: LockContent) -> None:
        """set moderated content as locked."""
        async with self._uow as operator:
            content = operator.storage
            lock = self._task(content.lock(cmd.content))
            try:
                await asyncio.gather(lock)
                await operator.commit()
            except Exception as err:
                await operator.rollback()
                h_logger.error(err)
                raise HandlerError(err)
            ct = await content.get_all_post_content(cmd.content[0]["c_uid"])
            h_logger.debug(ct)
            return None


class CreateNewPostHandler(BaseCmdHandler):

    async def handle(self, cmd: CreateNewPost) -> None:
        new_post = BlogPost(
                uid=cmd.uid,
                author_id=cmd.author_id,
                title=cmd.title,
                creation_dt=ctime(),
                )
        async with self._uow as operator:
            storage = operator.storage
            try:
                storage.create_new_post(new_post)
                await operator.commit()
            except Exception as err:
                await operator.rollback()
                h_logger.error(err)
                msg = (
                        f"\nModule {__name__}, class {type(self).__name__} "
                        f"fetched error from repo: {err}. FAILED\n"
                        )
                raise HandlerError(msg)
        schema = ContentSchema()
        post_preview = PublicationCreated(
                uid=cmd.uid,
                author_id=cmd.author_id,
                content=schema,
                title=cmd.title,
                )
        self._uow.fetch_event(AddHeaderForPost(
                    post=post_preview,
                    ),
                    )
        return None


class AddHeaderForPostHandler(BaseCmdHandler):

    async def handle(self, cmd: AddHeaderForPost) -> None:
        uid = generate_mcode(symblos_cnt=McodeSize.MIN_16S)
        header = TextContent(uid=uid, pub_id=cmd.post.uid, creation_dt=ctime())
        header.set_role(ContentRoles.HEADER)
        set_schema(cmd.post.content, [header, ])
        next_pipe_cmd = AddBodyForPost(post=cmd.post)
        next_pipe_cmd.content.append(header)
        self._uow.fetch_event(
                next_pipe_cmd,
                )
        return None


class AddBodyForPostHandler(BaseCmdHandler):

    async def handle(self, cmd: AddBodyForPost) -> None:
        uid = generate_mcode(symblos_cnt=McodeSize.MIN_16S)
        body = TextContent(uid=uid, pub_id=cmd.post.uid, creation_dt=ctime())
        body.set_role(ContentRoles.BODY)
        set_schema(cmd.post.content, [body, ])
        next_pipe_cmd = SaveAllNewPostContent(post=cmd.post)
        for c in cmd.content:
            next_pipe_cmd.content.append(c)
        next_pipe_cmd.content.append(body)
        self._uow.fetch_event(
                next_pipe_cmd,
                )
        return None


class SaveAllContentHandler(BaseCmdHandler):
    """save all content by default to db."""

    async def handle(self, cmd: SaveAllNewPostContent) -> None:
        async with self._uow as operator:
            await operator.storage.create_many_content_trans(
                    cont=cmd.content,
                    )
            try:
                await operator.commit()
            except Exception as err:
                h_logger.error(err)
                await operator.rollback()
                raise HandlerError(err)
        return None


class AddToCacheHandler(BaseCmdHandler):

    async def handle(self, cmd: AddToCache) -> None:
        try:
            redis = get_cache_engine()
            redis.set_temp_obj(
                    key=cmd.skey,
                    obj=cmd.obj,
                    exp_sec=600,
                    )
        except Exception as err:
            h_logger.error(err)
            raise HandlerError(err)
        return None


class RegisterMCRHandler(BaseCmdHandler):

    async def handle(self, cmd: RegisterMCR) -> None:
        cached = {
                "mcr": cmd.obj,
                **cmd.blocks,
                }
        try:
            redis = get_cache_engine()
            redis.set_ht_obj(hkey=cmd.skey, payload=cached)
        except Exception as err:
            h_logger.error(err)
            raise HandlerError(err)
        return None


class UpdateMCRHandler(BaseCmdHandler):

    async def handle(self, cmd: UpdateMCR) -> None:
        redis = get_cache_engine()
        try:
            redis.set_ht_field(hkey=cmd.skey, field="mcr", payload=cmd.obj)
        except Exception as err:
            h_logger.error(err)
            raise HandlerError(err)
        return None


class DeleteMCRHandler(BaseCmdHandler):

    async def handle(self, cmd: DeleteMCR) -> None:
        redis = get_cache_engine()
        try:
            redis.del_ht_obj(hkey=cmd.pub_id)
        except Exception as err:
            h_logger.error(err)
            raise HandlerError(err)
        return None


class SetResultToCacheHandler(BaseCmdHandler):

    async def handle(self, cmd: SetModerationResult) -> None:
        try:
            redis = get_cache_engine()
            redis.set_ht_field(cmd.mcr_id, cmd.block_id, cmd.state)
            redis.set_temp_obj(cmd.block_id, cmd.report, 600)
        except Exception as err:
            h_logger.error(err)
            raise HandlerError(err)
        self._uow.fetch_event(
                CheckModerationResult(
                    pub_id=cmd.mcr_id,
                    ),
                )
        return None


class SetPostModerationResHandler(BaseCmdHandler):

    async def handle(self, cmd: CheckModerationResult) -> None:
        """Set block moderation result"""
        moderator = PublicationModerator()
        cache = get_cache_engine()
        fetched_mcr = cache.get_ht_obj(cmd.pub_id)
        if fetched_mcr is None:
            h_logger.error("MCR expired or wasn`t created.")
            return None
        try:
            h_logger.debug(fetched_mcr)
            mcr = await moderator.mcr_from_json(fetched_mcr["mcr"])
            for k in mcr.blocks:
                report = cache.get_temp_obj(k)
                if report:
                    await moderator.set_mcr(k, fetched_mcr[k], report, mcr)
            await moderator.set_moderation_result(mcr)
        except ModerationError as err:
            h_logger.error(err)
            raise HandlerError from err
        except Exception as exp:
            h_logger.error(exp)
            raise HandlerError from exp
        for _ in range(moderator.events):
            self._uow.fetch_event(moderator.dump_event())
        return None


class UpdateHeaderHandler(BaseCmdHandler):
    """update header for current post."""

    async def handle(self, cmd: UpdateHeader) -> None:
        async with self._uow as operator:
            upd_task = self._task(
                    operator.storage.update_body(
                        uid=cmd.uid,
                        pub_id=cmd.pub_id,
                        body=cmd.payload,
                        ),
                    )
            try:
                await asyncio.gather(upd_task)
            except Exception as err:
                h_logger.error(err)
                raise HandlerError(err)


class UpdateBodyHandler(BaseCmdHandler):
    """update main body for current post."""

    async def handle(self, cmd: UpdateBody) -> None:
        async with self._uow as operator:
            upd_task = self._task(
                    operator.storage.update_body(
                        uid=cmd.uid,
                        pub_id=cmd.pub_id,
                        body=cmd.payload,
                        ),
                    )
            try:
                await asyncio.gather(upd_task)
            except Exception as err:
                h_logger.error(err)
                raise HandlerError(err)


class BeginPostModerationHandler(BaseCmdHandler):
    """ react on Task Accepted."""

    async def handle(self, cmd: StartModeration) -> None:
        """We`re waiting and react on StartModeration command.
            *mcr -> moderation_ctrl_block.
        """
        moderator = PublicationModerator()
        blocks = self._task(moderator.build_content_blocks(
            pub_id=cmd.pub_id,
            blocks=cmd.blocks,
            ))
        mcr = self._task(moderator.make_mcr(cmd.pub_id))
        tasks = (mcr, blocks)
        try:
            await asyncio.gather(*tasks)
        except Exception as err:
            h_logger.error(err)
            raise HandlerError(err)
        async with self._uow as operator:
            try:
                model = await operator.storage.get_post_by_uid(cmd.pub_id)
                upd_model = await moderator.set_on_moderation(model)
                await operator.storage.update_state(upd_model)
                await operator.commit()
            except (Exception, ModerationError) as err:
                await operator.rollback()
                h_logger.error(err)
                raise HandlerError from err
        for _ in range(moderator.events):
            self._uow.fetch_event(moderator.dump_event())
        return None


class SendToModerationHandler(BaseCmdHandler):

    async def handle(self, cmd: ModerateContent) -> None:
        try:
            fetch_content.apply_async(
                    (
                        cmd.mcode,
                        cmd.uid,
                        cmd.pub_id,
                        )
                    )
            return None
        except Exception as err:
            h_logger.error(err)
            raise HandlerError from err


class ModerationSuccessHandler(BaseCmdHandler):
    """react if PostAccepted event was produced."""

    async def handle(self, event: ModerationDoneSuccess) -> None:
        moderator = PublicationModerator()
        async with self._uow as operator:
            try:
                model = await operator.storage.get_post_by_uid(event.pub_id)
                upd_model = await moderator.accept_publication(model)
                await operator.storage.update_state(upd_model)
                await operator.commit()
            except Exception as err:
                h_logger.error(err)
                await operator.rollback()
                raise HandlerError from err
        for _ in range(moderator.events):
            self._uow.fetch_event(moderator.dump_event())
        h_logger.debug(self._uow._events)
        return None


class ModerationFailedHandler(BaseCmdHandler):
    """react if PostRejected event was produced."""

    async def handle(self, event: ModerationFailed) -> None:
        moderator = PublicationModerator()
        async with self._uow as operator:
            try:
                model = await operator.storage.get_post_by_uid(event.pub_id)
                upd_model = await moderator.reject_publication(model)
                await operator.storage.update_state(upd_model)
                await operator.commit()
            except Exception as err:
                h_logger.error(err)
                await operator.rollback()
                raise HandlerError from err
        for _ in range(moderator.events):
            self._uow.fetch_event(moderator.dump_event())
        return None
