from django.apps import AppConfig


class ListingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.listings"

    def ready(self):
        from django.db.models.signals import m2m_changed, post_delete, post_save

        from .publication_signals import schedule_refresh

        for signal in (post_save, post_delete, m2m_changed):
            signal.connect(schedule_refresh, dispatch_uid=f"publication_state_{signal!r}")
