import asyncio
import datetime
from typing import Any

from base_tools.exceptions import DBError, CacheError, ModerationError
from .services import mod_service
from .messages import DBerrorNotification, CacheErrorNotification


class FinalizeModerationHandler:
    """handler use current domain services
        to made work."""
    def __init__(self, uow: UOW) -> None:
        super().__init__(uow)

    async def handle(self, fin_cmd: Any) -> None:
        """Finalize Moderation."""
        async with self._uow as operator:
            moderbl = await operator.cache.get(fin_cmd.record_id)
            task = asyncio.create_task
            if moderbl is None:
                raise ModerationError("No moderation block found.")
            # should it be async?
            event, moderbl = mod_service.finalize_moderation(fin_cmd, moderbl)
            store_task = task(operator.storage.update(
                    fin_cmd.record_id,
                    moderbl
                    ))
            cache_task = task(operator.cache.remove(fin_cmd.record_id))
            tasks = (store_task, cache_task,)
            curr_group = asyncio.gather(*tasks)
            try:
                await curr_group
            except DBError as err:
                time = datetime.now()
                for task in tasks:
                    task.cancel()
                logger.error(err)
                if not operator.cache.get(fin_cmd.record_id):
                    await operator.cache.push(
                        moderbl.content_id,
                        moderbl,
                    )
                event = DBErrorNotification(
                    time=time,
                    error=err,
                    record_id=moderbl.content_id,
                    )
                self._uow.fetch_event(event)
                return None
            except CacheError as err:
                time = datetime.now()
                for task in tasks:
                    task.cancel()
                logger.error(err)
                self._uow.fetch_event(event=CacheErrorNotification(
                        time=time,
                        error=err,
                        record=moderbl.content_id,
                        )
                    )
                return None
            self._uow.fetch_event(event)
        return None


class BeginModerationHandler(BaseCmdHandler):
    """handler use current domain services
        to made work."""
    def __init__(self, uow: UOW) -> None:
        super().__init__(uow)

    async def handle(self, cmd: Any) -> None:
        """statr moderation."""
        async with self._uow as operator:
            task = asyncio.create_task
            content = operator.storage.load(cmd.content_id)
            mod_ctrl_record = mod_service.make_ctrl_record(content)
            c_blocks = mod_service.build_control_blocks(content)
            content.on_moderation()
            store_task = task(operator.storage.update(content))
            cache_task = task(
                operator.cache.push(
                    mod_ctrl_record.content_id,
                    mod_ctrl_record,
                    )
                )
            tasks = (store_task, cache_task,)
            curr_group = asyncio.gather(*tasks)
            try:
                await curr_group
            except (DBError, CacheError) as err:
                logger.error(err)
                for task in tasks:
                    task.cancel()
                return None
            for block in c_blocks:
                event = ContentBlockCreated(
                    id=mod_ctrl_record.content_id,
                    kind=block.kind,
                    content=block,
                    result=mstate.NOTSET,
                    )
                self._uow.fetch_event(event)
        return None


class LikeModerationHandler(BaseCmdHandler):

    def __init__(self, uow: UOW) -> None:
        super().__init__(uow)
