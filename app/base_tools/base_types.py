from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias, Union

from .actions import ModerationRes, _Serializable


LinkT: TypeAlias = Union[Path, str]


@dataclass
class _ContentBlock(_Serializable):
    """mcode - random unique str as moderation key."""
    id: str
    mcode: str
    pub_id: str
    link: LinkT
    state: str = field(default_factory=str)

    def __post_init__(self) -> None:
        self.state = ModerationRes.NOT_SET
