import logging
import json
from enum import Enum
from typing import TypeVar
from typing import NewType
from typing import Final
from typing import Any
from dataclasses import dataclass

import httpx
import celery

from .tasks import celery_app
from .settings import ModerationAPISettings
from base_tools.actions import ModerationRes
from base_tools.exceptions import (
        BodyFetchingError,
        InvalidCredentials,
        )


SUCC_REP: Final[str] = "Content accepted. No problems found"
FAIL_REP: Final[str] = "Content rejected. Reason [{}]: {} content found."
AVAIL_ATTR: Final[str] = "available"

TaskT = TypeVar("TaskT", bound=celery.Task, contravariant=True)
ModerationService = NewType("ModerationService", object)
api_setup = ModerationAPISettings()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
str_handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
str_handler.setFormatter(formatter)
logger.addHandler(str_handler)


@dataclass
class _IntModReport:
    """report after moderation."""
    state: str
    report: str


class ModerationMode(str, Enum):
    ML: str = "ml"
    UNAME: str = "username"
    RULES: str = "rules"


class TimeUnit(float, Enum):
    """TimeUnits repr in seconds."""
    SECOND: float = 1.0
    MINUTE: float = 60.0
    HOUR: float = 3600.0


class TimeoutSec(float, Enum):
    DEF_TOUT: float = 2.0
    LONG_RESP_TOUT: float = 10.0


def on_request_hook(request: httpx.Request) -> None:
    """event hook on httpx-request."""
    logger.debug(
            f"REQ_URL: {request.url}\n "
            )


def on_response_hook(responce: httpx.Response) -> None:
    """log responce."""
    logger.debug(
            f"REQ_URL: {responce.url}\n "
            f"REQ_HEAD:\n\t{responce.headers}\n"
            f"RESP_REQ: {responce.request}\n"
            f"RESP_ST_CODE: {responce.status_code}\n"
            )


def _build_ml_moderation_report(
        mod_resp: dict[str, Any],
        border: float,
        ) -> _IntModReport:
    if not mod_resp.get(AVAIL_ATTR, None):
        raise
    reports: list[str] = []
    idx = 1
    for crt in mod_resp[AVAIL_ATTR]:
        if float(mod_resp[crt]) >= border:
            reports.append(FAIL_REP.format(idx, crt))
            idx += 1
    if reports:
        _report = "\n".join(reports)
        return _IntModReport(state=ModerationRes.REJECTED, report=_report)
    return _IntModReport(state=ModerationRes.ACCEPTED, report=SUCC_REP)


def build_moderation_report(
        mode: str,
        resp: dict[str, Any],
        ) -> _IntModReport:
    match mode:
        case ModerationMode.ML:
            border = api_setup.border_coeff
            return _build_ml_moderation_report(
                    resp["moderation_classes"],
                    border,
                    )
        case _:
            return None


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3})
def fetch_content(self: TaskT, mcode: str, cont_id: str, pub_id: str) -> None:
    """test impl with httpx."""
    params = {"rkey": mcode, "c_uid": cont_id, "pub_id": pub_id}
    addr_url = "http://localhost:8000/main/moderation/posts"
    with httpx.Client(
            timeout=TimeoutSec.DEF_TOUT,
            event_hooks={
                "request": [on_request_hook],
                "response": [on_request_hook],
                },
            ) as client:
        try:
            responce = client.get(addr_url, params=params)
            responce.raise_for_status()
        except httpx.HTTPError as err:  # it`s a base error class
            logger.error(
                f"API raised: {err.response.status_code} "
                f"on url: {err.request.url}. Exact error: {err}\n"
                )
            if err.response.status_code == 404:
                raise BodyFetchingError(
                    f"Maybe error in url: {err.request.url}"
                    )
            raise self.retry(exc=err, contdown=TimeUnit.MINUTE)
        moderate_text_ml.apply_async((responce.json(), mcode, pub_id))
        # moderate_mock.apply_async((responce.json(), mcode, pub_id))


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3})
def moderate_mock(self: TaskT, data: dict, mcode: str, pub_id: str) -> None:
    """mock for e2e testing without API GW."""
    send_moderation_result.apply_async(
        ("mock_done", mcode, pub_id, "accepted"),
        )


@celery_app.task(bind=True, retry_kwargs={"max_retries": 3})
def moderate_text_ml(self: TaskT, data: dict, mcode: str, pub_id: str) -> None:
    """mock moderation process."""
    serv_url = "https://api.sightengine.com/1.0/text/check.json"
    req = {
        "text": data[mcode],
        "mode": "ml",
        "lang": "en",
        "api_user": api_setup.api_user,
        "api_secret": api_setup.api_secret,
    }
    with httpx.Client(
            timeout=TimeoutSec.DEF_TOUT,
            event_hooks={
                "request": [on_request_hook],
                "response": [on_request_hook],
                },
            ) as client:
        try:
            resp = client.post(serv_url, data=req)
            resp.raise_for_status()
        except httpx.ConnectTimeout as err:
            logger.error(err)
            raise self.retry(exc=err, contdown=TimeUnit.MINUTE)
        except httpx.NetworkError as err:
            msg = (
                f"ERR: code = {err.response.status_code}, "
                f"url = {err.request.url}, exact error: {err}\n."
                )
            logger.error(msg)
            raise InvalidCredentials(msg)
        mod_resp = json.loads(resp.text)
        report = build_moderation_report(ModerationMode.ML, mod_resp)
        send_moderation_result.apply_async(
            (report.report, mcode, pub_id, report.state),
            )


@celery_app.task(bind=True, retry_kwargs={"max_retries": 1})
def send_moderation_result(
        self: TaskT,
        report: str,
        mcode: str,
        pub_id: str,
        state: str,
        ) -> None:
    """send moderation result to service."""
    url = "http://localhost:8000/main/moderation/posts/set"
    with httpx.Client(
            timeout=TimeoutSec.DEF_TOUT,
            event_hooks={
                "request": [on_request_hook],
                "response": [on_request_hook],
                },
            follow_redirects=True,
            ) as client:
        try:
            data = {
                    "mcr_id": pub_id,
                    "mcode": mcode,
                    "state": state,
                    "report": report,
                    }
            resp = client.post(url, json=data)
            resp.raise_for_status()
        except httpx.HTTPError as err:
            logger.error(
                f"API raised: {err.response.status_code} "
                f"on url: {err.request.url}"
                )
            if err.response.status_code == 404:
                raise BodyFetchingError(
                    f"Maybe error in url: {err.request.url}"
                    )
            raise self.retry(exc=err, contdown=TimeUnit.MINUTE)
