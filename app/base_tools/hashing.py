from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from typing import TypeVar
from typing import Generic


HashedStr = TypeVar("HashedStr", bound=str, covariant=True)
PlainStr = TypeVar("PlainStr", bound=str, contravariant=True)


class CryptSchema(str, Enum):
    """base crypt schemas fro qiuck using."""
    SHA256_CRYPT: str = "sha256_crypt"
    MD5_CRYPT: str = "md5_crypt"
    DES_CRYPT: str = "des_crypt"
    LDAP_SLT_MD5: str = "ldap_salted_md5"


class AbcCryptographer(ABC, Generic[PlainStr, HashedStr]):
    """represent base cryptographer interface
    for most common purposes."""

    @abstractmethod
    def hash(
            self,
            item: PlainStr,
            *,
            scheme: Optional[str] = None,
            ) -> HashedStr: pass

    @abstractmethod
    def verify(self, item: PlainStr, hashed: HashedStr) -> bool: pass

    @abstractmethod
    def update_alg_schema(
            self,
            *,
            rounds_cnt: Optional[int] = None,
            salt_size: Optional[int] = None,
            ) -> None: pass

    @abstractmethod
    def needs_update(self, hashed: HashedStr) -> bool: pass
