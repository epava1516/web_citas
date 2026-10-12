"""Fresh read contrasts; mocks for lifecycle and explicitly real RustFS for transport."""

import hashlib
import io
import json

import pytest
from test_object_repository_stream_verify import Body, mock_case, reference
from test_rights_object_store import object_store as real_object_store

from apps.safety.object_storage import codec
from apps.safety.object_storage.repository import PREFIX

object_store = real_object_store


def legacy_read(repo, ref, target, context):
    with repo._verified_ciphertext(ref) as source:
        return codec.decrypt(source, target, repo.ring, context)


def observe(repo, ref, value, context, *, legacy, during_purge=False, initial_purge=False,
            fail_after=None, short=False, target=None):
    body = Body(value, fail_after, short)
    events = []

    class Client:
        def get_object(self, **kwargs):
            events.append("get")
            return {"Body": body}

    def tombstone(key):
        events.append("tombstone")
        return initial_purge or (during_purge and events.count("tombstone") == 2)

    repo.client = Client()
    repo._tombstone = tombstone
    target = io.BytesIO() if target is None else target
    try:
        total = (legacy_read if legacy else type(repo).read)(repo, ref, target, context)
        outcome = ("success", total)
    except Exception as error:
        outcome = (type(error), str(error))
    return outcome, target.getvalue(), events, body.closed, body.requests


@pytest.mark.parametrize("damage", ["none", "fragmented", "magic", "tag", "truncated",
    "trailing", "context", "key", "size", "digest", "grow", "purge", "initial-purge",
    "late-io", "magic-digest", "context-purge", "magic-grow"])
def test_mock_read_preserves_bytes_guards_physical_fetches_and_error_priority(damage):
    repo, value = mock_case(b"x" * (codec.MAX_CHUNK * 2 + 7), codec.MAX_CHUNK)
    context = b"owned"
    if damage.startswith("magic"):
        value = b"!" + value[1:]
    elif damage == "tag":
        value = value[:-1] + bytes([value[-1] ^ 1])
    elif damage == "truncated":
        value = value[:-1]
    elif damage == "trailing":
        value += b"extra"
    if damage in {"context", "context-purge"}:
        context = b"foreign"
    elif damage == "key":
        repo.ring = codec.Keyring({"v1": b"k" * 32}, "v1")
    size = len(value) - 1 if damage in {"grow", "magic-grow"} else None
    if damage == "size":
        size = len(value) + 1
    ref = reference(repo, value, size=size,
                    digest="0" * 64 if damage in {"digest", "magic-digest"} else None)
    options = {"during_purge": damage in {"purge", "context-purge"},
               "initial_purge": damage == "initial-purge",
               "fail_after": codec.MAX_CHUNK if damage == "late-io" else None,
               "short": damage == "fragmented"}
    old = observe(repo, ref, value, context, legacy=True, **options)
    new = observe(repo, ref, value, context, legacy=False, **options)
    assert old == new
    if damage not in {"none", "fragmented"}:
        assert new[1] == b""


@pytest.mark.parametrize("scratch_failure", ["create", "write", "seek"])
@pytest.mark.parametrize("physical_failure", [None, "digest", "purge"])
def test_mock_read_physical_errors_precede_plaintext_scratch_errors(
    monkeypatch, scratch_failure, physical_failure
):
    repo, value = mock_case()
    ref = reference(repo, value, digest="0" * 64 if physical_failure == "digest" else None)
    real_temporary = codec.tempfile.TemporaryFile
    results = []
    for legacy in (True, False):
        created = 0

        class Scratch:
            def __init__(self):
                self.file = real_temporary()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.file.close()

            def write(self, block):
                if scratch_failure == "write":
                    raise OSError("synthetic plaintext scratch write")
                return self.file.write(block)

            def seek(self, *args):
                if scratch_failure == "seek":
                    raise OSError("synthetic plaintext scratch seek")
                return self.file.seek(*args)

            def __getattr__(self, name):
                return getattr(self.file, name)

        def temporary():
            nonlocal created
            created += 1
            # The old path's first temporary stores ciphertext, not plaintext.
            if legacy and created == 1:
                return real_temporary()
            if scratch_failure == "create":
                raise OSError("synthetic plaintext scratch create")
            return Scratch()

        with monkeypatch.context() as patch:
            patch.setattr(codec.tempfile, "TemporaryFile", temporary)
            result = observe(repo, ref, value, b"owned", legacy=legacy,
                             during_purge=physical_failure == "purge")
            assert result[1] == b""
            assert result[3]
            results.append(result)
    assert results[0] == results[1]


@pytest.mark.parametrize("failure", ["body", "target"])
def test_mock_read_cancellation_closes_body_and_private_scratch(monkeypatch, failure):
    repo, value = mock_case()
    ref = reference(repo, value)
    scratch = []
    original = codec.tempfile.TemporaryFile

    def temporary():
        file = original()
        scratch.append(file)
        return file

    class CancelBody(Body):
        def read(self, size=-1):
            raise KeyboardInterrupt

    class CancelTarget(io.BytesIO):
        def write(self, block):
            raise KeyboardInterrupt

    body = CancelBody(value) if failure == "body" else Body(value)
    repo._tombstone = lambda key: False
    repo.client = type("Client", (), {"get_object": lambda self, **kwargs: {"Body": body}})()
    monkeypatch.setattr(codec.tempfile, "TemporaryFile", temporary)
    target = CancelTarget()
    with pytest.raises(KeyboardInterrupt):
        repo.read(ref, target, b"owned")
    assert body.closed
    assert all(file.closed for file in scratch)
    assert target.getvalue() == b""


def test_mock_target_write_failure_occurs_after_all_guards():
    repo, value = mock_case()
    ref = reference(repo, value)

    class FailedTarget(io.BytesIO):
        def write(self, block):
            raise OSError("synthetic target write")

    old = observe(repo, ref, value, b"owned", legacy=True, target=FailedTarget())
    new = observe(repo, ref, value, b"owned", legacy=False, target=FailedTarget())
    assert old == new
    assert new[0] == (OSError, "synthetic target write")
    assert new[2] == ["tombstone", "get", "tombstone"]


@pytest.mark.parametrize("content", [b"", b"x", b"x" * (codec.MAX_CHUNK + 1)])
def test_real_rustfs_read_three_gets_closed_body_and_only_plaintext_scratch(
    object_store, monkeypatch, content
):
    repo = object_store
    ref = repo.write(io.BytesIO(content), b"owned")
    native, original = repo.client.get_object, codec.tempfile.TemporaryFile
    gets, bodies, writes, files = [], [], [], []

    def observed(**kwargs):
        gets.append(kwargs["Key"])
        response = native(**kwargs)
        bodies.append(response["Body"])
        return response

    class Scratch:
        def __init__(self):
            self.file = original()
            files.append(self.file)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.file.close()

        def write(self, block):
            writes.append(bytes(block))
            return self.file.write(block)

        def __getattr__(self, name):
            return getattr(self.file, name)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(repo.client, "get_object", observed)
            patch.setattr(codec.tempfile, "TemporaryFile", Scratch)
            target = io.BytesIO()
            assert repo.read(ref, target, b"owned") == len(content)
            assert target.getvalue() == content
            assert b"".join(writes) == content
            assert len(files) == 1 and files[0].closed
            assert len(gets) == 3 and gets[0] == gets[2]
            assert gets[1] == repo.descriptor(ref)["key"]
            assert all(body._raw_stream.closed for body in bodies)
    finally:
        repo.purge(ref)


@pytest.mark.parametrize("damage", ["digest", "magic-rehashed", "tag-rehashed", "trailing-rehashed",
                                    "context", "key", "during"])
def test_real_rustfs_read_rejects_corruption_and_purge_without_any_output(
    object_store, monkeypatch, damage
):
    repo = object_store
    ref = repo.write(io.BytesIO(b"synthetic" * 1000), b"owned")
    metadata = repo.descriptor(ref)
    key = metadata["key"]
    body = repo.client.get_object(Bucket=repo.bucket, Key=key)["Body"]
    try:
        value = body.read()
    finally:
        body.close()
    if damage == "magic-rehashed":
        value = b"!" + value[1:]
    elif damage in {"digest", "tag-rehashed"}:
        value = value[:-1] + bytes([value[-1] ^ 1])
    elif damage == "trailing-rehashed":
        value += b"extra"
    checked_ref = ref
    if damage.endswith("-rehashed"):
        metadata.update(bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
        checked_ref = PREFIX + repo.reference_cipher.encrypt(json.dumps(metadata).encode()).decode()
    repo.client.put_object(Bucket=repo.bucket, Key=key, Body=value)
    original_ring, native = repo.ring, repo.client.get_object
    bodies = []
    tombstone = "tombstones/v1/" + key.rsplit("/", 1)[1]

    def observed(**kwargs):
        response = native(**kwargs)
        bodies.append(response["Body"])
        if damage == "during" and kwargs["Key"] == key:
            repo.purge(ref)
        return response

    if damage == "key":
        repo.ring = codec.Keyring({original_ring.active: b"k" * 32}, original_ring.active)
    context = b"foreign" if damage == "context" else b"owned"
    results = []
    try:
        with monkeypatch.context() as patch:
            patch.setattr(repo.client, "get_object", observed)
            for operation in (legacy_read, type(repo).read):
                if damage == "during":
                    repo.client.delete_object(Bucket=repo.bucket, Key=tombstone)
                    repo.client.put_object(Bucket=repo.bucket, Key=key, Body=value)
                target = io.BytesIO()
                with pytest.raises(codec.InvalidObject) as error:
                    operation(repo, checked_ref, target, context)
                results.append((type(error.value), str(error.value)))
                assert target.getvalue() == b""
            assert results[0] == results[1]
            assert all(body._raw_stream.closed for body in bodies)
    finally:
        repo.ring = original_ring
        repo.purge(ref)
