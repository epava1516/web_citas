"""Bounded generated-artifact identity, usable by standalone launchers."""

import hashlib
import os
import stat
from pathlib import Path

MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
CYTHON_VERSION = "3.0.12"
BUILD_FLAGS = ["-O3", "-fPIC", "-shared"]
MODULE = "apps.safety._canonical_kernel"


def artifact_fingerprints(root):
    directory = Path(root) / "apps/safety/_canonical_native"
    if directory.is_symlink():
        raise ValueError("Invalid canonical artifact directory")
    if not directory.exists():
        return {}
    if not directory.is_dir():
        raise ValueError("Invalid canonical artifact directory")
    result = {}
    entries = []
    for path in directory.iterdir():
        entries.append(path)
        if len(entries) > 3:
            raise ValueError("Unexpected canonical artifact entry")
    for path in sorted(entries):
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ARTIFACT_BYTES:
                raise ValueError("Invalid canonical artifact file")
            digest = hashlib.sha256()
            size = 0
            while chunk := os.read(descriptor, min(65536, MAX_ARTIFACT_BYTES + 1 - size)):
                size += len(chunk)
                if size > MAX_ARTIFACT_BYTES:
                    raise ValueError("Canonical artifact exceeds bound")
                digest.update(chunk)
            result[str(path.relative_to(root))] = digest.hexdigest()
        finally:
            os.close(descriptor)
    return result
