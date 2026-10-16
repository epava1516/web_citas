"""Configuration restoration for a test-only new-detail generic context."""
from contextlib import nullcontext

import pytest
from django.db import DataError, connection, transaction
from owned_detail_generic import build_scoped_generic_context
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import moderation_views
from apps.listings.models import Listing

pytestmark = pytest.mark.django_db(transaction=True)


def plan_mode():
    with connection.cursor() as cursor:
        cursor.execute('SHOW plan_cache_mode')
        return cursor.fetchone()[0]


@pytest.mark.parametrize('mode', ['agency', 'individual', 'render_error', 'context_error',
                                 'sql_error', 'inherited_rc', 'inherited_rr'])
def test_detail_generic_scope(request, monkeypatch, mode):
    if not any(str(x).split('::')[0] == 'tests/test_owned_detail_generic_scope.py'
               for x in request.config.args):
        pytest.skip('Explicit new-detail generic planning scope only')
    client = request.getfixturevalue('directory')
    listing = Listing.objects.filter(status='published', person__agency__isnull=(mode == 'individual')).first()
    assert listing is not None
    before = plan_mode()
    raw = connection.connection
    factory, threshold = raw.cursor_factory, raw.prepare_threshold
    original_context, original_render = moderation_views.PublicationContext, moderation_views.render
    counters, hydration_modes, render_modes = {'calls': 0}, [], []

    def observed_context(*args, **kwargs):
        assert plan_mode() == 'force_generic_plan'
        if mode == 'context_error':
            raise RuntimeError('owned-context-error')
        if mode == 'sql_error':
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1/0')
        return original_context(*args, **kwargs)

    def observed_render(*args, **kwargs):
        render_modes.append(plan_mode())
        if mode == 'render_error':
            raise RuntimeError('owned-render-error')
        return original_render(*args, **kwargs)

    def observe_sql(execute, sql, params, many, context):
        if '_pv_history' in str(sql):
            hydration_modes.append(plan_mode())
        return execute(sql, params, many, context)

    inherited = mode.startswith('inherited_')
    try:
        with connection.cursor() as cursor:
            cursor.execute('SET plan_cache_mode=force_custom_plan')
        with transaction.atomic() if inherited else nullcontext():
            if mode == 'inherited_rr':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            with monkeypatch.context() as patch, connection.execute_wrapper(observe_sql):
                patch.setattr(moderation_views, 'PublicationContext',
                              build_scoped_generic_context(counters, observed_context))
                patch.setattr(moderation_views, 'render', observed_render)
                if mode in ['context_error', 'render_error']:
                    with pytest.raises(RuntimeError, match='owned-.*-error'):
                        client.get(f'/es/listing/{listing.pk}/')
                elif mode == 'sql_error':
                    with pytest.raises(DataError):
                        client.get(f'/es/listing/{listing.pk}/')
                else:
                    assert client.get(f'/es/listing/{listing.pk}/').status_code == 200
            assert plan_mode() == 'force_custom_plan'
            assert raw.cursor_factory is factory and raw.prepare_threshold == threshold
        assert counters['calls'] == (0 if inherited else 1)
        assert all(x == 'force_generic_plan' for x in hydration_modes)
        if mode in ['agency', 'individual']:
            assert hydration_modes
        assert all(x == 'force_custom_plan' for x in render_modes)
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('plan_cache_mode', %s, false)", [before])
    assert plan_mode() == before
    assert moderation_views.PublicationContext is original_context
    assert moderation_views.render is original_render
