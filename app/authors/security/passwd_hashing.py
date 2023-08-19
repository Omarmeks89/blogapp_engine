import logging
from typing import Optional
from pathlib import Path

from passlib.context import CryptContext

from base_tools.hashing import AbcCryptographer, CryptSchema
from base_tools.hashing import HashedStr, PlainStr


logger = logging.getLogger("PASS_CRYPT")


class PasslibCrypt(AbcCryptographer):

    def __init__(
            self,
            *,
            schemes: Optional[list[CryptSchema]] = None,
            deprecated: Optional[list[CryptSchema]] = None,
            build_from_path: Optional[Path] = None,
            ) -> None:
        if build_from_path:
            # remember how to Path()...
            self._ctx = CryptContext.from_path(build_from_path)
        else:
            _schm = schemes or [CryptSchema.SHA256_CRYPT.value, ]
            logger.debug(_schm)
            _dpr = deprecated or []
            self._ctx = CryptContext(
                    schemes=_schm,
                    deprecated=_dpr,
                    )

    def hash(
            self,
            passwd: PlainStr,
            *,
            scheme: Optional[CryptSchema] = None,
            ) -> HashedStr:
        """hash current passwd."""
        if scheme:
            try:
                return self._ctx.hash(passwd, scheme=scheme)
            except KeyError as err:
                logger.error(err)
                raise Exception(f"Invalid {scheme=}")
        else:
            return self._ctx.hash(passwd)

    def verify(self, passwd: PlainStr, hashed: HashedStr) -> bool:
        if passwd and hashed:
            return self._ctx.verify(passwd, hashed)
        raise Exception("Empty credentials: {passwd=} | {hashed=}")

    def update_alg_schema(
            self,
            *,
            rounds_cnt: Optional[int] = None,
            salt_size: Optional[int] = None,
            ) -> None:
        """NotImplemented."""
        ...

    def needs_update(self, hashed: HashedStr) -> bool:
        return self._ctx.needs_update(hashed)
