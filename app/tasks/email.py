import smtplib
import logging
from typing import TypeVar
from email.message import EmailMessage

from .tasks import celery_app as app
from .settings import SMTPSettings


settings = SMTPSettings()


LOGIN: str = "r5railmodels@gmail.com"
RECEIVER: str = "r5railmodels@gmail.com"

T = TypeVar("T")


smtp_logger = logging.getLogger(__name__)
smtp_logger.setLevel(logging.DEBUG)
str_handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
str_handler.setFormatter(formatter)
smtp_logger.addHandler(str_handler)


# smtp_logger.debug(settings)


@app.task(
        bind=True,
        queue="notification",
        retry_kwargs={"max_retries": 1},
        )
def send_email(self: T, sender: str, recv: str, payload: str) -> None:
    msg = EmailMessage()
    msg.set_content(payload)
    msg["Subject"] = "Test celery."
    msg["From"] = sender
    msg["To"] = recv
    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as mail_srv:
        mail_srv.login(settings.SMTP_LOGIN, settings.SMTP_PASSWD)
        try:
            mail_srv.send_message(msg)
        except Exception as err:
            smtp_logger.error(err)
            raise self.retry(exc=err, contdown=2)
