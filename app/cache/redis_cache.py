import redis
import logging
import weakref
from typing import Generic
from typing import TypeVar
from typing import Any
from typing import Optional
from typing import ClassVar
from typing import Callable
from typing import NoReturn
from typing import Type
# needed weakvaedict
from typing import MutableMapping as MMap
from enum import Enum
from abc import ABC, abstractmethod


AnyItemT = TypeVar("AnyItemT", bound=Any)
RefT = TypeVar("RefT", bound=weakref.ReferenceType)
CEngineT = TypeVar("CacheEngineT", bound="AbstractCacheEngine", covariant=True)
S = TypeVar("S", bound="AbstractCacheSession", covariant=True)


logger = logging.getLogger("CacheLogger")
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class CacheSessionExpired(Exception):
    """session obj was removed from map."""
    pass


class DublicatedReferenceError(Exception):
    """try to subscribe same obj twice."""
    pass


class CacheDB(int, Enum):
    DEFNO: int = 0


class AbstractCacheSession(ABC, Generic[CEngineT]):

    _map: ClassVar[MMap]

    @abstractmethod
    async def connect(self, *, db: CacheDB = CacheDB.DEFNO) -> CEngineT: pass

    @classmethod
    @abstractmethod
    def reconfigure(cls: Type[S], host: str, port: int, db: CacheDB) -> S: pass


class AbstractCacheEngine(ABC):
    """interface for abstract cache system."""
    ...


class CacheSession(AbstractCacheSession):

    _map: ClassVar[MMap[int, Any]] = {}

    @classmethod
    def _register_connection(cls, key: str, conn: RefT) -> None:
        if key in cls._map:
            raise DublicatedReferenceError
        cls._map[key] = conn

    @classmethod
    def _get_connection(cls, key: str) -> Optional[Any]:
        return cls._map.get(key, None)

    @classmethod
    def _key_registered(cls, key: str) -> bool:
        return key in cls._map

    @classmethod
    def reconfigure(
            cls: Type[S],
            host: str,
            port: int,
            db: CacheDB,
            *,
            decode: bool = False
            ) -> "CacheSession":
        return cls(host, port, db, decode=decode)

    def __init__(
            self,
            host: str,
            port: int,
            db: CacheDB,
            *,
            decode: bool = False,
            ) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._decode = decode

    def __repr__(self) -> str:
        return (
            f"{self._host}:{self._port}/{self._db_no}.decode={self._decode}\n"
            )

    def _weakref_callback(self, link: RefT) -> NoReturn:
        raise CacheSessionExpired(link)

    @classmethod
    def _run_clearing(cls) -> None:
        to_remove = []
        for k in cls._map:
            if weakref.getweakrefcount(cls._map[k]()):
                continue
            to_remove.append(cls._map[k])
        for r in to_remove:
            del r

    def _del_connection(self) -> Callable[[None], None]:
        """remove connection if no referenses."""
        _cleaner = self._run_clearing

        def _remove_wr() -> None:
            """on_shutdown method that called inside
            a CacheEngine on connection end."""
            nonlocal _cleaner
            _cleaner()

        return _remove_wr

    def connect(self) -> "CacheEngine":
        """create connection to Redis."""
        conn: Optional[Any] = None
        key = self.__repr__()
        if self._key_registered(key):
            ref = self._get_connection(key)
            return CacheEngine(ref(), on_shutdown=self._del_connection())
        conn = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                decode_responses=self._decode
                )
        ref = weakref.ref(conn, self._weakref_callback)
        self._register_connection(key, ref)
        return CacheEngine(conn, on_shutdown=self._del_connection())


class CacheEngine(AbstractCacheEngine):
    """engine base sample."""

    def __init__(
            self,
            conn: Any,
            *,
            on_shutdown: Callable[[RefT], Callable[[None], None]],
            ) -> None:
        self._conn = conn
        self._on_shutdown = on_shutdown

    def close(self) -> None:
        try:
            del self._conn
            self._on_shutdown()
        except Exception as err:
            msg = f"Raised from {self.close}: {err=}"
            logger.debug(msg)
