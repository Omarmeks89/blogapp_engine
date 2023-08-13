from .redis_cache import CacheSession, CacheEngine
from settings import CacheSettings


setup = CacheSettings()
Cache = CacheSession(
        host=setup.CHOST,
        port=setup.CPORT,
        db=setup.DEFDBNO,
        decode=setup.RESP_DEC,
        )


def get_cache_engine() -> CacheEngine:
    return Cache.connect()
