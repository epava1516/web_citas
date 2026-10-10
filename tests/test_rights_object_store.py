"""Real private RustFS S3 integration; no fake object server."""

import io
import os
import subprocess
import time
from uuid import uuid4

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.object_storage.codec import InvalidObject, Keyring
from apps.safety.object_storage.repository import ObjectRepository


@pytest.fixture(scope="module")
def object_store(tmp_path_factory):
    name = "web-modelos-object-test-" + uuid4().hex[:12]
    access, secret = "synthetic" + os.urandom(16).hex(), os.urandom(32).hex()
    env = {
        **os.environ,
        "RUSTFS_ACCESS_KEY": access,
        "RUSTFS_SECRET_KEY": secret,
        "RUSTFS_CONSOLE_ENABLE": "false",
    }
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--pull=never",
                "-d",
                "--name",
                name,
                "--label",
                "web-modelos-object-tests",
                "--cpus",
                "0.5",
                "--memory",
                "512m",
                "--memory-swap",
                "512m",
                "--log-driver",
                "none",
                "--tmpfs",
                "/data:size=128m,uid=10001,gid=10001",
                "-p",
                "127.0.0.1::9000",
                "--tmpfs",
                "/logs:size=16m,uid=10001,gid=10001",
                "-e",
                "RUSTFS_ACCESS_KEY",
                "-e",
                "RUSTFS_SECRET_KEY",
                "-e",
                "RUSTFS_CONSOLE_ENABLE",
                "rustfs/rustfs@sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c",
            ],
            env=env,
            capture_output=True,
            check=True,
            timeout=30,
        )
        port = (
            subprocess.check_output(["docker", "port", name, "9000"], text=True)
            .strip()
            .rsplit(":", 1)[1]
        )
        client = boto3.client(
            "s3",
            endpoint_url=f"http://127.0.0.1:{port}",
            region_name="us-east-1",
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                connect_timeout=1,
                read_timeout=3,
                retries={"max_attempts": 0},
                request_checksum_calculation="when_required",
            ),
        )
        deadline = time.monotonic() + 30
        while True:
            try:
                client.create_bucket(Bucket="rights-test")
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.25)
        ring = Keyring({"v1": os.urandom(32)}, "v1")
        yield ObjectRepository(client, "rights-test", ring, Fernet(Fernet.generate_key()))
    finally:
        subprocess.run(["docker", "rm", "-f", "-v", name], capture_output=True, timeout=30)
        assert subprocess.run(["docker", "inspect", name], capture_output=True).returncode != 0


def test_actual_s3_immutable_put_private_read_rotation_purge_and_restore_replay(object_store):
    repo = object_store
    repo.validate_bucket()
    content, context = os.urandom(1048593), b"export/own/image/one"
    ref = repo.write(io.BytesIO(content), context)
    descriptor = repo.descriptor(ref)
    original = repo.client.get_object(Bucket=repo.bucket, Key=descriptor["key"])["Body"].read()
    assert content[:100] not in original
    with pytest.raises(ClientError) as denied:
        repo.client.put_object(
            Bucket=repo.bucket, Key=descriptor["key"], Body=b"bad", IfNoneMatch="*"
        )
    assert denied.value.response["ResponseMetadata"]["HTTPStatusCode"] == 412
    target = io.BytesIO()
    assert repo.read(ref, target, context) == len(content)
    assert target.getvalue() == content
    with pytest.raises(InvalidObject):
        repo.read(ref, io.BytesIO(), b"export/foreign/image/one")
    ring = Keyring({"v2": os.urandom(32)}, "v2")
    rotated = repo.rotate(ref, context, ring)
    repo.ring = ring
    target = io.BytesIO()
    repo.read(rotated, target, context)
    assert target.getvalue() == content
    repo.purge(ref)
    repo.purge(ref)  # Idempotent absent object; tombstone retained.
    with pytest.raises(ClientError):
        repo.client.head_object(Bucket=repo.bucket, Key=descriptor["key"])
    # Restoring old object bytes cannot revive an independently retained purge tombstone.
    repo.client.put_object(
        Bucket=repo.bucket, Key=descriptor["key"], Body=original, IfNoneMatch="*"
    )
    with pytest.raises(InvalidObject, match="purged"):
        repo.read(ref, io.BytesIO(), context)
    repo.purge(ref)
    repo.purge(rotated)


def test_actual_s3_corruption_and_reference_tamper_release_no_bytes(object_store):
    repo = object_store
    context = b"export/own/part/1"
    ref = repo.write(io.BytesIO(b"private bytes" * 10000), context)
    descriptor = repo.descriptor(ref)
    repo.client.put_object(Bucket=repo.bucket, Key=descriptor["key"], Body=b"changed")
    target = io.BytesIO()
    with pytest.raises(InvalidObject):
        repo.read(ref, target, context)
    assert target.getvalue() == b""
    with pytest.raises(InvalidObject):
        repo.descriptor(ref[:-5] + "AAAAA")
    repo.purge(ref)


@pytest.mark.django_db(transaction=True)
def test_actual_export_data_packages_download_and_purge_s3(
    request, settings, monkeypatch, object_store
):
    from test_rights_data_parts import test_reviewed_large_copy_manifest_receipt_download_and_purge

    from apps.safety import rights_object_content

    settings.RIGHTS_OBJECT_STORAGE_ENABLED = True
    monkeypatch.setattr(rights_object_content, "repository", lambda: object_store)
    test_reviewed_large_copy_manifest_receipt_download_and_purge(request, settings, monkeypatch)
    assert not object_store.client.list_objects_v2(
        Bucket=object_store.bucket, Prefix="encrypted/v1/"
    ).get("Contents", [])
    assert object_store.client.list_objects_v2(
        Bucket=object_store.bucket, Prefix="tombstones/v1/"
    ).get("Contents", [])


def test_actual_s3_versioning_change_blocks_new_writes_and_physical_purge(object_store):
    repo = object_store
    bucket = "rights-versioned-" + uuid4().hex[:12]
    repo.client.create_bucket(Bucket=bucket)
    isolated = ObjectRepository(repo.client, bucket, repo.ring, repo.reference_cipher)
    reference = isolated.write(io.BytesIO(b"versioned synthetic"), b"own")
    key = isolated.descriptor(reference)["key"]
    original = isolated.client.get_object(Bucket=bucket, Key=key)["Body"].read()
    isolated.client.put_bucket_versioning(
        Bucket=bucket, VersioningConfiguration={"Status": "Enabled"}
    )
    assert isolated.client.get_bucket_versioning(Bucket=bucket)["Status"] == "Enabled"
    for status in ("Enabled", "Suspended"):
        if status == "Suspended":
            isolated.client.put_bucket_versioning(
                Bucket=bucket, VersioningConfiguration={"Status": status}
            )
        with pytest.raises(InvalidObject, match="Versioned"):
            isolated.write(io.BytesIO(b"new bytes"), b"own")
        with pytest.raises(InvalidObject, match="Versioned"):
            isolated.purge(reference)
        with pytest.raises(InvalidObject, match="Versioned"):
            isolated.delete_unreferenced(key)
        assert isolated.client.get_object(Bucket=bucket, Key=key)["Body"].read() == original
        assert len(isolated.client.list_object_versions(Bucket=bucket).get("Versions", [])) == 1
        assert not isolated.client.list_objects_v2(Bucket=bucket, Prefix="tombstones/").get(
            "Contents"
        )


@pytest.mark.parametrize("mode", ["Enabled", "Suspended", "Unknown", "lock", "denied"])
def test_unsupported_bucket_guards_never_mutate_client(mode):
    class GuardClient:
        def get_bucket_versioning(self, **kwargs):
            return {"Status": mode} if mode in {"Enabled", "Suspended", "Unknown"} else {}

        def get_object_lock_configuration(self, **kwargs):
            if mode == "denied":
                raise ClientError({"Error": {"Code": "AccessDenied"}}, "GetObjectLockConfiguration")
            return {"ObjectLockConfiguration": {"ObjectLockEnabled": "Enabled"}}

        def put_object(self, **kwargs):
            pytest.fail("Rejected bucket must never upload")

        def delete_object(self, **kwargs):
            pytest.fail("Rejected bucket must never delete")

    repo = ObjectRepository(
        GuardClient(), "own", Keyring({"v1": os.urandom(32)}, "v1"), Fernet(Fernet.generate_key())
    )
    with pytest.raises((InvalidObject, ClientError)):
        repo.write(io.BytesIO(b"own"), b"own")
    with pytest.raises((InvalidObject, ClientError)):
        repo.purge("invalid-ref")
    with pytest.raises((InvalidObject, ClientError)):
        repo.delete_unreferenced("encrypted/v1/" + "a" * 32)
