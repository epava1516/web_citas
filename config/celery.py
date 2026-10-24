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
            from apps.core.operational_events import task_result

            task_result(self.name, "ignored")
            raise Ignore("Business task disabled during isolated recovery")
        return super().before_start(task_id, args, kwargs)


    def on_success(self, retval, task_id, args, kwargs):
        from apps.core.operational_events import task_result

        task_result(self.name, "succeeded", retval)
        return super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from apps.core.operational_events import task_result

        task_result(self.name, "failed")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        from apps.core.operational_events import task_result

        task_result(self.name, "retry")
        return super().on_retry(exc, task_id, args, kwargs, einfo)


app = Celery("clasificados", task_cls=RecoveryAwareTask)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
