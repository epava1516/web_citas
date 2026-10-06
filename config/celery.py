import os

from celery import Celery
from celery.contrib.django.task import DjangoTask
from celery.exceptions import Ignore
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


class RecoveryAwareTask(DjangoTask):
    """Never execute consumed business messages while recovery is active."""

    def before_start(self, task_id, args, kwargs):
        if settings.RECOVERY_MODE:
            raise Ignore("Business task disabled during isolated recovery")
        return super().before_start(task_id, args, kwargs)


app = Celery("clasificados", task_cls=RecoveryAwareTask)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
