import io
import os
import struct

import pytest

from apps.safety.object_storage.codec import MAGIC, InvalidObject, Keyring, decrypt, encrypt, rewrap


@pytest.mark.parametrize("width", [1, 7, 513, 1026, 1048576])
@pytest.mark.parametrize("buffer_type", [bytes, bytearray, memoryview])
@pytest.mark.parametrize("failure_at", [None, 0, 1, 2])
def test_frame_reader_preserves_fragmented_read_order_and_failures(width, buffer_type, failure_at):
    from apps.safety.object_storage.codec import _read

    def reference(source, size):
        # Frozen pre-optimization reader: contrast observable stream behaviour.
        value = bytearray()
        while len(value) < size:
            chunk = source.read(size - len(value))
            if not chunk:
                raise InvalidObject("Truncated object")
            value.extend(chunk)
        return bytes(value)

    class Reader:
        def __init__(self, content):
            self.source = io.BytesIO(content)
            self.calls = []

        def read(self, size):
            self.calls.append(size)
            if len(self.calls) - 1 == failure_at:
                raise OSError("synthetic stream failure")
            return buffer_type(self.source.read(min(width, size)))

    for size, content in [(0, b""), (1027, b"s" * 1027), (1027, b"s" * 1026)]:
        observations = []
        for function in (reference, _read):
            source = Reader(content)
            try:
                value = function(source, size)
                observations.append((type(value), value, source.calls, source.source.tell()))
            except (InvalidObject, OSError) as error:
                observations.append((type(error), str(error), source.calls, source.source.tell()))
        assert observations[0] == observations[1]


@pytest.fixture
def ring():
    return Keyring({"old": os.urandom(32)}, "old")


def encoded(ring, content=b"secret" * 100):
    target = io.BytesIO()
    encrypt(io.BytesIO(content), target, ring, b"export:1:subject:2", chunk_size=32)
    return target.getvalue()


@pytest.mark.parametrize(
    "content",
    [b"", b"a", b"abc" * 1000, os.urandom(1048577)],
    ids=["empty", "one-byte", "repeated", "random-over-one-mib"],
)
def test_roundtrip(ring, content):
    target = io.BytesIO()
    assert decrypt(io.BytesIO(encoded(ring, content)), target, ring, b"export:1:subject:2") == len(
        content
    )
    assert target.getvalue() == content


@pytest.mark.parametrize("mutation", ["header", "tag", "truncate", "append", "reorder"])
def test_complete_authentication_before_any_output(ring, mutation):
    value = bytearray(encoded(ring))
    header_end = len(MAGIC) + 4 + struct.unpack(">I", value[len(MAGIC) : len(MAGIC) + 4])[0]
    if mutation == "header":
        value[len(MAGIC) + 7] ^= 1
    elif mutation == "tag":
        value[-1] ^= 1
    elif mutation == "truncate":
        value = value[:-56]
    elif mutation == "append":
        value += b"extra"
    else:
        frame_size = 5 + 32 + 16
        first = value[header_end : header_end + frame_size]
        second = value[header_end + frame_size : header_end + 2 * frame_size]
        value[header_end : header_end + 2 * frame_size] = second + first
    target = io.BytesIO()
    with pytest.raises(InvalidObject):
        decrypt(io.BytesIO(value), target, ring, b"export:1:subject:2")
    assert target.getvalue() == b""


def test_foreign_context_rejected(ring):
    with pytest.raises(InvalidObject):
        decrypt(io.BytesIO(encoded(ring)), io.BytesIO(), ring, b"export:1:subject:other")


def test_rotation_changes_envelope_not_frames(ring):
    original = encoded(ring)
    new_ring = Keyring({"new": os.urandom(32)}, "new")
    changed = io.BytesIO()
    rewrap(io.BytesIO(original), changed, ring, new_ring, b"export:1:subject:2")
    result = changed.getvalue()

    def frames(value):
        return value[12 + struct.unpack(">I", value[8:12])[0] :]

    assert frames(result) == frames(original)
    out = io.BytesIO()
    decrypt(io.BytesIO(result), out, new_ring, b"export:1:subject:2")
    assert out.getvalue() == b"secret" * 100
    with pytest.raises(InvalidObject):
        decrypt(io.BytesIO(result), io.BytesIO(), ring, b"export:1:subject:2")


def test_size_limit_no_prefix_exposure(ring):
    out = io.BytesIO()
    with pytest.raises(InvalidObject):
        decrypt(io.BytesIO(encoded(ring)), out, ring, b"export:1:subject:2", max_bytes=50)
    assert not out.getvalue()


@pytest.mark.parametrize("damage", ["tag", "truncate", "append", "context", "key", "ceiling"])
def test_rotation_rejects_invalid_object_before_output(ring, damage):
    value = encoded(ring)
    context = b"export:1:subject:2"
    limit = 1000
    if damage == "tag":
        value = value[:-1] + bytes([value[-1] ^ 1])
    elif damage == "truncate":
        value = value[:-1]
    elif damage == "append":
        value += b"extra"
    elif damage == "context":
        context = b"export:1:subject:other"
    elif damage == "key":
        ring = Keyring({"old": os.urandom(32)}, "old")
    else:
        limit = 50
    target = io.BytesIO()
    new_ring = Keyring({"new": os.urandom(32)}, "new")
    with pytest.raises(InvalidObject):
        rewrap(io.BytesIO(value), target, ring, new_ring, context, max_bytes=limit)
    assert target.getvalue() == b""


def test_rotation_scratch_contains_only_ciphertext(ring, monkeypatch):
    from apps.safety.object_storage import codec

    original = encoded(ring)
    writes = []
    temporary_file = codec.tempfile.TemporaryFile

    class RecordingFile:
        def __init__(self):
            self.file = temporary_file()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.file.close()

        def write(self, value):
            writes.append(bytes(value))
            return self.file.write(value)

        def __getattr__(self, name):
            return getattr(self.file, name)

    monkeypatch.setattr(codec.tempfile, "TemporaryFile", RecordingFile)
    target = io.BytesIO()
    rewrap(
        io.BytesIO(original),
        target,
        ring,
        Keyring({"new": os.urandom(32)}, "new"),
        b"export:1:subject:2",
    )
    assert b"".join(writes) == original
    assert target.getvalue()
