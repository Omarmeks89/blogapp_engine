from dataclasses import dataclass


from base_tools.base_content import BaseContentPreset, ContentTypes
from base_tools.base_content import ContentRoles
from base_tools.base_moderation import _ContentBlock
from base_tools.base_moderation import McodeSize, generate_mcode
from base_tools.actions import ModeratableBlock


@dataclass
class TextBlock(ModeratableBlock, _ContentBlock):
    """type for text content block representation."""

    def __post_init__(self) -> None:
        self._kind = ContentTypes.TEXT


def make_text_block(
        uid: str,
        pub_id: str,
        *,
        codelen: int = McodeSize.MIN_8S,
        ) -> _ContentBlock:
    """func for creation text block
    from StartModeration cmd inside a service."""
    code = generate_mcode(symblos_cnt=codelen)
    return TextBlock(
            uid=uid,
            pub_id=pub_id,
            mcode=code,
            )


@dataclass
class TextContent(BaseContentPreset):

    def __post_init__(self) -> None:
        """sex exact content type."""
        self._kind = ContentTypes.TEXT

    @classmethod
    def make_block(cls, mcode: str) -> _ContentBlock:
        """make block with a content for moderation
        Useful when we try restart moderation after fail."""
        return TextBlock(
                uid=cls.uid,
                pub_id=cls.pub_id,
                mcode=mcode,
                )


@dataclass
class Header(TextContent):

    def __post_init__(self) -> None:
        """specify role."""
        super().__post_init__(self)
        self._role = ContentRoles.HEADER


@dataclass
class Body(TextContent):

    def __post_init__(self) -> None:
        """specify role."""
        super().__post_init__(self)
        self._role = ContentRoles.BODY
