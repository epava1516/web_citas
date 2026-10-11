"""MOCK lifecycle/order cases and separate actual RustFS physical proofs."""

import base64
import io
import json
import os
from contextlib import contextmanager
from threading import Barrier, Event, Lock, get_ident

import pytest
from cryptography.fernet import Fernet, InvalidToken
from test_rights_object_store import object_store as real_object_store

from apps.safety import rights_object_content as content
from apps.safety.object_storage import factory
from apps.safety.object_storage import read_clients as transport
from apps.safety.object_storage.repository import ObjectRepository

object_store = real_object_store


def test_mock_two_pending_ordered_exception_and_wait_for_started_jobs(monkeypatch):
    first_waiting, release, finished = Event(), Event(), Event()
    calls = []

    def verify(reference, context):
        calls.append(reference)
        if reference == "first":
            first_waiting.set()
            assert release.wait(5)
            raise ValueError("first failure")
        assert first_waiting.wait(5)
        release.set()
        finished.set()
        raise TypeError("second failure")

    monkeypatch.setattr(content, "_verify_object", verify)
    with pytest.raises(ValueError, match="first failure"):
        content._verify_objects_in_order(iter([("first", b"a"), ("second", b"b"), ("third", b"c")]))
    assert finished.is_set()
    assert set(calls) == {"first", "second"}


def test_mock_metadata_exception_cannot_mask_earlier_physical_failure(monkeypatch):
    def objects():
        yield "first", b"owned"
        raise TypeError("metadata failure")

    def verify(*args):
        raise ValueError("physical first")

    monkeypatch.setattr(content, "_verify_object", verify)
    with pytest.raises(ValueError, match="physical first"):
        content._verify_objects_in_order(objects())
    monkeypatch.setattr(content, "_verify_object", lambda *args: None)
    with pytest.raises(TypeError, match="metadata failure"):
        content._verify_objects_in_order(objects())


def test_mock_worker_scope_closes_and_resets_even_when_object_and_close_fail(monkeypatch):
    original_scope = transport.read_clients
    exited, clients = [], []

    @contextmanager
    def observed_scope():
        try:
            with original_scope():
                yield
        finally:
            exited.append(transport._current.get())

    class Client:
        closed = False

        def close(self):
            self.closed = True
            raise RuntimeError("mock close failure")

    class Repo:
        def verify(self, *args):
            raise InvalidToken

    def repository():
        def create():
            client = Client()
            clients.append(client)
            return client

        transport.client(create)
        return Repo()

    monkeypatch.setattr(transport, "read_clients", observed_scope)
    monkeypatch.setattr(content, "repository", repository)
    with pytest.raises(InvalidToken):
        content._verify_objects_in_order(iter([("a", b"own"), ("b", b"own")]))
    assert len(exited) == 2 and all(state is None for state in exited)
    assert clients and all(client.closed for client in clients)


def test_mock_iterator_close_after_failure_does_not_mask_domain(monkeypatch):
    closed = []

    def objects():
        try:
            yield "a", b"own"
            yield "b", b"own"
            yield "never-dispatched", b"own"
        finally:
            closed.append(True)
            raise RuntimeError("cursor teardown")

    def fail(*args):
        raise InvalidToken

    monkeypatch.setattr(content, "_verify_object", fail)
    with pytest.raises(InvalidToken):
        content._verify_objects_in_order(objects())
    assert closed == [True]


def real_settings(settings, object_store):
    credentials = object_store.client._request_signer._credentials.get_frozen_credentials()
    settings.RIGHTS_OBJECT_ENDPOINT = object_store.client.meta.endpoint_url
    settings.RIGHTS_OBJECT_REGION = "us-east-1"
    settings.RIGHTS_OBJECT_ACCESS_KEY = credentials.access_key
    settings.RIGHTS_OBJECT_SECRET_KEY = credentials.secret_key
    settings.RIGHTS_OBJECT_BUCKET = object_store.bucket
    settings.RIGHTS_OBJECT_KEYS = json.dumps({"v1": base64.b64encode(os.urandom(32)).decode()})
    settings.RIGHTS_OBJECT_ACTIVE_KEY = "v1"
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True


def test_real_rustfs_28_objects_84_gets_two_jobs_closed_bodies_clients(
    settings, monkeypatch, object_store
):
    real_settings(settings, object_store)
    writer = factory.repository()
    references = [
        writer.write(io.BytesIO(b"synthetic" * 1000), f"own/{i}".encode()) for i in range(28)
    ]
    native_client, native_verify = factory._new_s3_client, ObjectRepository.verify
    lock, barrier = Lock(), Barrier(2, timeout=10)
    gets, clients, bodies, rings, active = [], [], [], [], [0, 0]

    def create(*args, **kwargs):
        client = native_client(*args, **kwargs)
        get, close = client.get_object, client.close
        marker = {"closed": False, "thread": get_ident()}
        with lock:
            clients.append(marker)

        def observed(**values):
            with lock:
                gets.append(values["Key"])
            response = get(**values)
            with lock:
                bodies.append(response["Body"])
            return response

        def closed():
            marker["closed"] = True
            close()

        client.get_object, client.close = observed, closed
        return client

    def verify(self, reference, context):
        with lock:
            rings.append(self.ring)
            active[0] += 1
            active[1] = max(active)
        try:
            barrier.wait()
            return native_verify(self, reference, context)
        finally:
            with lock:
                active[0] -= 1

    monkeypatch.setattr(factory, "_new_s3_client", create)
    monkeypatch.setattr(ObjectRepository, "verify", verify)
    try:
        content._verify_objects_in_order(
            (ref, f"own/{i}".encode()) for i, ref in enumerate(references)
        )
        assert len(gets) == 84
        assert len(clients) == 2
        assert active == [0, 2]
        assert all(client["closed"] for client in clients)
        assert all(body._raw_stream.closed for body in bodies)
        assert len({client["thread"] for client in clients}) == 2
        assert len({id(ring) for ring in rings}) == 28
        content._verify_objects_in_order(
            (ref, f"own/{i}".encode()) for i, ref in enumerate(references)
        )
        assert len(gets) == 168 and len(clients) == 4
        assert all(client["closed"] for client in clients)
    finally:
        for ref in references:
            writer.purge(ref)
        writer.client.close()


def test_real_rustfs_key_change_after_one_object_uses_fresh_ring(
    settings, monkeypatch, object_store
):
    real_settings(settings, object_store)
    writer = factory.repository()
    references = [writer.write(io.BytesIO(b"synthetic"), b"own") for _ in range(2)]
    first_complete = Event()
    native = content._verify_object

    def verify(reference, owner_context):
        if reference == references[0]:
            native(reference, owner_context)
            settings.RIGHTS_OBJECT_KEYS = json.dumps(
                {"v1": base64.b64encode(os.urandom(32)).decode()}
            )
            first_complete.set()
        else:
            assert first_complete.wait(10)
            native(reference, owner_context)

    monkeypatch.setattr(content, "_verify_object", verify)
    try:
        with pytest.raises(InvalidToken):
            content._verify_objects_in_order((ref, b"own") for ref in references)
    finally:
        for ref in references:
            writer.purge(ref)
        writer.client.close()


@pytest.mark.parametrize(
    "damage", ["corrupt", "truncated", "oversized", "purged", "during", "wrongkey", "foreign"]
)
def test_real_rustfs_parallel_rejects_physical_damage(settings, monkeypatch, object_store, damage):
    real_settings(settings, object_store)
    writer = factory.repository()
    references = [writer.write(io.BytesIO(b"synthetic" * 1000), b"own") for _ in range(2)]
    key = writer.descriptor(references[0])["key"]
    body = writer.client.get_object(Bucket=writer.bucket, Key=key)["Body"]
    try:
        original = body.read()
    finally:
        body.close()
    native_client = factory._new_s3_client
    bodies, clients = [], []

    def create(*args, **kwargs):
        client = native_client(*args, **kwargs)
        get, close = client.get_object, client.close
        marker = {"closed": False}
        clients.append(marker)

        def observed(**values):
            response = get(**values)
            bodies.append(response["Body"])
            if damage == "during" and values["Key"] == key:
                writer.purge(references[0])
            return response

        def closed():
            marker["closed"] = True
            close()

        client.get_object, client.close = observed, closed
        return client

    monkeypatch.setattr(factory, "_new_s3_client", create)
    try:
        if damage in {"corrupt", "truncated", "oversized"}:
            changed = {
                "corrupt": b"bad",
                "truncated": original[:-1],
                "oversized": original + b"extra",
            }[damage]
            writer.client.put_object(Bucket=writer.bucket, Key=key, Body=changed)
        elif damage == "purged":
            writer.purge(references[0])
        elif damage == "wrongkey":
            settings.RIGHTS_OBJECT_KEYS = json.dumps(
                {"v1": base64.b64encode(os.urandom(32)).decode()}
            )
        context = b"foreign" if damage == "foreign" else b"own"
        with pytest.raises(InvalidToken):
            content._verify_objects_in_order((ref, context) for ref in references)
        assert all(client["closed"] for client in clients)
        assert all(body._raw_stream.closed for body in bodies)
    finally:
        for ref in references:
            writer.purge(ref)
        writer.client.close()
