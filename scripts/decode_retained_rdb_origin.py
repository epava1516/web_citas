"""Operator-only bounded RDB decoding; reconstructed RESP is never executed.

The web application must consume reviewed encrypted material, not launch this
native parser. Physical expired values remain available for source review.
"""

import base64
import ctypes
import hashlib
import json
import os
import resource
import stat
import subprocess
import tempfile
import time
from pathlib import Path

MAX_RDB_BYTES = 64 * 1024 * 1024
MAX_RESP_BYTES = 8 * 1024 * 1024
PARSER_COMMIT = "bc5f295c98b40c2c33099d9d72ab30ce9e595dc7"
PARSER_VERSION = "2.4.0"


def decoder_limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_RESP_BYTES, MAX_RESP_BYTES))
    if ctypes.CDLL(None).prctl(38, 1, 0, 0, 0):  # Linux PR_SET_NO_NEW_PRIVS.
        raise RuntimeError("Native decoder privilege guard unavailable")


def private_file(path):
    return os.fdopen(os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600), "w+b")


def decode_body(body, decoder, *, decoder_sha256):
    """Return bounded reconstruction plus provenance, without claiming coverage."""
    started = time.perf_counter()
    common = {"schema", "project", "captured_at", "content_base64", "sha256", "partial"}
    if not isinstance(body, dict):
        raise ValueError("Retained RDB object required")
    extra = {"manifest", "source_name"} if body.get("schema") == "local-redis-base-origin-v1" else set()
    if (
        set(body) != common | extra
        or body["schema"] not in {"local-redis-snapshot-origin-v1", "local-redis-base-origin-v1"}
        or body["project"] != "web-modelos"
        or body["partial"] is not True
    ):
        raise ValueError("Exact partial retained RDB origin required")
    raw = base64.b64decode(body["content_base64"], validate=True)
    if len(raw) > MAX_RDB_BYTES or hashlib.sha256(raw).hexdigest() != body["sha256"]:
        raise ValueError("Retained RDB content changed")
    decoder = Path(decoder)
    metadata = decoder.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) & 0o022
        or hashlib.sha256(decoder.read_bytes()).hexdigest() != decoder_sha256
    ):
        raise ValueError("Pinned owned native decoder required")
    with tempfile.TemporaryDirectory(prefix="web-modelos-rdb-decode-") as folder:
        directory = Path(folder)
        source_path = directory / "source.rdb"
        with private_file(source_path) as source:
            source.write(raw)
            source.flush()
        with private_file(directory / "resp.private") as output, private_file(directory / "errors.private") as errors:
            completed = subprocess.run(
                [str(decoder.absolute()), str(source_path), "resp"],
                stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, cwd=directory,
                timeout=15, check=False, preexec_fn=decoder_limits,
            )
            if completed.returncode:
                raise ValueError("Retained RDB decoder failed; no accepted reconstruction")
            output.seek(0)
            reconstructed = output.read(MAX_RESP_BYTES + 1)
            if len(reconstructed) > MAX_RESP_BYTES:
                raise ValueError("Retained RDB reconstruction exceeds bound")
    return {
        "schema": "local-redis-rdb-reconstruction-v1",
        "source_kind": "rdb_snapshot_state",
        "source_schema": body["schema"],
        "source_sha256": body["sha256"],
        "source_origin_sha256": hashlib.sha256(
            json.dumps(body, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        "captured_at": body["captured_at"],
        "representation": "reconstructed-resp-not-original-command-history",
        "content_base64": base64.b64encode(reconstructed).decode(),
        "sha256": hashlib.sha256(reconstructed).hexdigest(),
        "decoder": {"version": PARSER_VERSION, "source_commit": PARSER_COMMIT, "binary_sha256": decoder_sha256},
        "partial": True,
        "pending": ["snapshot_metadata_scope_review", "historical_redis_coverage"],
        "decoder_observed_seconds": time.perf_counter() - started,
    }
