import logging
from enum import Enum
from typing import TypeVar
from typing import NewType

import httpx
import celery

from .tasks import celery_app
from .settings import ModerationAPISettings


TaskT = TypeVar("TaskT", bound=celery.Task, contravariant=True)
Report = NewType("Report", object)
ModerationService = NewType("ModerationService", object)
api_setup = ModerationAPISettings()

_logger_ = logging.getLogger(__name__)
_logger_.setLevel(logging.DEBUG)
str_handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
str_handler.setFormatter(formatter)
_logger_.addHandler(str_handler)


# _logger_.debug(api_setup)


class BodyFetchingError(Exception):
    """error on API connection."""
    pass


class InvalidCredentials(Exception):
    """invalid api_secret or api_num."""
    pass


class TimeUnit(float, Enum):
    """TimeUnits repr in seconds."""
    SECOND: float = 1.0
    MINUTE: float = 60.0
    HOUR: float = 3600.0


class TimeoutSec(float, Enum):
    DEF_TOUT: float = 2.0
    LONG_RESP_TOUT: float = 10.0


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3})
def fetch_content(self: TaskT, mcode: str, cont_id: str, pub_id: str) -> None:
    """test impl with httpx."""
    params = {"rkey": mcode, "c_uid": cont_id, "pub_id": pub_id}
    addr_url = "http://localhost:8000/main/moderation/posts"
    with httpx.Client(timeout=TimeoutSec.DEF_TOUT) as client:
        try:
            responce = client.get(addr_url, params=params)
            responce.raise_for_status()
        except httpx.HTTPError as err:  # it`s a base error class
            _logger_.error(
                f"API raised: {err.response.status_code} "
                f"on url: {err.request.url}"
                )
            if err.response.status_code == 404:
                raise BodyFetchingError(
                    f"Maybe error in url: {err.request.url}"
                    )
            raise self.retry(exc=err, contdown=TimeUnit.MINUTE)
        moderate.apply_async((responce.json(), mcode, pub_id))


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3})
def moderate(self: TaskT, data: bytes, mcode: str, pub_id: str) -> None:
    """mock moderation process."""
    serv_url = "https://api.sightengine.com/1.0/text/check.json"
    _logger_.debug(f"Data: {data}")
    req = {
        "text": data[mcode],
        "mode": "ml",
        "lang": "en",
        "api_user": api_setup.api_user,
        "api_secret": api_setup.api_secret,
    }
    with httpx.Client(timeout=TimeoutSec.DEF_TOUT) as client:
        try:
            resp = client.post(serv_url, data=req)
            resp.raise_for_status()
        except httpx.ConnectTimeout as err:
            _logger_.error(err)
            raise self.retry(exc=err, contdown=TimeUnit.MINUTE)
        except httpx.NetworkError as err:
            msg = (
                f"ERR: code = {err.response.status_code}, "
                f"url = {err.request.url}."
                )
            _logger_.error(msg)
            raise InvalidCredentials(msg)
        _logger_.debug(resp.text)
        send_moderation_result.apply_async(("report", mcode, pub_id, "accepted"))


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3})
def send_moderation_result(
        self: TaskT,
        report: Report,
        mcode: str,
        pub_id: str,
        state: bool,
        ) -> None:
    """send moderation result to service."""
    url = "http://localhost:8000/main/moderation/posts/set"
    params = {"pub_id": pub_id, "c_uid": mcode}
    with httpx.Client(
            timeout=TimeoutSec.DEF_TOUT,
            follow_redirects=True,
            ) as client:
        try:
            data = {
                    "mcr_id": pub_id,
                    "mcode": mcode,
                    "state": state,
                    "report": report,
                    }
            resp = client.post(url, json=data, data=params)
            resp.raise_for_status()
        except httpx.HTTPError as err:
            _logger_.error(
                f"API raised: {err.response.status_code} "
                f"on url: {err.request.url}"
                )
            raise self.retry(exc=err, contdown=TimeUnit.MINUTE)
