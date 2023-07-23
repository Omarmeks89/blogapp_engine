from dataclasses import dataclass
from typing import MutableMapping as MMap

from base_tools.base_types import _ContentBlock, LinkT
from base_tools.actions import _Moderatable, _Serializable


@dataclass
class TextContent(_Moderatable, _ContentBlock):
    """type for text content block representation."""
    link: LinkT = ""


@dataclass
class PictureContent(_Moderatable, _ContentBlock):
    """type for image content representation."""
    pass


@dataclass
class ModerationControlRecord(_Serializable):
    """base MCR implementation."""
    pub_id: str
    blocks: MMap[str, bool]
