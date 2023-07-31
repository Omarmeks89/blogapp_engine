from sqlalchemy import MetaData, Table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from enum import Enum
from typing import AsyncGenerator
from typing import Optional

from settings import DBSettings
from base_tools.base_models import Model
from base_tools.exceptions import BootstrapError

settings = DBSettings()
metadata = MetaData()


async_engine = create_async_engine(
        settings.DB_SETUP,
        echo=settings.ECHO,
        connect_args={"server_settings": {"jit": "off"}},
        pool_pre_ping=settings.PREPING,
        query_cache_size=settings.QC_SIZE,
    )


class DbBootstrapModes(int, Enum):
    TEST_REBUILD: int = 0
    PROG_NO_REBUILD: int = 1


async_session = AsyncSession(async_engine, expire_on_commit=False)


class TablesCatalogue:
    """use for add models to
    bootstrap db."""

    from typing import Generator, Type

    def __init__(self) -> None:
        self._cat: dict[str, Table] = {}

    @property
    def not_set(self) -> bool:
        return self._cat == {}

    def add_table(self, tkey: str, model: Type[Model], table: Table) -> None:
        """model should be a class, table - object."""
        self._cat[tkey] = self._cat.get(tkey, table)

    def remove_table(self, table_k: str) -> None:
        if self._cat.get(table_k):
            del self._cat[table_k]

    def tables(self) -> Generator:
        return (v for _, v in self._cat.items())


async def get_db_session() -> AsyncGenerator:
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()


async def bootstrap_db(
        engine: AsyncSession,
        metadata: MetaData,
        tables: TablesCatalogue,
        *,
        mode: DbBootstrapModes = DbBootstrapModes.TEST_REBUILD,
        run_test: bool = False,
        ) -> Optional[dict[str, list]]:
    """bootstrap db. Goes to 'on_startup()'."""
    try:
        from sqlalchemy.orm import registry
    except ImportError as err:
        raise BootstrapError from err

    async with engine.begin() as conn:
        if mode == mode.TEST_REBUILD:
            await conn.run_sync(metadata.drop_all())

        # creale_all check before creation, so no collapse here.
        await conn.run_sync(metadata.create_all())

        if tables.not_set:
            msg = f"{type(tables).__name__} not set. No models to get."
            raise BootstrapError(msg)

        mapper = registry()

        for model, table in tables.tables:
            mapper.map_imperatively(model, table)

        if run_test:
            # run test for look at created tables data
            report: dict[str, list] = {}
            try:
                from sqlalchemy import inspect
            except ImportError as err:
                raise BootstrapError from err

            for model, _ in tables.tables:
                mod_info = inspect(model)
                report[model.__name__] = report.get(
                    model.__name__,
                    mod_info.all_orm_descriptors.keys(),
                    )
            return report
        return None
