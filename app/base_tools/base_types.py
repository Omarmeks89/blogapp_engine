from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeAlias, Union, TypeVar


__all__ = (
        "SysMsgT",
        "SimpleAction",
        "_PublicationStatistic",
        )


SysMsgT: TypeAlias = Union["Event", "Command"]
IntervalT = TypeVar("IntervalT", bound=datetime,  contravariant=True)
PubAttr: str = "pub"


@dataclass
class SimpleAction:
    """simple template to represent any action."""
    producer: str
    pub_id: str
    action_dt: datetime


@dataclass
class Event:
    """root Event class."""
    pass


@dataclass
class Command:
    """root class for commands."""
    pass


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
