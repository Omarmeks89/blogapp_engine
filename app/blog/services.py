from collections import deque
from typing import TypeVar
from typing import TypeAlias
from typing import cast
from typing import Optional
from typing import Callable
from datetime import datetime

from base_tools.exceptions import ModerationError, PublicationError
from base_tools.base_content import BasePublication, ContentTypes
from base_tools.base_moderation import _ContentBlock, ModerationControlRecord
from base_tools.base_moderation import generate_mcode
from base_tools.actions import ModerationRes
from base_tools.base_types import SysMsgT
from .messages import ModerationFailed, ModerationDoneSuccess, LockContent
from .messages import ModerateContent, RegisterMCR, DeleteMCR, UpdateMCR
from .content_types import TextBlock
from base_tools.actions import JSONFmt


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
    def events(self) -> int:
        """get events count"""
        return len(self._events)

    def dump_event(self) -> SysMsgT:
        """dump event to next handler."""
        if self._events:
            return self._events.popleft()

    def _grab_events(self) -> Callable[[SysMsgT], None]:
        _obj = self

        def _set_event_from_model(event: SysMsgT) -> None:
            nonlocal _obj
            if hasattr(_obj, "_events"):
                _obj._events.append(event)
                return None
            raise Exception(f"{_obj} haven`t attr <'_events'>.")

        return _set_event_from_model

    async def set_moderation_result(
            self,
            mcr: ModerationControlRecord
            ) -> None:
        """Need to parse SetModerationResult."""
        if mcr.finished():
            if mcr.done_success():
                self._events.append(
                        ModerationDoneSuccess(pub_id=mcr.pub_id),
                        )
            else:
                self._events.append(
                    ModerationFailed(
                        pub_id=mcr.pub_id,
                        reasons=mcr.reports,
                        ),
                    )
            rem = DeleteMCR(pub_id=mcr.pub_id)
            self._events.append(rem)
        else:
            upd = UpdateMCR(skey=mcr.pub_id, obj=mcr.to_json())
            self._events.append(upd)
        return None

    async def set_mcr(
            self,
            mcode: str,
            state: ModerationRes,
            report: str,
            mcr: ModerationControlRecord
            ) -> None:
        try:
            mcr.set_moderation_result(mcode, state, report)
        except Exception:
            # add event for support
            pass
        return None

    @staticmethod
    async def mcr_from_json(json_str: JSONFmt) -> ModerationControlRecord:
        return ModerationControlRecord.from_json(json_str)

    async def make_mcr(
            self,
            pub_id: str,
            ) -> ModerationControlRecord:
        """create control block for results checking."""
        if not self._blocks:
            raise ModerationError("No content blocks created.")
        act_dt = datetime.utcnow()
        mcr = ModerationControlRecord(
                pub_id=pub_id,
                act_dt=act_dt.strftime("%Y%m%d%H%M%S"),
                exp_after_sec=3600,
                )
        for block in self._blocks:
            mcr.register_block(block)
        cmd = RegisterMCR(
                skey=mcr.pub_id,
                obj=mcr.to_json(),
                blocks=mcr.blocks,
                )
        to_lock = LockContent(
                content=[{"c_uid": k.uid, "lock": 1} for k in self._blocks],
                )
        for c in (cmd, to_lock):
            self._events.append(c)
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
            model.moderate(self._grab_events())
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
            model.accept(self._grab_events())
            return cast(PubVT, model)
        except PublicationError as err:
            raise ModerationError(err)

    async def reject_publication(
            self,
            model: PubCV,
            *,
            reasons: Optional[list[str]] = None,
            ) -> PubVT:
        """fetch event from model.
        Model raised PostRejected.
        Return Model back."""
        try:
            model.decline(self._grab_events(), reasons=reasons)
            return cast(PubVT, model)
        except PublicationError as err:
            raise ModerationError(err)
