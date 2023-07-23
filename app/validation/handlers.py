import asyncio


from base_tools.handler_interfaces import BaseCmdHandler
from base_tools.exceptions import DBError, HandlerError, ValidationError
from .services import validator
from .messages import CheckAuthorPermissions
from .messages import ValidateNewLike


class CheckAuthorPermissionsHandler(BaseCmdHandler):

    async def handle(self, cmd: CheckAuthorPermissions) -> None:
        """CheckAuthorPermissions is a facade."""

        async with self._uow as operator:
            event = None
            user = asyncio.gather(self._task(
                operator.storage.load(cmd.author_id),
                ))
            try:
                await user
            except DBError as err:
                raise HandlerError from err
            event = validator.get_permissions(user, cmd)
            self._uow.fetch_event(event)
        return None


class LikeValidationHandler(BaseCmdHandler):
    """This is for validation service i think..."""

    async def handle(self, new_like_cmd: ValidateNewLike) -> None:
        """moderate/validate new like to post."""
        async with self._uow as operator:
            post = await operator.cache.get(new_like_cmd.post_id)
            valid_res = self._task(
                validator.validate_action(new_like_cmd, post),
                )
            try:
                await asyncio.gather(valid_res)
            except ValidationError as err:
                raise HandlerError from err
            for _ in len(validator.events) - 1:
                self._uow.fetch_event(validator.dump_event())
        return None
