"""Operator-only AUX extraction. Web readers never start native processes."""

import base64
import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

from scripts.decode_retained_rdb_origin import decoder_limits, private_file

COLLECTOR_SOURCE_SHA256 = "41825a8c72d6171881ea36221419d2561cf2c52b1549bbec59cfcd0a7a38c318"


def collect_aux(body, reconstruction, decoder, *, decoder_sha256):
    raw = base64.b64decode(body["content_base64"], validate=True)
    if (
        len(raw) > 64 * 1024 * 1024
        or hashlib.sha256(raw).hexdigest() != reconstruction["source_sha256"]
        or body["captured_at"] != reconstruction["captured_at"]
    ):
        raise ValueError("AUX source must match reconstructed RDB")
    decoder = Path(decoder)
    info = decoder.lstat()
    if (
        not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) & 0o022
        or hashlib.sha256(decoder.read_bytes()).hexdigest() != decoder_sha256
    ):
        raise ValueError("Pinned owned AUX collector required")
    with tempfile.TemporaryDirectory(prefix="web-modelos-rdb-aux-") as folder:
        directory = Path(folder)
        source = directory / "source.rdb"
        with private_file(source) as stream:
            stream.write(raw)
        with private_file(directory / "aux.private") as output, private_file(directory / "errors.private") as errors:
            result = subprocess.run(
                [str(decoder.absolute()), str(source)], stdin=subprocess.DEVNULL,
                stdout=output, stderr=errors, cwd=directory,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                timeout=15, preexec_fn=decoder_limits, check=False,
            )
            if result.returncode:
                raise ValueError("AUX collector failed; partial output is not accepted")
            output.seek(0)
            encoded = output.read(3 * 1024 * 1024 + 1)
            if len(encoded) > 3 * 1024 * 1024:
                raise ValueError("AUX output limit exceeded")
    entries = json.loads(encoded)
    # The native collector emits fixed JSON keys and hex bytes; field duplicates
    # are separate entries, not silently overwritten object properties.
    metadata = {
        "schema": "local-redis-rdb-aux-v1", "source_sha256": reconstruction["source_sha256"],
        "source_origin_sha256": reconstruction["source_origin_sha256"],
        "captured_at": reconstruction["captured_at"], "entries": entries,
        "entries_sha256": hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest(),
        "collector_source_sha256": COLLECTOR_SOURCE_SHA256,
        "collector_binary_sha256": decoder_sha256, "partial": True,
    }
    from apps.safety.retained_redis_metadata import checked_aux

    checked_aux(metadata, reconstruction)
    return reconstruction | {"schema": "local-redis-rdb-reconstruction-v2", "aux_metadata": metadata}
