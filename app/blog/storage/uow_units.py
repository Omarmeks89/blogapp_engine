from typing import Any

from base_tools.base_types import SysMsgT
from db.base_uow import BaseUOW, UOW_FSM
from db.base_repositories import Repository


class ModerationUOW(BaseUOW):

    _work_state: UOW_FSM = UOW_FSM

    def __init__(
            self,
            repo: Repository,
            session: Any,
            ) -> None:
        super().__init__(repo, session)

    async def __aexit__(
            self,
            exc_type: Exception,
            exc_value: Any,
            traceback: Any,
            ) -> None:
        if (
                exc_type is not None
                and self._state is type(self)._work_state.TRANSACTION
                ):
            self._curr_ses.rollback()
            self._state = type(self)._work_state.ROLLEDBACK
            # needed logging
        else:
            if self._state is type(self)._work_state.TRANSACTION:
                self._curr_ses.commit()
                self._state = type(self)._work_state.COMMITED
        return await super().__aexit__(
                exc_type,
                exc_value,
                traceback,
                )

    @property
    def storage(self) -> Repository:
        return self._repository

    def fetch_event(self, event: SysMsgT) -> None:
        if event is None:
            return None
        self._events.append(event)
