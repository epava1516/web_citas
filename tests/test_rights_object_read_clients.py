"""Lifecycle mocks are not provider proof; real RustFS cases exercise every GET."""

import base64
import io
import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

import pytest
from cryptography.fernet import Fernet
from test_rights_object_store import object_store as real_object_store

from apps.safety.object_storage import factory
from apps.safety.object_storage import read_clients as scope
from apps.safety.object_storage.codec import InvalidObject

object_store = real_object_store


class Client:
    def __init__(self, fail=False):
        self.closed = 0
        self.fail = fail

    def close(self):
        self.closed += 1
        if self.fail:
            raise RuntimeError("synthetic transport teardown")


def configured(settings):
    settings.RIGHTS_OBJECT_ENDPOINT = "http://127.0.0.1:1"
    settings.RIGHTS_OBJECT_REGION = "us-east-1"
    settings.RIGHTS_OBJECT_ACCESS_KEY = "synthetic"
    settings.RIGHTS_OBJECT_SECRET_KEY = "synthetic-secret"
    settings.RIGHTS_OBJECT_BUCKET = "rights-test"
    settings.RIGHTS_OBJECT_KEYS = json.dumps({"v1": base64.b64encode(os.urandom(32)).decode()})
    settings.RIGHTS_OBJECT_ACTIVE_KEY = "v1"
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True


def test_mock_lifecycle_nested_failure_cap_and_all_close_attempts(settings):
    configured(settings)
    created = []

    def create():
        client = Client(fail=not created)
        created.append(client)
        return client

    with pytest.raises(ValueError, match="domain"):
        with scope.read_clients():
            outer = scope._current.get()
            assert scope.client(create) is scope.client(create)
            with scope.read_clients():
                nested = scope.client(create)
            assert nested.closed == 1
            assert scope._current.get() is outer
            for index in range(4):
                settings.RIGHTS_OBJECT_REGION = str(index)
                scope.client(create)
            assert len(outer["clients"]) == 4
            overflow = created[-1]
            raise ValueError("domain")
    assert scope._current.get() is None
    assert created[0].closed == 1
    assert all(client.closed == 1 for client in created[2:5])
    assert overflow.closed == 0  # Explicit native lifecycle fallback.


@pytest.mark.parametrize("setting", scope.SETTINGS)
def test_mock_every_configuration_field_is_fresh(settings, setting):
    configured(settings)
    with scope.read_clients():
        first = scope.client(Client)
        old = getattr(settings, setting)
        setattr(settings, setting, not old if type(old) is bool else str(old) + "-changed")
        assert scope.client(Client) is not first


@pytest.mark.parametrize(
    "setting", ["RIGHTS_OBJECT_ENDPOINT", "RIGHTS_OBJECT_ACCESS_KEY", "RIGHTS_OBJECT_SECRET_KEY"]
)
def test_mock_config_drift_inside_constructor_never_retains_wrong_target(settings, setting):
    configured(settings)
    old = getattr(settings, setting)
    created = []

    def changing_create():
        setattr(settings, setting, old + "-during-create")
        result = Client()
        created.append(result)
        return result

    with scope.read_clients():
        first = scope.client(changing_create)
        assert first is created[0]
        assert not scope._current.get()["clients"]
        setattr(settings, setting, old)
        second = scope.client(changing_create)
        assert second is created[1] and second is not first
        assert not scope._current.get()["clients"]
    # Changed-during-create transports keep the original native lifecycle.
    assert first.closed == second.closed == 0
    first.close()
    second.close()


def test_mock_unknown_types_pid_thread_and_outside_scope_are_native(settings, monkeypatch):
    configured(settings)
    assert scope.client(Client) is not scope.client(Client)
    with scope.read_clients():
        original = scope.client(Client)
        context = copy_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(context.run, scope.client, Client).result() is not original
        with monkeypatch.context() as patch:
            patch.setattr(scope.os, "getpid", lambda: -1)
            assert scope.client(Client) is not original
        settings.RIGHTS_OBJECT_KEYS = {}
        assert scope.client(Client) is not scope.client(Client)

        class Custom(str):
            pass

        settings.RIGHTS_OBJECT_KEYS = Custom("custom")
        assert scope.client(Client) is not scope.client(Client)


def real_settings(settings, object_store):
    configured(settings)
    credentials = object_store.client._request_signer._credentials.get_frozen_credentials()
    settings.RIGHTS_OBJECT_ENDPOINT = object_store.client.meta.endpoint_url
    settings.RIGHTS_OBJECT_ACCESS_KEY = credentials.access_key
    settings.RIGHTS_OBJECT_SECRET_KEY = credentials.secret_key


def test_real_rustfs_repeated_reads_three_gets_each_one_scoped_client(
    settings, monkeypatch, object_store
):
    real_settings(settings, object_store)
    original = factory.boto3.client
    created, gets, bodies = [], [], []

    def create(*args, **kwargs):
        client = original(*args, **kwargs)
        created.append(client)
        get = client.get_object

        def observed(**values):
            gets.append(values["Key"])
            response = get(**values)
            bodies.append(response["Body"])
            return response

        client.get_object = observed
        return client

    monkeypatch.setattr(factory.boto3, "client", create)
    writer = factory.repository()
    ref = writer.write(io.BytesIO(b"synthetic private content" * 100), b"owned/context")
    writer.client.close()
    created.clear()
    gets.clear()
    with scope.read_clients():
        for _ in range(2):
            target = io.BytesIO()
            factory.repository().read(ref, target, b"owned/context")
            assert target.getvalue() == b"synthetic private content" * 100
        assert len(created) == 1
        assert len(gets) == 6
    assert all(body._raw_stream.closed for body in bodies)
    created.clear()
    for _ in range(2):
        repo = factory.repository()
        repo.read(ref, io.BytesIO(), b"owned/context")
        repo.client.close()
    assert len(created) == 2
    purger = factory.repository()
    try:
        purger.purge(ref)
    finally:
        purger.client.close()


@pytest.mark.parametrize("damage", ["corrupt", "truncated", "oversized", "tombstone", "during"])
def test_real_rustfs_damage_between_scoped_reads_rejected(settings, object_store, damage):
    real_settings(settings, object_store)
    repo = factory.repository()
    ref = repo.write(io.BytesIO(b"synthetic" * 1000), b"owned/context")
    key = repo.descriptor(ref)["key"]
    body = repo.client.get_object(Bucket=repo.bucket, Key=key)["Body"]
    try:
        original = body.read()
    finally:
        body.close()
    try:
        with scope.read_clients():
            borrowed = factory.repository()
            native_get = borrowed.client.get_object
            bodies = []

            def observed(**values):
                response = native_get(**values)
                bodies.append(response["Body"])
                return response

            borrowed.client.get_object = observed
            borrowed.read(ref, io.BytesIO(), b"owned/context")
            if damage in {"corrupt", "truncated", "oversized"}:
                changed = {
                    "corrupt": b"changed",
                    "truncated": original[:-1],
                    "oversized": original + b"extra",
                }[damage]
                repo.client.put_object(Bucket=repo.bucket, Key=key, Body=changed)
            elif damage == "tombstone":
                repo.purge(ref)
            else:
                borrowed = factory.repository()
                observed_get = borrowed.client.get_object

                def purged_during(**values):
                    response = observed_get(**values)
                    if values["Key"] == key:
                        repo.purge(ref)
                    return response

                borrowed.client.get_object = purged_during
            target = io.BytesIO()
            with pytest.raises(InvalidObject):
                factory.repository().read(ref, target, b"owned/context")
            assert target.getvalue() == b""
            assert all(body._raw_stream.closed for body in bodies)
    finally:
        repo.purge(ref)
        repo.client.close()


def test_real_rustfs_fresh_wrong_ring_rejects_with_new_transport(settings, object_store):
    real_settings(settings, object_store)
    repo = factory.repository()
    ref = repo.write(io.BytesIO(b"synthetic"), b"owned/context")
    try:
        with scope.read_clients():
            first = factory.repository()
            first.read(ref, io.BytesIO(), b"owned/context")
            settings.RIGHTS_OBJECT_KEYS = json.dumps(
                {"v1": base64.b64encode(os.urandom(32)).decode()}
            )
            second = factory.repository()
            assert second.client is not first.client and second.ring is not first.ring
            with pytest.raises(InvalidObject):
                second.read(ref, io.BytesIO(), b"owned/context")
    finally:
        repo.purge(ref)
        repo.client.close()
