from enum import Enum
from typing import ClassVar
from typing import Optional


class Author_FSM(str, Enum):
    """base FSM for authors."""
    CREATED: str = "created"
    ACTIVE: str = "active"
    BANNED: str = "banned"
    DELETED: str = "deleted"


class Roles(int, Enum):
    """base roles for app users."""
    AUTHOR: int = 0
    ADMIN: int = 256


class Author:

    _fsm: ClassVar[Author_FSM] = Author_FSM

    def __init__(
            self,
            uid: str,
            login: str,
            email: str,
            hpasswd: str,
            *,
            state: Optional[str] = None,
            role: Optional[str] = None,
            ) -> None:
        self.uid = uid
        self.login = login
        self.email = email
        self._hpasswd = hpasswd
        self._state = state or type(self)._fsm.CREATED
        self._role = role or Roles.AUTHOR

    @property
    def hpasswd(self) -> str:
        return self._hpasswd

    @property
    def role(self) -> Roles:
        return self._role

    @property
    def state(self) -> Author_FSM:
        return self._state

    def activate(self) -> None:
        """if email confirmed."""
        if self.state is type(self)._fsm.CREATED:
            self.state = type(self)._fsm.ACTIVE

    def ban(self) -> None:
        if self.state is type(self)._fsm.ACTIVE:
            self.state = type(self)._fsm.BANNED

    def unban(self) -> None:
        if self.state is type(self)._fsm.BANNED:
            self.state = type(self)._fsm.ACTIVE

    def mark_as_deleted(self) -> None:
        self.state = type(self)._fsm.DELETED
