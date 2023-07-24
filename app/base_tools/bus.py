import asyncio
from typing import MutableMapping as MMap

from handler_interfaces import BaseCmdHandler
from exceptions import BusError
from base_types import SysMsgT


class MsgBus:

    def __init__(self) -> None:
        self._h_map: MMap[str, BaseCmdHandler] = {}
        try:
            from collections import deque
            self._tasks: list[SysMsgT] = deque()
        except ImportError:
            raise BusError("Deque not found. ImpoerError.")

    def subscribe(self, item: SysMsgT, handler: BaseCmdHandler) -> None:
        key = self.make_key(item)
        self._h_map[key] = self._h_map.get(key, handler)

    def unsubscribe(self, item: SysMsgT) -> None:
        key = self.make_key(item)
        try:
            del self._h_map[key]
        except KeyError:
            pass

    @staticmethod
    def make_key(item: SysMsgT) -> str:
        return item.__name__

    async def fetch_events(self, handler: BaseCmdHandler) -> None:
        for t in handler.events:
            self._tasks.append(t)
        return None

    async def handle(self, item: SysMsgT) -> None:
        self._tasks.append(item)
        is_active = True
        while is_active:
            handler = None
            while self._tasks:
                t = self._tasks.pop()
                handler = self._h_map.get(type(t).__name__, None)
                if handler is None:
                    raise BusError("Unexpected handler.")
                task = asyncio.create_task(handler(item))
                await asyncio.gather(task)
            ft = asyncio.create_task(self.fetch_events(handler))
            await asyncio.gather(ft)
            if not self._tasks:
                is_active = False
        return None
