import logging
from datetime import timedelta
from datetime import datetime
from typing import Any

from jose import jwt
from jose import JWTError
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer

from settings import TestSettings


settings = TestSettings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")
logger = logging.getLogger(__name__)


def create_access_token(
        data: dict[str: Any],
        exp_time: timedelta,
        ) -> str:
    expire = datetime.utcnow() + exp_time
    data.update({"exp": expire})
    jwt_token = jwt.encode(
            data,
            settings.secret,
            settings.crypt_alg,
            )
    return jwt_token


async def get_uid_from_token(token: str = Depends(oauth2_scheme)) -> str:
    exp = HTTPException(
            status_code=401,
            detail="User unauthorized.",
            )
    try:
        payload = jwt.decode(
                token,
                settings.secret,
                algorithms=[settings.crypt_alg, ],
                )
        uid = payload.get("sub", None)
        if not uid:
            raise exp
        return uid
    except JWTError as err:
        logger.error(f"Expected {err=}")
        raise exp
