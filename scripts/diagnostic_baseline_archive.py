"""Bounded USTAR reader: rejects extended headers before parsing their payload."""
import json
import os

from diagnostic_baseline_codec import LIMIT

BLOCK = 512
MAX_MEMBERS = 256
MAX_MEMBER_BYTES = 32 * 1024 ** 2


def _octal(value):
    value = value.strip(b'\0 ')
    if not value or any(byte not in b'01234567' for byte in value):
        raise ValueError('Baseline USTAR numeric field invalid')
    return int(value, 8)


class Reader:
    def __init__(self, path):
        self.stream = open(path, 'rb')
        try:
            size = os.fstat(self.stream.fileno()).st_size
            if not 0 < size <= LIMIT:
                raise ValueError('Baseline archive aggregate bound invalid')
            members = {}
            while True:
                header = self.stream.read(BLOCK)
                if len(header) != BLOCK:
                    raise ValueError('Baseline USTAR footer missing')
                if not any(header):
                    if self.stream.read(BLOCK) != b'\0' * BLOCK:
                        raise ValueError('Baseline USTAR footer invalid')
                    while tail := self.stream.read(4096):
                        if any(tail):
                            raise ValueError('Baseline USTAR trailing data invalid')
                    break
                # No PAX/GNU extended headers, symlinks, directory/prefix names or
                # base256 sizes: inspect these fixed512 bytes before any payload.
                if (header[156:157] not in (b'0', b'\0')
                    or header[257:265] != b'ustar\x0000' or any(header[345:500])
                    or any(header[157:257])):
                    raise ValueError('Baseline requires simple regular USTAR entries')
                if _octal(header[148:156]) != sum(header[:148]) + 8 * 32 + sum(header[156:]):
                    raise ValueError('Baseline USTAR checksum invalid')
                name = header[:100].split(b'\0', 1)[0].decode('ascii')
                if not name or '/' in name or name in ('.', '..') or name in members or len(members) >= MAX_MEMBERS:
                    raise ValueError('Baseline USTAR member list invalid')
                length = _octal(header[124:136])
                offset = self.stream.tell()
                padded = (length + BLOCK - 1) // BLOCK * BLOCK
                if length > MAX_MEMBER_BYTES or offset + padded > size:
                    raise ValueError('Baseline USTAR member bound invalid')
                members[name] = (offset, length)
                self.stream.seek(padded, 1)
            offset, length = members['baseline.index.json']
            if length > 65536:
                raise ValueError('Baseline index invalid')
            self.stream.seek(offset)
            parts = json.loads(self.stream.read(length))['parts']
            if (not isinstance(parts, list) or not parts or len(parts) > 32
                or any(not isinstance(name, str) for name in parts)
                or len(set(parts)) != len(parts)):
                raise ValueError('Baseline fragment count invalid')
            total, self.parts = 0, []
            for number, name in enumerate(parts):
                if name != f'baseline.{number:04}.bin':
                    raise ValueError('Baseline fragment order invalid')
                offset, length = members[name]
                if not 0 < length <= 8 * 1024 ** 2:
                    raise ValueError('Baseline fragment bound invalid')
                self.parts.append((offset, length))
                total += length
            if total > LIMIT:
                raise ValueError('Baseline exceeds aggregate bound')
            self.index, self.remaining = 0, 0
        except Exception:
            self.stream.close()
            raise

    def read(self, size):
        if size < 0 or size > 4 * 1024 ** 2 + 17:
            raise ValueError('Baseline reader requires bounded reads')
        result = bytearray()
        while len(result) < size:
            if not self.remaining:
                if self.index == len(self.parts):
                    break
                offset, self.remaining = self.parts[self.index]
                self.stream.seek(offset)
                self.index += 1
            block = self.stream.read(min(size - len(result), self.remaining))
            if not block:
                raise ValueError('Baseline fragment truncated during read')
            self.remaining -= len(block)
            result.extend(block)
        return bytes(result)

    def close(self):
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
