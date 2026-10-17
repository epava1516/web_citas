"""Explicit causal control using only the disposable runner's real Redis."""

import json
import os
import subprocess
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from redis import Redis


def test_refresh_accumulation_blocks_bounded_inventory(settings):
    if os.environ.get("OWNED_BROKER_ACCUMULATION") != "1":
        pytest.skip("Explicit owned broker accumulation control only")
    run = os.environ.get("LOCAL_CI_SNAPSHOT_RUN", "")
    assert run and os.environ.get("DJANGO_SETTINGS_MODULE") == "local_ci_settings"
    name = "web-modelos-ci-redis-" + run
    info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
    endpoint = urlparse(settings.CELERY_BROKER_URL)
    assert endpoint.hostname == "127.0.0.1" and endpoint.path == "/0"
    assert info["Config"]["Labels"]["web-modelos-local-ci-run"] == run
    assert info["NetworkSettings"]["Ports"]["6379/tcp"] == [
        {"HostIp": endpoint.hostname, "HostPort": str(endpoint.port)}
    ]
    assert not settings.PRODUCTION
    prefix = "causal" + uuid4().hex + ":"
    settings.CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": prefix}
    settings.CELERY_TASK_ALWAYS_EAGER = False
    from apps.listings.tasks import refresh_publication_state
    from apps.safety.rights_access_delivery import broker_records
    from config.celery import app

    assert app.conf.broker_transport_options == {"global_keyprefix": prefix}
    assert not app.conf.task_always_eager
    queue = prefix + settings.CELERY_TASK_DEFAULT_QUEUE
    with Redis.from_url(settings.CELERY_BROKER_URL) as client:
        assert not client.exists(queue)
        try:
            for _ in range(1000):
                refresh_publication_state.delay()
            assert client.llen(queue) == 1000
            assert broker_records(set())["blocked"] == []
            refresh_publication_state.delay()
            assert client.llen(queue) == 1001
            assert broker_records(set())["blocked"] == [
                {"resource": "queues", "reason": "bounded_read_limit"}
            ]
            assert client.llen(queue) == 1001  # Inspection must never consume.
        finally:
            # Only this control's unpredictable namespace, on its verified Redis.
            for key in client.scan_iter(match=prefix + "*"):
                client.delete(key)
        assert broker_records(set())["blocked"] == []
