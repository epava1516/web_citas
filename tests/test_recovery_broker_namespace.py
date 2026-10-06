"""Actual Redis transport namespaces isolate old queues without destructive flush."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from django.conf import settings
from kombu import Connection, Producer, Queue


def test_old_fresh_and_other_project_messages_are_isolated():
    token = uuid4().hex
    queue = "recovery_namespace_" + token
    connections = [
        Connection(
            settings.CELERY_BROKER_URL,
            transport_options={"global_keyprefix": f"recovery_namespace_{token}:{generation}:"},
        )
        for generation in ["old", "fresh", "other"]
    ]
    try:
        for broker, label in zip(connections, ["old", "fresh", "other"], strict=True):
            Queue(queue)(broker.default_channel).declare()
            if label != "fresh":
                Producer(broker).publish(
                    {"synthetic": label}, exchange="", routing_key=queue, serializer="json"
                )
        fresh = connections[1].default_channel
        assert fresh.basic_get(queue) is None
        Producer(connections[1]).publish(
            {"synthetic": "fresh"}, exchange="", routing_key=queue, serializer="json"
        )
        message = fresh.basic_get(queue)
        assert message.payload == {"synthetic": "fresh"}
        message.ack()
        for broker, label in [(connections[0], "old"), (connections[2], "other")]:
            message = broker.default_channel.basic_get(queue)
            assert message.payload == {"synthetic": label}
            message.ack()
    finally:
        for broker in connections:
            try:
                broker.default_channel.queue_delete(queue)
            finally:
                broker.release()


@pytest.mark.parametrize("generation", ["../old", "a:b", "UPPER", "", "a" * 33])
def test_queue_generation_rejects_unsafe_names(generation):
    environment = os.environ.copy()
    environment["TASK_QUEUE_GENERATION"] = generation
    result = subprocess.run(
        [sys.executable, "-c", "import config.settings"],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Task queue generation" in result.stderr
