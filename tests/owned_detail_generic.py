"""Test-only generic planning limited to the new detail's context construction."""
from django.db import connection, transaction

from apps.listings import moderation_views


def build_scoped_generic_context(counters=None, original=None):
    original = original or moderation_views.PublicationContext
    counters = counters if counters is not None else {'calls': 0}

    def context(*args, **kwargs):
        counters['calls'] += 1
        assert connection.in_atomic_block
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SHOW plan_cache_mode')
                previous = cursor.fetchone()[0]
                cursor.execute('SET LOCAL plan_cache_mode=force_generic_plan')
            result = original(*args, **kwargs)
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('plan_cache_mode', %s, true)", [previous])
            return result

    return context
