from celery import Celery


celery_app = Celery(__name__)
celery_app.conf.broker_url = "redis://localhost:6379/0"
celery_app.conf.result_backend = "redis://localhost:6379/0"
celery_app.conf.result_backend_transport_options = {
        "global_keyprefix": "task_results",
        }
celery_app.conf.update(
        task_serializer="json",
        accept_content=["json", ],
        result_serializer="json",
        timezone="Europe/Moscow",
        enable_utc=True,
        include=["tasks.email", ],
        )
celery_app.conf.task_routes = {
            "tasks.email.*": {"queue": "notification"},
        }
