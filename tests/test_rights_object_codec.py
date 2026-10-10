import io
import os
import struct

import pytest

from apps.safety.object_storage.codec import MAGIC, InvalidObject, Keyring, decrypt, encrypt, rewrap


@pytest.fixture
def ring():
    return Keyring({"old": os.urandom(32)}, "old")


def encoded(ring, content=b"secret" * 100):
    target = io.BytesIO()
    encrypt(io.BytesIO(content), target, ring, b"export:1:subject:2", chunk_size=32)
    return target.getvalue()


@pytest.mark.parametrize("content", [b"", b"a", b"abc" * 1000, os.urandom(1048577)])
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
