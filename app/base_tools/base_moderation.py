from dataclasses import dataclass, field
from string import ascii_letters, digits
from random import choice
from enum import Enum
from typing import Union

from .actions import ModerationRes, Serializable


SYMBOLS: list[str] = [*ascii_letters, *digits, "-", "_"]


__all__ = (
        "_ContentBlock",
        "ModerationControlRecord",
        "McodeSize",
        "generate_mcode",
        )


class McodeSize(int, Enum):
    """size constants for <generate mcode> func."""
    MIN_8S: int = 8
    MIN_16S: int = 16
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
    _state: ModerationRes = ModerationRes.NOT_SET

    @property
    def state(self) -> ModerationRes:
        return self._state


@dataclass
class ModerationControlRecord(Serializable):
    """MCR implementation. class that controlled
    moderation process."""
    pub_id: str
    act_dt: str
    exp_after_sec: int
    blocks: dict[str, Union[str, ModerationRes]] = field(default_factory=dict)
    reports: list[str] = field(default_factory=list)

    def finished(self) -> bool:
        return len(self.reports) == len(self.blocks)

    def register_block(self, block: _ContentBlock) -> None:
        """register content block."""
        if block.mcode not in self.blocks:
            self.blocks[block.mcode] = self.blocks.get(
                        block.mcode,
                        block.state,
                    )

    def mcode_registered(self, mcode: str) -> bool:
        """check external mcode on registration."""
        return mcode in self.blocks

    def set_moderation_result(
            self,
            mcode: str,
            res_state: str,
            report: str,
            ) -> None:
        """set each result after each block was moderated."""
        if self.blocks[mcode] != ModerationRes.NOT_SET:
            raise Exception(f"Result for block: {mcode} is just set.")
        self.blocks[mcode] = res_state
        self.reports.append(report)

    def done_success(self) -> bool:
        """return True if moderation was done with success."""
        results = []
        for v in self.blocks.values():
            results.append(
                True if v == ModerationRes.ACCEPTED.value else False
                )
        return all(results)
