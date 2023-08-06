import asyncio
from typing import MutableMapping as MMap
from typing import Generator
from typing import Type
from typing import TypeVar
from typing import Protocol
from collections import deque

from .exceptions import BusError
from .base_types import SysMsgT


HandlerT = TypeVar("HandlerT", bound="HandlerProto", contravariant=True)
BT = TypeVar("BT", bound="MsgBus", covariant=True)


class HandlerProto(Protocol):
    @property
    def events(self) -> Generator: pass

    async def handle(self, cmd: SysMsgT) -> None: pass


class MsgBus:

    _map: MMap[str, HandlerT] = {}

    @classmethod
    def subscribe(cls, item: Type[SysMsgT], handler: HandlerT) -> None:
        key = cls.make_key(item)
        cls._map[key] = cls._map.get(key, handler)
        print(cls._map)

    @classmethod
    def unsubscribe(cls, item: Type[SysMsgT]) -> None:
        key = cls.make_key(item)
        try:
            del cls._map[key]
        except KeyError:
            pass

    @classmethod
    def is_set(cls) -> bool:
        return cls._map != {}

    @classmethod
    def get_bus(cls: BT) -> BT:
        if cls._map:
            return cls(cls._map)
        raise Exception("Can`t create empty bus.")

    def __init__(self, h_map: MMap[str, HandlerT]) -> None:
        self._h_map = h_map

    @staticmethod
    def make_key(item: Type[SysMsgT]) -> str:
        return item.__name__

    async def fetch_events(self, hnd: HandlerT, tasks: deque[SysMsgT]) -> None:
        for t in hnd.events:
            tasks.append(t)
        return None

    async def handle(self, item: SysMsgT) -> None:
        tasks: deque[SysMsgT] = deque()
        tasks.append(item)
        is_active = True
        while is_active:
            handler = None
            while tasks:
                t = tasks.popleft()
                handler = self._h_map.get(type(t).__name__, None)
                if handler is None:
                    raise BusError("Unexpected handler.")
                task = asyncio.create_task(handler.handle(t))
                await asyncio.gather(task)
            ft = asyncio.create_task(self.fetch_events(handler, tasks))
            await asyncio.gather(ft)
            if not tasks:
                is_active = False
        return None
