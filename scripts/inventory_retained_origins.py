"""Fingerprint explicitly supplied retained ciphertexts; never infer subject or coverage."""

import argparse
import hashlib
import json
import os
import stat
import time
from datetime import UTC, datetime
from pathlib import Path

MAX_BYTES = 256 * 1024 * 1024


def inspect_origin(path):
    path = Path(path)
    if path.suffix != ".encrypted":
        raise ValueError("Only explicit encrypted origins are supported")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or stat.S_IMODE(before.st_mode) & 0o077
            or before.st_size > MAX_BYTES
        ):
            raise ValueError("Unsafe or oversized retained origin")
        digest = hashlib.sha256()
        size = 0
        while block := source.read(64 * 1024):
            size += len(block)
            if size > MAX_BYTES:
                raise ValueError("Retained origin grew beyond limit")
            digest.update(block)
        after = os.fstat(source.fileno())

        def identity(row):
            return (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_ctime_ns)

        if identity(before) != identity(after) or size != before.st_size:
            raise ValueError("Retained origin changed during inventory")
        if identity(after) != identity(path.lstat()):
            raise ValueError("Retained origin path changed during inventory")
    return {"path": str(path.absolute()), "bytes": size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    rows = [inspect_origin(path) for path in args.origin]
    body = {
        "schema": "retained-origin-inventory-v1",
        "observed_at": datetime.now(UTC).isoformat(),
        "origins": rows,
        "partial": True,
        "subject_association_verified": False,
        "pending": ["other_retained_sources", "subject_association", "retention_authority"],
        "observed_seconds": time.monotonic() - started,
    }
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(body, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    print(
        json.dumps(
            {
                "origins": len(rows),
                "bytes": sum(row["bytes"] for row in rows),
                "partial": True,
                "observed_seconds": body["observed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
