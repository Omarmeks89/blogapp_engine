import asyncio
from datetime import datetime

from db.base_uow import BaseCmdHandler
from base_tools.exceptions import DBError, HandlerError, ModerationError
from .storage.models import BlogPost
from tasks.email import LOGIN, RECEIVER, send_email
from base_tools.base_moderation import generate_mcode, McodeSize
from base_tools.base_content import ContentRoles
from .content_types import TextContent
from .schemas.response_models import PublicationCreated
from .schemas.response_models import ContentSchema, set_schema
from .services import PublicationModerator
from cache import get_cache_engine
from .messages import (
        PostRejected,
        PostAccepted,
        StartModeration,
        SetModerationResult,
        CreateNewPost,
        NotifyAuthor,
        AddHeaderForPost,
        AddBodyForPost,
        SaveAllNewPostContent,
        UpdateHeader,
        UpdateBody,
        AddToCache,
        )


mod_service = None
ctime = datetime.now


class NotifyAuthorsCmdHandler(BaseCmdHandler):
    """let`s move it to notification service later."""

    async def handle(self, cmd: NotifyAuthor) -> None:
        """for bus test only."""
        try:
            send_email.delay(LOGIN, RECEIVER, cmd.msg)
        except Exception:
            pass
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
                await operator.rollback()
                raise HandlerError(err)
        add = AddToCache(skey=cmd.post.uid, obj=cmd.post.model_dump_json())
        self._uow.fetch_event(add)
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
            raise HandlerError(err)
        return None


class SetPostModerationResHandler(BaseCmdHandler):

    async def handle(self, cmd: SetModerationResult) -> None:
        """Set block moderation result"""
        moderator = PublicationModerator()
        cache = get_cache_engine()
        mcr = cache.get_mcr_obj(hkey=cmd.mcr_id, internal_key="mcr")
        if mcr is None:
            self._uow.fetch_event(
                    f"mcr {cmd.mcr_id} expired.",
                    )
            return None
        try:
            await moderator.set_moderation_result(
                    mcode=cmd.mcode,
                    state=cmd.state,
                    report=cmd.report,
                    mcr=mcr,
                    )
            cache.set_mcr_obj(
                    hkey=cmd.mcr_id,
                    internal_key="mcr",
                    obj=mcr.to_json(),
                    )
        except ModerationError as err:
            raise HandlerError from err
        except Exception:
            # CacheError here
            pass
        for _ in range(len(moderator.events)):
            self._uow.fetch_event(mod_service.dump_event())
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
                raise HandlerError(err)


class UpdateBodyHandler(BaseCmdHandler):
    """update main body for current post."""

    async def handle(self, cmd: UpdateBody) -> None:
        async with self._uow as operator:
            upd_task = self._task(
                    operator.storage.update_content_body(
                        uid=cmd.uid,
                        pub_id=cmd.pub_id,
                        body=cmd.payload,
                        ),
                    )
            try:
                await asyncio.gather(upd_task)
            except Exception as err:
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
        except ModerationError as err:
            raise HandlerError(err)
        async with self._uow as operator:
            try:
                model = await operator.storage.get_post_by_id(cmd.pub_id)
                upd_model = await moderator.set_on_moderation(model)
                await operator.storage.update_state(upd_model)
                await operator.commit()
            except (DBError, ModerationError) as err:
                await operator.rollback()
                raise HandlerError from err
        for _ in range(len(moderator.events)):
            self._uow.fetch_event(moderator.dump_event())
        return None


class FixPostAcceptedHandler(BaseCmdHandler):
    """react if PostAccepted event was produced."""

    async def handle(self, event: PostAccepted) -> None:
        moderator = PublicationModerator()
        async with self._uow as operator:
            try:
                model = await operator.storage.get_post_by_id(event.pub_id)
                upd_model = await moderator.accept_publication(model)
                await operator.storage.update_state(upd_model)
                await operator.commit()
            except DBError as err:
                await operator.rollback()
                raise HandlerError from err
        for _ in range(len(moderator.events)):
            self._uow.fetch_event(moderator.dump_event())
        return None


class FixPostRejectedHandler(BaseCmdHandler):
    """react if PostRejected event was produced."""

    async def handle(self, event: PostRejected) -> None:
        moderator = PublicationModerator()
        async with self._uow as operator:
            try:
                model = await operator.storage.get_post_by_id(event.pub_id)
                upd_model = await moderator.reject_publication(model)
                await operator.storage.update_state(upd_model)
                await operator.commit()
            except DBError as err:
                await operator.rollback()
                raise HandlerError from err
        for _ in range(len(moderator.events)):
            self._uow.fetch_event(moderator.dump_event())
        return None
