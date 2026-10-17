"""Per-test broker generations, opt-in and confined to verified disposable CI."""

import json
import os
import subprocess
from urllib.parse import urlparse
from uuid import uuid4

import pytest

_verified = set()


@pytest.fixture(autouse=True)
def isolated_test_broker(settings, monkeypatch):
    run = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN", "")
    if not run:
        raise RuntimeError("Broker isolation plugin requires the owned CI runner")
    endpoint = urlparse(settings.CELERY_BROKER_URL)
    name = "web-modelos-ci-redis-" + run
    if settings.PRODUCTION or endpoint.hostname != "127.0.0.1" or endpoint.path != "/0":
        raise RuntimeError("Test broker must be the disposable local Redis")
    identity = (name, endpoint.port)
    if identity not in _verified:
        info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
        if (
            info["Config"]["Labels"].get("web-modelos-local-ci-run") != run
            or not info["State"]["Running"]
            or info["NetworkSettings"]["Ports"]["6379/tcp"]
            != [{"HostIp": endpoint.hostname, "HostPort": str(endpoint.port)}]
        ):
            raise RuntimeError("Redis ownership or endpoint mismatch")
        _verified.add(identity)
    generation = "t" + uuid4().hex[:31]
    monkeypatch.setenv("TASK_QUEUE_GENERATION", generation)
    monkeypatch.setenv("LOCAL_CI_TEST_QUEUE_GENERATION", generation)
    settings.TASK_QUEUE_GENERATION = generation
    settings.CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": f"clasificados:{generation}:"}
    from kombu import pools

    from config.celery import app

    pools.reset()
    app._pool = None
    app.amqp._producer_pool = None
    # No messages are deleted: previous test generations remain until the runner
    # removes its owned Redis. Subprocesses inherit this case's generation.
    try:
        yield generation
    finally:
        pools.reset()
        app._pool = None
        app.amqp._producer_pool = None
