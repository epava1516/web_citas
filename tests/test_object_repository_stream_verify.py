"""MOCK error/lifecycle contrasts plus explicitly real RustFS transport proof."""

import hashlib
import io
import json
import os

import pytest
from cryptography.fernet import Fernet
from test_rights_object_store import object_store as real_object_store

from apps.safety.object_storage import codec
from apps.safety.object_storage.repository import PREFIX, ObjectRepository

object_store = real_object_store


def result(function):
    try:
        return "success", function()
    except Exception as error:
        return type(error), str(error)


class Body(io.BytesIO):
    def __init__(self, content, fail_after=None, short=False):
        super().__init__(content)
        self.requests = []
        self.fail_after, self.short = fail_after, short

    def read(self, size=-1):
        self.requests.append(size)
        if self.fail_after is not None and self.tell() >= self.fail_after:
            raise OSError("synthetic late IO")
        return super().read(min(size, 19) if self.short else size)


def mock_case(content=b"owned" * 100, chunk=32):
    ring = codec.Keyring({"v1": os.urandom(32)}, "v1")
    encrypted = io.BytesIO()
    codec.encrypt(io.BytesIO(content), encrypted, ring, b"owned", chunk_size=chunk)
    cipher = Fernet(Fernet.generate_key())
    repo = ObjectRepository(None, "owned", ring, cipher)
    return repo, encrypted.getvalue()


def reference(repo, value, *, size=None, digest=None):
    metadata = {"v": 1, "key": "encrypted/v1/" + "a" * 32,
                "bytes": len(value) if size is None else size,
                "sha256": hashlib.sha256(value).hexdigest() if digest is None else digest}
    return PREFIX + repo.reference_cipher.encrypt(json.dumps(metadata).encode()).decode()


def operation(repo, ref, value, context, *, old=False, tombstone=False, fail_after=None, short=False):
    body = Body(value, fail_after, short)
    events = []

    class Client:
        def get_object(self, **kwargs):
            events.append("get")
            return {"Body": body}

    repo.client = Client()

    def tombstone_check(key):
        events.append("tombstone")
        return tombstone and events.count("tombstone") == 2

    repo._tombstone = tombstone_check

    def run():
        if old:
            with repo._verified_ciphertext(ref) as source:
                return codec.verify(source, repo.ring, context)
        return repo.verify(ref, context)

    observed = result(run)
    assert body.closed
    assert all(size == codec.MAX_CHUNK for size in body.requests)
    return observed, events, body.requests


@pytest.mark.parametrize("content,chunk,short", [(b"", 1, False), (b"x", 1, True),
    (b"x" * (codec.MAX_CHUNK * 3 + 7), codec.MAX_CHUNK, False)])
def test_mock_same_total_physical_fetches_and_three_guards(content, chunk, short):
    repo, value = mock_case(content, chunk)
    ref = reference(repo, value)
    old = operation(repo, ref, value, b"owned", old=True, short=short)
    new = operation(repo, ref, value, b"owned", short=short)
    assert old == new
    assert new[0] == ("success", len(content))
    assert new[1] == ["tombstone", "get", "tombstone"]


@pytest.mark.parametrize("damage", ["magic", "tag", "truncated-codec", "trailing", "context", "key",
    "size", "digest", "grow", "purge", "late-io", "magic-digest", "context-purge", "magic-grow"])
def test_mock_exact_original_error_priority_and_drain(damage):
    repo, original = mock_case(b"x" * (codec.MAX_CHUNK * 2 + 7), codec.MAX_CHUNK)
    value, context = original, b"owned"
    if damage.startswith("magic"):
        value = b"!" + value[1:]
    elif damage == "tag":
        value = value[:-1] + bytes([value[-1] ^ 1])
    elif damage == "truncated-codec":
        value = value[:-1]
    elif damage == "trailing":
        value += b"extra"
    if damage in {"context", "context-purge"}:
        context = b"foreign"
    elif damage == "key":
        repo.ring = codec.Keyring({"v1": os.urandom(32)}, "v1")
    size = len(value) - 1 if damage in {"grow", "magic-grow"} else None
    if damage == "size":
        size = len(value) + 1
    digest = "0" * 64 if damage in {"digest", "magic-digest"} else None
    ref = reference(repo, value, size=size, digest=digest)
    # Authenticated rehashed refs reach AEAD/EOF negatives, not just cipher SHA.
    if damage == "late-io":
        value = b"!" + value[1:]
        ref = reference(repo, value)
    kwargs = {"tombstone": damage in {"purge", "context-purge"},
              "fail_after": codec.MAX_CHUNK if damage == "late-io" else None}
    old = operation(repo, ref, value, context, old=True, **kwargs)
    new = operation(repo, ref, value, context, **kwargs)
    assert old == new
    assert new[0][0] is (OSError if damage == "late-io" else codec.InvalidObject)
    if damage == "late-io":
        assert len(new[2]) == 2  # Never retry the physical failure while draining.


def test_mock_verify_zero_tempfiles_and_read_preserved(monkeypatch):
    repo, value = mock_case()
    ref = reference(repo, value)

    def forbidden(*args, **kwargs):
        raise AssertionError("verify must not create any tempfile")

    monkeypatch.setattr(codec.tempfile, "TemporaryFile", forbidden)
    assert operation(repo, ref, value, b"owned")[0] == ("success", 500)
    assert operation(repo, ref, value, b"owned", old=True)[0][0] is AssertionError


def test_mock_descriptor_and_initial_purge_precede_object_get():
    repo, value = mock_case()
    calls = []
    repo._tombstone = lambda key: calls.append(key) or True
    assert result(lambda: repo.verify("invalid", b"owned"))[0] is codec.InvalidObject
    assert calls == []
    assert result(lambda: repo.verify(reference(repo, value), b"owned")) == (
        codec.InvalidObject, "Object irreversibly purged")
    assert len(calls) == 1


def test_real_rustfs_stream_verify_three_gets_closed_body_no_tempfile(object_store, monkeypatch):
    repo = object_store
    content = b"synthetic" * (codec.MAX_CHUNK // 3)
    ref = repo.write(io.BytesIO(content), b"owned")
    native, gets, bodies = repo.client.get_object, [], []

    def observed(**kwargs):
        gets.append(kwargs["Key"])
        response = native(**kwargs)
        bodies.append(response["Body"])
        return response

    def forbidden(*args, **kwargs):
        raise AssertionError("stream verify tempfile")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(repo.client, "get_object", observed)
            patch.setattr(codec.tempfile, "TemporaryFile", forbidden)
            assert repo.verify(ref, b"owned") == len(content)
            assert len(gets) == 3
            assert gets[0] == gets[2] and gets[1] == repo.descriptor(ref)["key"]
            assert all(body._raw_stream.closed for body in bodies)
    finally:
        repo.purge(ref)


@pytest.mark.parametrize("damage", ["digest", "grow", "truncate", "magic-rehashed", "tag-rehashed",
                                    "trailing-rehashed", "context", "key", "during"])
def test_real_rustfs_same_error_priority_and_body_cleanup(object_store, monkeypatch, damage):
    repo = object_store
    ref = repo.write(io.BytesIO(b"synthetic" * 1000), b"owned")
    metadata = repo.descriptor(ref)
    key = metadata["key"]
    body = repo.client.get_object(Bucket=repo.bucket, Key=key)["Body"]
    try:
        original = body.read()
    finally:
        body.close()
    value = original
    if damage in {"digest", "tag-rehashed"}:
        value = value[:-1] + bytes([value[-1] ^ 1])
    elif damage == "grow":
        value += b"extra"
    elif damage == "truncate":
        value = value[:-1]
    elif damage == "magic-rehashed":
        value = b"!" + value[1:]
    elif damage == "trailing-rehashed":
        value += b"extra"
    checked_ref = ref
    if damage.endswith("-rehashed"):
        metadata.update(bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
        checked_ref = PREFIX + repo.reference_cipher.encrypt(json.dumps(metadata).encode()).decode()
    native, bodies = repo.client.get_object, []
    original_ring = repo.ring
    tombstone = "tombstones/v1/" + key.rsplit("/", 1)[1]

    def observed(**kwargs):
        response = native(**kwargs)
        bodies.append(response["Body"])
        if damage == "during" and kwargs["Key"] == key:
            repo.purge(ref)
        return response

    def legacy_verify():
        with repo._verified_ciphertext(checked_ref) as source:
            return codec.verify(source, repo.ring, context)

    context = b"foreign" if damage == "context" else b"owned"
    try:
        repo.client.put_object(Bucket=repo.bucket, Key=key, Body=value)
        if damage == "key":
            repo.ring = codec.Keyring({original_ring.active: os.urandom(32)}, original_ring.active)
        with monkeypatch.context() as patch:
            patch.setattr(repo.client, "get_object", observed)
            old = result(legacy_verify)
            if damage == "during":
                # Restore only this fixture-owned synthetic state for the contrast.
                repo.client.delete_object(Bucket=repo.bucket, Key=tombstone)
                repo.client.put_object(Bucket=repo.bucket, Key=key, Body=value)
            new = result(lambda: repo.verify(checked_ref, context))
            assert old == new and new[0] is codec.InvalidObject
            assert all(body._raw_stream.closed for body in bodies)
    finally:
        repo.ring = original_ring
        repo.purge(ref)
