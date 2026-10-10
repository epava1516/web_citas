"""Bounded AEAD framing for private diagnostic snapshots; no Django imports."""
import hashlib
import json
import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b'MOD08BASELINE1\n'
CHUNK = 4 * 1024 ** 2
LIMIT = 256 * 1024 ** 2
PLAINTEXT_LIMIT = 512 * 1024 ** 2


def key(path):
    info = os.stat(path, follow_symlinks=False)
    if info.st_mode & 0o077 or info.st_size != 32:
        raise ValueError('Baseline key must be a private32-byte regular file')
    import stat
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Baseline key must be regular')
    with open(path, 'rb') as file:
        return file.read(32)


def encode(source, target, metadata, secret):
    aes, prefix, digest = AESGCM(secret), os.urandom(8), hashlib.sha256()
    target.write(MAGIC + prefix)
    total, number = len(MAGIC) + 8, 0
    def record(kind, data):
        nonlocal number, total
        nonce = prefix + number.to_bytes(4, 'big')
        value = aes.encrypt(nonce, kind + data, MAGIC + number.to_bytes(4, 'big'))
        total += len(value) + 4
        if total > LIMIT:
            raise ValueError('Baseline exceeds256MiB quota')
        target.write(struct.pack('!I', len(value)) + value)
        number += 1
    header = json.dumps(metadata, sort_keys=True, separators=(',', ':')).encode()
    if len(header) > CHUNK:
        raise ValueError('Baseline metadata exceeds bound')
    record(b'M', header)
    while block := source.read(CHUNK):
        digest.update(block)
        record(b'D', block)
    record(b'F', digest.digest())


def records(source, secret):
    if source.read(len(MAGIC)) != MAGIC:
        raise ValueError('Baseline format mismatch')
    prefix = source.read(8)
    if len(prefix) != 8:
        raise ValueError('Baseline truncated')
    aes, number, total = AESGCM(secret), 0, len(MAGIC) + 8
    while True:
        length = source.read(4)
        if len(length) != 4:
            raise ValueError('Baseline missing authenticated end')
        size = struct.unpack('!I', length)[0]
        total += 4 + size
        if size < 17 or size > CHUNK + 17 or total > LIMIT:
            raise ValueError('Baseline chunk bounds invalid')
        encrypted = source.read(size)
        if len(encrypted) != size:
            raise ValueError('Baseline truncated')
        value = aes.decrypt(prefix + number.to_bytes(4, 'big'), encrypted,
                            MAGIC + number.to_bytes(4, 'big'))
        number += 1
        yield value[:1], value[1:]
        if value[:1] == b'F':
            if source.read(1):
                raise ValueError('Baseline trailing data')
            return


def metadata(source, secret):
    kind, value = next(records(source, secret))
    if kind != b'M':
        raise ValueError('Baseline metadata missing')
    return json.loads(value)


def decode(source, target, secret):
    digest, header = hashlib.sha256(), None
    for kind, value in records(source, secret):
        if kind == b'M' and header is None:
            header = json.loads(value)
        elif kind == b'D' and header is not None:
            digest.update(value)
            target.write(value)
        elif kind == b'F' and header is not None and value == digest.digest():
            return header
        else:
            raise ValueError('Baseline frame order/integrity invalid')
    raise ValueError('Baseline incomplete')
