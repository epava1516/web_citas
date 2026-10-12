"""Exact codec contrasts and real RustFS; mocks prove lifecycle only."""

import io
import os
import struct
from threading import Barrier, Event, Lock

import pytest
from cryptography.fernet import InvalidToken
from test_rights_object_store import object_store as real_object_store

from apps.safety import rights_object_content as content
from apps.safety.object_storage import codec

object_store = real_object_store


class Discard:
    def write(self, value):
        return len(value)


def encoded(value=b"synthetic" * 100, chunk=32):
    ring = codec.Keyring({"v1": os.urandom(32)}, "v1")
    target = io.BytesIO()
    codec.encrypt(io.BytesIO(value), target, ring, b"owned", chunk_size=chunk)
    return ring, target.getvalue()


def outcome(operation):
    try:
        return "success", operation()
    except Exception as error:
        return type(error), str(error)


@pytest.mark.parametrize("value,chunk", [(b"", 1), (b"a", 1), (b"abc" * 1000, 32),
                                         (b"x" * (codec.MAX_CHUNK + 1), codec.MAX_CHUNK)])
def test_codec_same_total_and_identical_source_read_order(value, chunk):
    ring, encrypted = encoded(value, chunk)

    class Source(io.BytesIO):
        def __init__(self):
            super().__init__(encrypted)
            self.reads = []

        def read(self, size=-1):
            result = super().read(size)
            self.reads.append((size, len(result)))
            return result

    old, new = Source(), Source()
    assert codec.decrypt(old, Discard(), ring, b"owned") == len(value)
    assert codec.verify(new, ring, b"owned") == len(value)
    assert old.reads == new.reads


@pytest.mark.parametrize("damage", ["magic", "header", "noncanonical", "kind", "size", "tag",
                                   "truncate", "trailing", "reorder", "context", "key", "ceiling"])
def test_codec_exact_negative_class_message_order_and_atomic_read_output(damage):
    ring, original = encoded()
    value = bytearray(original)
    header_size = struct.unpack(">I", value[8:12])[0]
    start = 12 + header_size
    context, maximum = b"owned", codec.MAX_BYTES
    if damage == "magic":
        value[0] ^= 1
        value += b"secondary-trailing-failure"
    elif damage == "header":
        value[15] ^= 1
    elif damage == "noncanonical":
        value = value[:8] + struct.pack(">I", header_size + 1) + b" " + value[12:]
    elif damage == "kind":
        value[start] = 3
    elif damage == "size":
        value[start + 1:start + 5] = struct.pack(">I", 16)
    elif damage == "tag":
        value[-1] ^= 1
    elif damage == "truncate":
        value = value[:-1]
    elif damage == "trailing":
        value += b"extra"
    elif damage == "reorder":
        frame_size = 5 + 32 + 16
        value[start:start + frame_size * 2] = (
            value[start + frame_size:start + frame_size * 2] + value[start:start + frame_size])
    elif damage == "context":
        context = b"foreign"
    elif damage == "key":
        ring = codec.Keyring({"v1": os.urandom(32)}, "v1")
    else:
        maximum = 32
    target = io.BytesIO()
    old = outcome(lambda: codec.decrypt(io.BytesIO(value), target, ring, context, max_bytes=maximum))
    new = outcome(lambda: codec.verify(io.BytesIO(value), ring, context, max_bytes=maximum))
    assert old == new and old[0] is codec.InvalidObject
    assert target.getvalue() == b""


def test_codec_verify_never_creates_plaintext_tempfile_read_still_does(monkeypatch):
    ring, value = encoded()
    original, created = codec.tempfile.TemporaryFile, []

    def tempfile(*args, **kwargs):
        created.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(codec.tempfile, "TemporaryFile", tempfile)
    assert codec.verify(io.BytesIO(value), ring, b"owned") == 900
    assert not created
    target = io.BytesIO()
    assert codec.decrypt(io.BytesIO(value), target, ring, b"owned") == 900
    assert created == [True] and target.getvalue() == b"synthetic" * 100


def test_exact_size_ceiling_and_native_source_io_errors_keep_same_order():
    ring, value = encoded(b"x" * 32, 32)
    assert codec.verify(io.BytesIO(value), ring, b"owned", max_bytes=32) == 32
    assert codec.decrypt(io.BytesIO(value), Discard(), ring, b"owned", max_bytes=32) == 32

    class BrokenSource(io.BytesIO):
        def read(self, size=-1):
            if self.tell() >= 12 + struct.unpack(">I", value[8:12])[0]:
                raise OSError("synthetic input failure")
            return super().read(size)

    target = io.BytesIO()
    old = outcome(lambda: codec.decrypt(BrokenSource(value), target, ring, b"owned"))
    new = outcome(lambda: codec.verify(BrokenSource(value), ring, b"owned"))
    assert old == new == (OSError, "synthetic input failure")
    assert not target.getvalue()


def test_legacy_fernet_dual_reader_unchanged_and_never_enters_verify(settings, monkeypatch):
    from apps.safety.crypto import cipher

    calls = []
    monkeypatch.setattr(content, "repository", lambda: calls.append(True))
    legacy = cipher().encrypt(b"synthetic legacy").decode()
    assert content.unseal_binary(legacy, "export", "image", "photo") == b"synthetic legacy"
    assert not calls
    with pytest.raises(InvalidToken):
        content.unseal_binary(legacy[:-5] + "AAAAA", "export", "image", "photo")
    assert not calls


def test_real_rustfs_same_three_gets_and_body_close_without_plaintext_tempfile(
    object_store, monkeypatch
):
    repo = object_store
    ref = repo.write(io.BytesIO(b"synthetic" * 1000), b"owned")
    get, temporary = repo.client.get_object, codec.tempfile.TemporaryFile
    gets, bodies, temps = [], [], []

    def observed(**values):
        gets.append(values["Key"])
        response = get(**values)
        bodies.append(response["Body"])
        return response

    def tempfile(*args, **kwargs):
        temps.append(True)
        return temporary(*args, **kwargs)

    monkeypatch.setattr(repo.client, "get_object", observed)
    monkeypatch.setattr(codec.tempfile, "TemporaryFile", tempfile)
    try:
        assert repo.read(ref, Discard(), b"owned") == 9000
        old_gets = list(gets)
        # Fresh read stages plaintext only; verify stages neither kind of bytes.
        assert len(old_gets) == 3 and len(temps) == 1
        gets.clear()
        temps.clear()
        assert repo.verify(ref, b"owned") == 9000
        assert gets == old_gets and len(temps) == 0
        assert all(body._raw_stream.closed for body in bodies)
    finally:
        repo.purge(ref)


@pytest.mark.parametrize("damage", ["same-size", "truncate", "grow", "tombstone", "during", "context"])
def test_real_rustfs_read_verify_same_negative_and_closed_body(object_store, monkeypatch, damage):
    repo = object_store
    ref = repo.write(io.BytesIO(b"synthetic" * 1000), b"owned")
    key = repo.descriptor(ref)["key"]
    body = repo.client.get_object(Bucket=repo.bucket, Key=key)["Body"]
    try:
        original = body.read()
    finally:
        body.close()
    get, bodies = repo.client.get_object, []
    context = b"foreign" if damage == "context" else b"owned"
    tombstone = "tombstones/v1/" + key.rsplit("/", 1)[1]

    def observed(**values):
        response = get(**values)
        bodies.append(response["Body"])
        if damage == "during" and values["Key"] == key:
            repo.purge(ref)
        return response

    monkeypatch.setattr(repo.client, "get_object", observed)
    try:
        if damage in {"same-size", "truncate", "grow"}:
            changed = {"same-size": original[:-1] + bytes([original[-1] ^ 1]),
                       "truncate": original[:-1], "grow": original + b"extra"}[damage]
            repo.client.put_object(Bucket=repo.bucket, Key=key, Body=changed)
        elif damage == "tombstone":
            repo.purge(ref)
        target = io.BytesIO()
        old = outcome(lambda: repo.read(ref, target, context))
        if damage == "during":
            # Recreate the SAME synthetic pre-read state for the contrast;
            # this test owns both object and tombstone, no released real data.
            repo.client.delete_object(Bucket=repo.bucket, Key=tombstone)
            repo.client.put_object(Bucket=repo.bucket, Key=key, Body=original)
        new = outcome(lambda: repo.verify(ref, context))
        assert old == new and old[0] is codec.InvalidObject
        assert target.getvalue() == b""
        assert all(body._raw_stream.closed for body in bodies)
    finally:
        repo.purge(ref)


def test_real_rustfs_two_workers_use_verify_and_keep_84_gets_28_objects(object_store, monkeypatch):
    repo = object_store
    references = [repo.write(io.BytesIO(b"synthetic"), b"owned") for _ in range(28)]
    get, native = repo.client.get_object, repo.verify
    lock, barrier = Lock(), Barrier(2, timeout=10)
    gets, active = [], [0, 0]

    def observed(**values):
        with lock:
            gets.append(values["Key"])
        return get(**values)

    def verify(*args):
        with lock:
            active[0] += 1
            active[1] = max(active)
        try:
            barrier.wait()
            return native(*args)
        finally:
            with lock:
                active[0] -= 1

    monkeypatch.setattr(repo.client, "get_object", observed)
    monkeypatch.setattr(repo, "verify", verify)
    # Transport factory lifecycle has its separate real tests. This test borrows
    # the fixture client to prove real provider reads and unchanged dispatcher.
    monkeypatch.setattr(content, "repository", lambda: repo)
    try:
        content._verify_objects_in_order((ref, b"owned") for ref in references)
        assert len(gets) == 84 and active == [0, 2]
    finally:
        for ref in references:
            repo.purge(ref)


def test_mock_verify_worker_first_failure_order_and_drain(monkeypatch):
    release, finished = Event(), Event()
    calls = []

    class Repo:
        def verify(self, reference, context):
            calls.append(reference)
            if reference == "first":
                assert release.wait(5)
                raise codec.InvalidObject("first")
            release.set()
            finished.set()
            raise OSError("second")

    monkeypatch.setattr(content, "repository", Repo)
    with pytest.raises(InvalidToken) as rejected:
        content._verify_objects_in_order(iter([("first", b"owned"), ("second", b"owned"), ("third", b"owned")]))
    assert isinstance(rejected.value.__cause__, codec.InvalidObject)
    assert str(rejected.value.__cause__) == "first"
    assert finished.is_set() and set(calls) == {"first", "second"}
