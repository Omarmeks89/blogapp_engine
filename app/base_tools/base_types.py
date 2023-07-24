from dataclasses import dataclass, field
from pathlib import Path
from datetim import datetime
from typing import TypeAlias, Union, Literal

from .actions import ModerationRes, _Serializable


LinkT: TypeAlias = Union[Path, str]
PubAttr = Literal["pub"]


@dataclass
class _ContentBlock(_Serializable):
    """mcode - random unique str as moderation key."""
    id: str
    mcode: str
    pub_id: str
    link: LinkT
    _state: str = field(default_factory=str)

    def __post_init__(self) -> None:
        self._state = ModerationRes.NOT_SET

    @property
    def state(self) -> ModerationRes:
        return self._state


@dataclass
class _SimpleAction:
    """simple template to represent any action."""
    producer: str
    pub_id: str
    action_dt: datetime


@dataclass
class _PublicationStatistic:
    """base representation."""
    pub_id: str
    likes: int = field(default_factory=int)
    dislikes: int = field(default_factory=int)

    def __post_init__(self) -> None:
        """auto set NULL on __init__ for all numeric attrs."""
        for k, v in self.__dict__.items():
            if k.startswith(PubAttr):
                continue
            self.__dict__[k] = 0
