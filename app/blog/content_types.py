from dataclasses import dataclass


from base_tools.base_content import BaseContentPreset
from base_tools.base_moderation import _ContentBlock
from .types import TextBlock


@dataclass
class TextContent(BaseContentPreset):

    @classmethod
    def make_block(cls, mcode: str) -> _ContentBlock:
        """make block with a content for moderation."""
        return TextBlock(
                uid=cls.uid,
                mcode=mcode,
                payload=cls.body,
                )
