from celery import Celery


app = Celery(__name__, broker="redis://localhost", backend="redis://localhost")
app.conf.update(
        task_serializer="json",
        accept_content="json",
        )

# or app.celeryconfig(confmod.py)
