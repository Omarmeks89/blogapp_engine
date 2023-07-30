from dataclasses import dataclass, field
from string import ascii_letters, digits
from random import choice
from enum import Enum
from typing import Union
from typing import Any

from .actions import ModerationRes, Serializable


SYMBOLS: list[str] = [*ascii_letters, *digits, "-", "_"]


__all__ = (
        "_ContentBlock",
        "ModerationControlBlock",
        "McodeSize",
        "generate_mcode",
        )


class McodeSize(int, Enum):
    """size constants for <generate mcode> func."""
    MIN_8S: int = 8
    MID_32S: int = 32
    MID_64S: int = 64
    MAX_128S: int = 128


def generate_mcode(*, symblos_cnt: int = McodeSize.MIN_8S) -> str:
    """generate unique random code for moderated block."""
    if symblos_cnt < 0 or symblos_cnt > McodeSize.MAX_128S:
        symblos_cnt = McodeSize.MIN_8S
    return "".join([choice(SYMBOLS) for _ in range(symblos_cnt)])


@dataclass
class _ContentBlock(Serializable):
    """mcode - random unique str as moderation key."""
    uid: str
    mcode: str
    pub_id: str
    payload: Any
    _state: ModerationRes = ModerationRes.NOT_SET

    @property
    def state(self) -> ModerationRes:
        return self._state


@dataclass
class ModerationControlBlock(Serializable):
    pub_id: str
    blocks: dict[str, Union[str, ModerationRes]] = field(default_factory=dict)

    def register_block(self, block: _ContentBlock) -> None:
        """register content block."""
        if block.uid not in self.blocks:
            self.blocks[block.uid] = self.blocks.get(block.uid, block.state)

    def set_moderation_result(self, block_id: str, result: str) -> None:
        """set each result after each block was moderated."""
        if self.blocks[block_id] is not ModerationRes.NOT_SET:
            raise Exception(f"Result for block: {block_id} is just set.")
        self.blocks[block_id] = result

    def done_success(self) -> bool:
        """return True if moderation was done with success."""
        results = []
        for v in self.blocks.values():
            results.append(
                True if v is ModerationRes.ACCEPTED.value else False
                )
        return all(results)
