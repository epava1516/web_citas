"""Versioned, envelope encrypted AES-GCM frames with authenticated EOF.

No bytes reach the destination until every frame and the EOF commitment verify.
Keys and context are provided by the domain, never inferred from ciphertext.
"""

import base64
import hashlib
import json
import os
import struct
import tempfile
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"WMAEAD01"
MAX_HEADER = 4096
MAX_CHUNK = 1024 * 1024
MAX_BYTES = 1024 * 1024 * 1024


class InvalidObject(ValueError):
    """Missing, corrupt, foreign, oversized or unsupported encrypted object."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def _b64(value):
    return base64.b64encode(value).decode("ascii")


def _unb64(value):
    return base64.b64decode(value, validate=True)


def _read(source, size):
    if size <= 0:
        return b""
    first = source.read(size)
    if not first:
        raise InvalidObject("Truncated object")
    if len(first) >= size:
        return bytes(first)
    second = source.read(size - len(first))
    if not second:
        raise InvalidObject("Truncated object")
    # The bounded object adapter usually splits a frame at one fetch boundary.
    # Join those two byte strings once instead of growing and copying a bytearray.
    # Keep fragmented/custom buffer readers on the original bounded accumulator.
    if isinstance(first, bytes) and isinstance(second, bytes) and len(first) + len(second) >= size:
        return first + second
    value = bytearray(first)
    value.extend(second)
    while len(value) < size:
        chunk = source.read(size - len(value))
        if not chunk:
            raise InvalidObject("Truncated object")
        value.extend(chunk)
    return bytes(value)


@dataclass(frozen=True)
class Keyring:
    keys: dict
    active: str

    def key(self, key_id):
        try:
            key = self.keys[key_id]
        except KeyError:
            raise InvalidObject("Unavailable envelope key") from None
        if len(key) != 32:
            raise InvalidObject("Envelope key must be AES-256")
        return key


def _metadata(context, chunk, prefix):
    return {
        "v": 1,
        "chunk": chunk,
        "prefix": _b64(prefix),
        "context": hashlib.sha256(context).hexdigest(),
    }


def _wrapped(meta, dek, ring):
    nonce = os.urandom(12)
    wrapper = {"key": ring.active, "nonce": _b64(nonce)}
    wrapper["dek"] = _b64(
        AESGCM(ring.key(ring.active)).encrypt(
            nonce, dek, _canonical({"meta": meta, "key": ring.active})
        )
    )
    return {"meta": meta, "wrapper": wrapper}


def _header(source, ring, context):
    if _read(source, len(MAGIC)) != MAGIC:
        raise InvalidObject("Unsupported object format")
    length = struct.unpack(">I", _read(source, 4))[0]
    if not 0 < length <= MAX_HEADER:
        raise InvalidObject("Invalid header size")
    try:
        encoded = _read(source, length)
        header = json.loads(encoded)
        if _canonical(header) != encoded or set(header) != {"meta", "wrapper"}:
            raise InvalidObject("Noncanonical header")
        meta, wrapper = header["meta"], header["wrapper"]
        if set(meta) != {"v", "chunk", "prefix", "context"}:
            raise InvalidObject("Invalid metadata")
        if (
            meta["v"] != 1
            or type(meta["chunk"]) is not int
            or not 1 <= meta["chunk"] <= MAX_CHUNK
            or meta["context"] != hashlib.sha256(context).hexdigest()
        ):
            raise InvalidObject("Unsupported or foreign metadata")
        prefix = _unb64(meta["prefix"])
        if len(prefix) != 4 or set(wrapper) != {"key", "nonce", "dek"}:
            raise InvalidObject("Invalid envelope")
        dek = AESGCM(ring.key(wrapper["key"])).decrypt(
            _unb64(wrapper["nonce"]),
            _unb64(wrapper["dek"]),
            _canonical({"meta": meta, "key": wrapper["key"]}),
        )
        if len(dek) != 32:
            raise InvalidObject("Invalid data key")
        return meta, dek, prefix
    except (ValueError, TypeError, KeyError, InvalidTag) as error:
        raise InvalidObject("Object header authentication failed") from error


def _write_header(target, header):
    encoded = _canonical(header)
    if len(encoded) > MAX_HEADER:
        raise InvalidObject("Header too large")
    target.write(MAGIC + struct.pack(">I", len(encoded)) + encoded)


def _aad(meta, index, kind, length):
    return _canonical(meta) + struct.pack(">QBI", index, kind, length)


def encrypt(source, target, ring, context, *, chunk_size=MAX_CHUNK, max_bytes=MAX_BYTES):
    if not isinstance(context, bytes) or not context:
        raise ValueError("Explicit nonempty byte context required")
    if not 1 <= chunk_size <= MAX_CHUNK:
        raise ValueError("Invalid chunk size")
    prefix, dek = os.urandom(4), AESGCM.generate_key(bit_length=256)
    meta = _metadata(context, chunk_size, prefix)
    _write_header(target, _wrapped(meta, dek, ring))
    aes, digest, total, index = AESGCM(dek), hashlib.sha256(), 0, 0
    while block := source.read(chunk_size):
        if len(block) > chunk_size:
            raise InvalidObject("Reader exceeded block limit")
        total += len(block)
        if total > max_bytes:
            raise InvalidObject("Object exceeds size limit")
        digest.update(block)
        encrypted = aes.encrypt(
            prefix + struct.pack(">Q", index), block, _aad(meta, index, 1, len(block))
        )
        target.write(struct.pack(">BI", 1, len(encrypted)) + encrypted)
        index += 1
    final = struct.pack(">Q", total) + digest.digest()
    encrypted = aes.encrypt(
        prefix + struct.pack(">Q", index), final, _aad(meta, index, 0, len(final))
    )
    target.write(struct.pack(">BI", 0, len(encrypted)) + encrypted)
    return total


def _authenticate_frames(source, aes, digest, meta, prefix, max_bytes, verified):
    """One authentication machine; optional private plaintext staging only.

    ``verified`` is either the read API's own tempfile or explicit None for
    verification without output. No external sink or consumer callback is used.
    """
    total, index = 0, 0
    while True:
        kind, size = struct.unpack(">BI", _read(source, 5))
        if kind not in {0, 1} or (kind == 0 and size != 56):
            raise InvalidObject("Invalid frame")
        if kind == 1 and not 17 <= size <= meta["chunk"] + 16:
            raise InvalidObject("Invalid block size")
        try:
            block = aes.decrypt(
                prefix + struct.pack(">Q", index),
                _read(source, size),
                _aad(meta, index, kind, size - 16),
            )
        except InvalidTag as error:
            raise InvalidObject("Block authentication failed") from error
        if kind == 0:
            if block != struct.pack(">Q", total) + digest.digest() or source.read(1):
                raise InvalidObject("Invalid object commitment or trailing bytes")
            break
        total += len(block)
        if total > max_bytes:
            raise InvalidObject("Object exceeds size limit")
        digest.update(block)
        if verified is not None:
            verified.write(block)
        index += 1
    return total


def decrypt(source, target, ring, context, *, max_bytes=MAX_BYTES):
    meta, dek, prefix = _header(source, ring, context)
    aes, digest = AESGCM(dek), hashlib.sha256()
    # Disk tempfile, no unbounded memory and no authenticated-prefix exposure.
    with tempfile.TemporaryFile() as verified:
        total = _authenticate_frames(source, aes, digest, meta, prefix, max_bytes, verified)
        verified.seek(0)
        while block := verified.read(MAX_CHUNK):
            target.write(block)
    return total


def verify(source, ring, context, *, max_bytes=MAX_BYTES):
    """Authenticate every byte/frame/EOF without plaintext staging or output."""
    meta, dek, prefix = _header(source, ring, context)
    aes, digest = AESGCM(dek), hashlib.sha256()
    return _authenticate_frames(source, aes, digest, meta, prefix, max_bytes, None)


def rewrap(source, target, old_ring, new_ring, context, *, max_bytes=MAX_BYTES):
    """Authenticate fully first, then replace only the wrapped DEK."""
    with tempfile.TemporaryFile() as copy:
        size = 0
        while block := source.read(MAX_CHUNK):
            size += len(block)
            if size > max_bytes + MAX_HEADER + (max_bytes // 1 + 1) * 21:
                raise InvalidObject("Ciphertext exceeds size limit")
            copy.write(block)
        copy.seek(0)
        verify(copy, old_ring, context, max_bytes=max_bytes)
        copy.seek(0)
        meta, dek, _ = _header(copy, old_ring, context)
        _write_header(target, _wrapped(meta, dek, new_ring))
        while block := copy.read(MAX_CHUNK):
            target.write(block)
