"""Synthetic RDB from an owned Redis process with no TCP listener."""

import base64
import hashlib
import os
import subprocess
import time
from pathlib import Path

import redis


def native_decoder():
    return Path(os.environ["RETAINED_RDB_DECODER_BIN"]), os.environ["RETAINED_RDB_DECODER_SHA256"]


def capture(directory, captured_at, values):
    directory.mkdir(mode=0o700)
    socket = directory / "redis.sock"
    with (directory / "redis.private.log").open("wb") as log:
        process = subprocess.Popen(
            ["/usr/bin/redis-server", "--port", "0", "--unixsocket", str(socket),
             "--unixsocketperm", "700", "--dir", str(directory), "--save", "",
             "--appendonly", "no", "--dbfilename", "fixture.rdb"],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log,
        )
        client = redis.Redis(unix_socket_path=str(socket), socket_timeout=1)
        try:
            deadline = time.monotonic() + 5
            while True:
                try:
                    client.ping()
                    break
                except redis.ConnectionError:
                    if process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("Owned fixture Redis failed to start") from None
                    time.sleep(0.02)
            client.rpush("fixture:q", *values)
            expiration = int(time.time() * 1000) + 500
            client.pexpireat("fixture:q", expiration)
            client.save()
            raw = (directory / "fixture.rdb").read_bytes()
        finally:
            client.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    # The physical capture survives expiry; do not load it into a server.
    remaining = expiration / 1000 - time.time()
    if remaining > 0:
        time.sleep(remaining + 0.01)
    return {
        "schema": "local-redis-snapshot-origin-v1", "project": "web-modelos",
        "captured_at": captured_at.isoformat(), "sha256": hashlib.sha256(raw).hexdigest(),
        "content_base64": base64.b64encode(raw).decode(), "partial": True,
    }, expiration
