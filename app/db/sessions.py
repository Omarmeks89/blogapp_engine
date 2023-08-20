from enum import Enum
from typing import AsyncGenerator
from typing import Optional
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import TestDBSettings


__all__ = (
        "Session",
        "bootstrap_db",
        "engine",
        "get_db_session",
        )


db_settings = TestDBSettings()


engine = create_engine(
        db_settings.get_db_url(),
        echo_pool=db_settings.TEST_ECHO_POOL,
        pool_pre_ping=db_settings.TEST_POOL_PREPING,
        pool_size=db_settings.TEST_POOL_SZ,
        max_overflow=db_settings.TEST_POOL_OWF,
        pool_recycle=db_settings.TEST_POOL_RECL,
    )


Session = sessionmaker(
        engine,
        autocommit=db_settings.TEST_AUTOCM,
        autoflush=db_settings.TEST_AUTOFL,
        )


class DbBootstrapModes(int, Enum):
    TEST_REBUILD: int = 0
    PROG_NO_REBUILD: int = 1


async def get_db_session() -> AsyncGenerator:
    try:
        session: Session = Session()
        yield session
    finally:
        await session.close()


async def bootstrap_db(
        engine: Any,
        meta: MetaData,
        *,
        mode: DbBootstrapModes = DbBootstrapModes.TEST_REBUILD,
        run_test: bool = False,
        ) -> Optional[dict[str, list]]:
    if mode == mode.TEST_REBUILD:
        meta.drop_all(engine)
    meta.create_all(engine)
    return None
