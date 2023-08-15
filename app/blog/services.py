from collections import deque
from typing import TypeVar
from typing import TypeAlias
from typing import cast

from base_tools.exceptions import ModerationError, PublicationError
from base_tools.base_content import BasePublication, ContentTypes
from base_tools.base_moderation import _ContentBlock, ModerationControlRecord
from base_tools.base_moderation import generate_mcode
from base_tools.actions import ModerationRes
from base_tools.base_types import SysMsgT
from .messages import ModerationFailed, ModerationDoneSuccess, AddToCache
from .messages import ModerateContent
from .content_types import TextBlock


PubCV = TypeVar("PubCV", bound=BasePublication, contravariant=True)
PubVT = TypeVar("PubVT", bound=BasePublication, covariant=True)
Block: TypeAlias = _ContentBlock


class PublicationModerator:
    """service class that handle income
    commands and events and set needed model
    state depend on command / event type."""

    def __init__(self) -> None:
        self._events: deque[SysMsgT] = deque()
        self._blocks: deque[Block] = deque()

    @property
    def blocks_set(self) -> bool:
        return self._blocks != []

    @property
    def events(self) -> list[SysMsgT]:
        """get events count"""
        return list(self._events)

    def dump_event(self) -> SysMsgT:
        """dump event to next handler."""
        if self._events:
            return self._events.popleft()

    async def set_moderation_result(
            self,
            mcode: str,
            state: ModerationRes,
            report: str,
            mcr: ModerationControlRecord
            ) -> None:
        """Need to parse SetModerationResult."""
        try:
            mcr.set_moderation_result(mcode, state, report)
            # if all blocks returned from moderation.
            if mcr.finished():
                if mcr.done_success():
                    self._events.append(
                            ModerationDoneSuccess(pub_id=mcr.pub_id),
                            )
                else:
                    reports = [report for report in mcr.reports]
                    self._events.append(
                        ModerationFailed(pub_id=mcr.pub_id, reasons=reports),
                        )
            return None
        except Exception as err:
            raise ModerationError(
                    f"{type(self).__name__}:{__name__} failed.\n"
                    f"\tTrapped Exception: {err}.\n"
                    )

    async def make_mcr(
            self,
            pub_id: str,
            ) -> ModerationControlRecord:
        """create control block for results checking."""
        if not self._blocks:
            raise ModerationError("No content blocks created.")
        mcr = ModerationControlRecord(pub_id=pub_id)
        for block in self._blocks:
            # mcr set uid as block.mcode
            mcr.register_block(block)
        cmd = AddToCache(skey=mcr.pub_id, obj=mcr.to_json())
        self._events.append(cmd)
        return mcr

    async def build_content_blocks(
            self,
            pub_id: str,
            blocks: dict[str, ContentTypes],
            ) -> None:
        """create ContentBlocks from blocks = {uid: kind}."""
        for b_uid, kind in blocks.items():
            match kind:
                case ContentTypes.TEXT:
                    block = TextBlock(
                            uid=b_uid,
                            mcode=generate_mcode(),
                            pub_id=pub_id,
                        )
                    self._blocks.append(block)
                    cmd = ModerateContent(
                            uid=b_uid,
                            mcode=block.mcode,
                            pub_id=pub_id,
                            )
                    self._events.append(cmd)
                case _:
                    pass
        return None

    async def set_on_moderation(
            self,
            model: PubCV,
            ) -> PubVT:
        """invariant model. Return model to save in db.
        After Model have state MODERATION."""
        try:
            model.moderate()
            for event in model.events:
                self._events.append(event)
            return cast(PubVT, model)
        except PublicationError as err:
            raise ModerationError(err)

    async def accept_publication(
            self,
            model: PubCV,
            ) -> PubVT:
        """fetch event from model.
        Model raised PostAccepted.
        Return Model back."""
        try:
            model.accept()
            for event in model.events:
                self._events.append(event)
            return cast(PubVT, model)
        except PublicationError as err:
            raise ModerationError(err)

    async def reject_publication(
            self,
            model: PubCV,
            ) -> PubVT:
        """fetch event from model.
        Model raised PostRejected.
        Return Model back."""
        try:
            model.decline()
            for event in model.events:
                self._events.append(event)
            return cast(PubVT, model)
        except PublicationError as err:
            raise ModerationError(err)
