"""Read only explicitly indexed bounded encrypted fragments from an owned archive."""
import json
import tarfile

from diagnostic_baseline_codec import LIMIT


class Reader:
    def __init__(self, path):
        self.archive = tarfile.open(path, 'r:')
        names = set()
        for member in self.archive:
            if len(names) >= 100 or member.name in names:
                self.archive.close()
                raise ValueError('Baseline archive member list invalid')
            names.add(member.name)
        member = self.archive.getmember('baseline.index.json')
        if not member.isfile() or member.size > 65536:
            raise ValueError('Baseline index invalid')
        self.parts = json.load(self.archive.extractfile(member))['parts']
        if not self.parts or len(self.parts) > 32 or len(set(self.parts)) != len(self.parts):
            raise ValueError('Baseline fragment count invalid')
        total = 0
        for number, name in enumerate(self.parts):
            if name != f'baseline.{number:04}.bin':
                raise ValueError('Baseline fragment order invalid')
            value = self.archive.getmember(name)
            if not value.isfile() or not 0 < value.size <= 8 * 1024 ** 2:
                raise ValueError('Baseline fragment bound invalid')
            total += value.size
        if total > LIMIT:
            raise ValueError('Baseline exceeds aggregate bound')
        self.index, self.current = 0, None

    def read(self, size):
        if size < 0 or size > 4 * 1024 ** 2 + 17:
            raise ValueError('Baseline reader requires bounded reads')
        result = bytearray()
        while len(result) < size:
            if self.current is None:
                if self.index == len(self.parts):
                    break
                self.current = self.archive.extractfile(self.parts[self.index])
                self.index += 1
            block = self.current.read(size - len(result))
            if not block:
                self.current.close()
                self.current = None
            else:
                result.extend(block)
        return bytes(result)

    def close(self):
        if self.current:
            self.current.close()
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
