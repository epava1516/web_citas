"""Finite private artifact writes; kernel file ceiling is applied by the controller."""

import hashlib
import io
import os
import tarfile
from pathlib import Path

MAX_FILE_BYTES = 32 * 1024 ** 2
MAX_FILES = 100
ARCHIVE_MAX_BYTES = 256 * 1024 ** 2
RESERVED = frozenset({"report.json"})
VIRTUAL_FILESYSTEMS = {"proc", "sysfs", "cgroup2", "devpts", "mqueue"}
DOCKER_RUNTIME_FILES = {"/etc/hosts", "/etc/hostname", "/etc/resolv.conf"}


def _check(name, data, existing):
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("Artifact must have a single local filename")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("Artifact exceeds the declared file ceiling")
    limit = MAX_FILES if name in RESERVED else MAX_FILES - len(RESERVED)
    if existing >= limit:
        raise ValueError("Artifact count exceeds the declared ceiling")


def write_artifact(directory, name, text):
    directory = Path(directory)
    destination = directory / name
    data = text.encode("utf-8")
    if Path(name).name == name and destination.is_symlink():
        raise ValueError("Artifact must not follow a symlink")
    _check(name, data, 0 if destination.exists() else sum(1 for _ in directory.iterdir()))
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class ArchiveSink:
    """Append members to one pre-existing bound tar file; RLIMIT_FSIZE caps it in the kernel."""

    def __init__(self, path):
        descriptor = os.open(path, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)  # Never creates.
        self.stream = os.fdopen(descriptor, "wb")
        self.archive = tarfile.open(fileobj=self.stream, mode="w", format=tarfile.PAX_FORMAT)
        self.receipts = {}

    def write(self, name, text):
        data = text.encode("utf-8")
        _check(name, data, len(self.receipts) - (name in self.receipts))
        member = tarfile.TarInfo(name)
        member.size, member.mode = len(data), 0o600
        self.archive.addfile(member, io.BytesIO(data))
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.receipts[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        return self.receipts[name]

    def close(self):
        self.archive.close()
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.stream.close()


def parse_mountinfo(text):
    mounts = {}
    for line in text.splitlines():
        left, _, right = line.partition(" - ")
        fields, tail = left.split(), right.split()
        mounts[fields[4]] = {"device": fields[2], "options": set(fields[5].split(",")), "fstype": tail[0],
                             "super": dict(item.partition("=")[::2] for item in tail[2].split(","))}
    return mounts


def tmpfs_bytes(entry):
    size = entry["super"].get("size")
    if not size:
        raise ValueError("tmpfs without size= is unbounded")
    unit = {"k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}.get(size[-1].lower(), 1)
    return int(size[:-1] if size[-1].isalpha() else size) * unit


def writable_storage(mounts, allowed=()):
    """Writable tmpfs is kernel-bounded, counted once per device; other writes must be allowed."""
    bounded, unbounded, devices = {}, [], set()
    for point, entry in mounts.items():
        if "rw" not in entry["options"] or entry["fstype"] in VIRTUAL_FILESYSTEMS or point in allowed:
            continue
        if entry["fstype"] == "tmpfs":
            if entry.get("device") not in devices:  # File binds from /dev share its superblock.
                devices.add(entry.get("device"))
                bounded[point] = tmpfs_bytes(entry)
        elif point not in DOCKER_RUNTIME_FILES:
            unbounded.append(point)
    return bounded, unbounded
