"""Integration controls for the opt-in CI broker isolation plugin."""

import pytest
from redis import Redis

_previous = None


def test_previous_case_can_leave_a_real_backlog(request, settings):
    if not request.config.pluginmanager.hasplugin("scripts.local_ci_broker"):
        pytest.skip("Requires owned CI broker isolation plugin")
    from apps.listings.tasks import refresh_publication_state

    global _previous
    settings.CELERY_TASK_ALWAYS_EAGER = False
    _previous = settings.CELERY_BROKER_TRANSPORT_OPTIONS["global_keyprefix"]
    with Redis.from_url(settings.CELERY_BROKER_URL) as client:
        for _ in range(1001):
            refresh_publication_state.delay()
        assert client.llen(_previous + settings.CELERY_TASK_DEFAULT_QUEUE) == 1001


def test_next_case_isolated_without_deleting_previous_backlog(request, settings):
    if not request.config.pluginmanager.hasplugin("scripts.local_ci_broker"):
        pytest.skip("Requires owned CI broker isolation plugin")
    from apps.safety.rights_access_delivery import broker_records
    from config.celery import app

    assert _previous is not None
    prefix = settings.CELERY_BROKER_TRANSPORT_OPTIONS["global_keyprefix"]
    assert prefix != _previous
    assert app.conf.broker_transport_options["global_keyprefix"] == prefix
    with Redis.from_url(settings.CELERY_BROKER_URL) as client:
        assert client.llen(_previous + settings.CELERY_TASK_DEFAULT_QUEUE) == 1001
        assert client.llen(prefix + settings.CELERY_TASK_DEFAULT_QUEUE) == 0
    assert broker_records(set())["blocked"] == []
    from apps.listings.tasks import refresh_publication_state

    settings.CELERY_TASK_ALWAYS_EAGER = False
    refresh_publication_state.delay()
    with Redis.from_url(settings.CELERY_BROKER_URL) as client:
        assert client.llen(prefix + settings.CELERY_TASK_DEFAULT_QUEUE) == 1
        assert client.llen(_previous + settings.CELERY_TASK_DEFAULT_QUEUE) == 1001


def test_subprocess_inherits_current_case_generation(request, settings):
    if not request.config.pluginmanager.hasplugin("scripts.local_ci_broker"):
        pytest.skip("Requires owned CI broker isolation plugin")
    import json
    import subprocess
    import sys

    expected = settings.CELERY_BROKER_TRANSPORT_OPTIONS["global_keyprefix"]
    child = subprocess.run(
        [sys.executable, "-c", "from django.conf import settings; import json; "
         "print(json.dumps(settings.CELERY_BROKER_TRANSPORT_OPTIONS))"],
        check=True, capture_output=True, text=True, timeout=20,
    )
    assert json.loads(child.stdout) == {"global_keyprefix": expected}
