"""S3-compatible private repository with authenticated compact references."""

import hashlib
import json
import re
import tempfile
from contextlib import contextmanager
from uuid import uuid4

from botocore.exceptions import ClientError

from .codec import MAX_CHUNK, InvalidObject, decrypt, encrypt, rewrap, verify

PREFIX = "wmblob1:"
KEY = re.compile(r"^encrypted/v1/[0-9a-f]{32}$")


class _HashedBodyReader:
    """Bounded codec adapter; physical fetches retain the native MAX_CHUNK size.

    Every fetched byte is counted/hashed once, including bytes the codec rejects
    before consuming. A physical failure is sticky: draining never retries IO.
    """

    def __init__(self, body, expected):
        self.body, self.expected = body, expected
        self.size, self.digest = 0, hashlib.sha256()
        self.buffer, self.offset = b"", 0
        self.eof, self.failure = False, None

    def _fetch(self):
        if self.failure is not None:
            raise self.failure
        if self.eof:
            return False
        try:
            block = self.body.read(MAX_CHUNK)
            if not block:
                self.eof = True
                self.buffer, self.offset = b"", 0
                return False
            self.size += len(block)
            if self.size > self.expected["bytes"]:
                raise InvalidObject("Object grew")
            self.digest.update(block)
            self.buffer, self.offset = block, 0
            return True
        except Exception as error:
            self.failure = error
            raise

    def read(self, size):
        if size == 0:
            return b""
        if self.offset == len(self.buffer) and not self._fetch():
            return b""
        end = min(self.offset + size, len(self.buffer))
        value = self.buffer[self.offset:end]
        self.offset = end
        return value

    def finish(self):
        # The unread buffer is already physically counted and hashed.
        self.buffer, self.offset = b"", 0
        while self._fetch():
            self.buffer, self.offset = b"", 0
        if self.size != self.expected["bytes"] or self.digest.hexdigest() != self.expected["sha256"]:
            raise InvalidObject("Object digest mismatch")


class ObjectRepository:
    def __init__(self, client, bucket, ring, reference_cipher):
        self.client, self.bucket, self.ring = client, bucket, ring
        self.reference_cipher = reference_cipher

    def descriptor(self, reference):
        try:
            if not reference.startswith(PREFIX):
                raise InvalidObject("Not an object reference")
            value = json.loads(self.reference_cipher.decrypt(reference[len(PREFIX) :].encode()))
            if (
                set(value) != {"v", "key", "sha256", "bytes"}
                or value["v"] != 1
                or not KEY.fullmatch(value["key"])
                or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])
                or type(value["bytes"]) is not int
                or value["bytes"] < 1
            ):
                raise InvalidObject("Invalid reference")
            return value
        except Exception as error:
            raise InvalidObject("Object reference authentication failed") from error

    def _upload(self, stream):
        digest, size = hashlib.sha256(), 0
        stream.seek(0)
        while block := stream.read(MAX_CHUNK):
            digest.update(block)
            size += len(block)
        stream.seek(0)
        key = "encrypted/v1/" + uuid4().hex
        self.validate_bucket()
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=stream,
            ContentLength=size,
            ContentType="application/octet-stream",
            IfNoneMatch="*",
        )
        value = {"v": 1, "key": key, "sha256": digest.hexdigest(), "bytes": size}
        return (
            PREFIX
            + self.reference_cipher.encrypt(
                json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
            ).decode()
        )

    def _tombstone(self, key):
        tombstone = "tombstones/v1/" + key.rsplit("/", 1)[1]
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=tombstone)
        except ClientError as error:
            if error.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                return False
            raise
        body = response["Body"]
        try:
            data = body.read(4097)
            value = json.loads(self.reference_cipher.decrypt(data))
            if value != {"key": key, "purged": True}:
                raise InvalidObject("Invalid purge tombstone")
            return True
        finally:
            body.close()

    def write(self, source, context):
        with tempfile.TemporaryFile() as encrypted:
            encrypt(source, encrypted, self.ring, context)
            return self._upload(encrypted)

    @contextmanager
    def _verified_ciphertext(self, reference):
        value = self.descriptor(reference)
        if self._tombstone(value["key"]):
            raise InvalidObject("Object irreversibly purged")
        response = self.client.get_object(Bucket=self.bucket, Key=value["key"])
        body = response["Body"]
        try:
            with tempfile.TemporaryFile() as stored:
                size, digest = 0, hashlib.sha256()
                while block := body.read(MAX_CHUNK):
                    size += len(block)
                    if size > value["bytes"]:
                        raise InvalidObject("Object grew")
                    digest.update(block)
                    stored.write(block)
                if size != value["bytes"] or digest.hexdigest() != value["sha256"]:
                    raise InvalidObject("Object digest mismatch")
                if self._tombstone(value["key"]):
                    raise InvalidObject("Object purged during read")
                stored.seek(0)
                yield stored
        finally:
            body.close()

    def read(self, reference, target, context):
        with self._verified_ciphertext(reference) as stored:
            return decrypt(stored, target, self.ring, context)

    def verify(self, reference, context):
        """Authenticate streaming, with physical failures preceding codec failures.

        No ciphertext/plaintext tempfile or output. Even an early codec failure
        drains the body first, preserving the read API's size/digest/purge/IO
        priority. KeyboardInterrupt/SystemExit are not intercepted or drained.
        """
        value = self.descriptor(reference)
        if self._tombstone(value["key"]):
            raise InvalidObject("Object irreversibly purged")
        response = self.client.get_object(Bucket=self.bucket, Key=value["key"])
        body = response["Body"]
        try:
            source = _HashedBodyReader(body, value)
            codec_error = None
            try:
                total = verify(source, self.ring, context)
            except Exception as error:
                codec_error = error
            source.finish()
            if self._tombstone(value["key"]):
                raise InvalidObject("Object purged during read")
            if codec_error is not None:
                raise codec_error
            return total
        finally:
            body.close()

    def rotate(self, reference, context, new_ring):
        """Create a new immutable object; caller commits new ref before purging old."""
        with self._verified_ciphertext(reference) as stored, tempfile.TemporaryFile() as new:
            rewrap(stored, new, self.ring, new_ring, context)
            return self._upload(new)

    def purge(self, reference):
        self.validate_bucket()
        value = self.descriptor(reference)
        tombstone = "tombstones/v1/" + value["key"].rsplit("/", 1)[1]
        if not self._tombstone(value["key"]):
            body = self.reference_cipher.encrypt(
                json.dumps({"key": value["key"], "purged": True}, sort_keys=True).encode()
            )
            try:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=tombstone,
                    Body=body,
                    IfNoneMatch="*",
                    ContentType="application/octet-stream",
                )
            except ClientError as error:
                if error.response["ResponseMetadata"][
                    "HTTPStatusCode"
                ] != 412 or not self._tombstone(value["key"]):
                    raise
        self.delete_unreferenced(value["key"])

    def delete_unreferenced(self, key):
        """Delete unversioned bytes only after a fresh administrative state check."""
        if not KEY.fullmatch(key):
            raise InvalidObject("Invalid object key")
        self.validate_bucket()
        self.client.delete_object(Bucket=self.bucket, Key=key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as error:
            if error.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                return
            raise
        raise InvalidObject("Object deletion did not remove bytes")

    def validate_bucket(self):
        """Fail closed if deletion would retain old versions or Object Lock bytes."""
        versioning = self.client.get_bucket_versioning(Bucket=self.bucket)
        if versioning.get("Status"):
            raise InvalidObject("Versioned bucket incompatible with physical purge")
        try:
            lock = self.client.get_object_lock_configuration(Bucket=self.bucket)
        except ClientError as error:
            if error.response["Error"]["Code"] not in {
                "ObjectLockConfigurationNotFoundError",
                "NoSuchObjectLockConfiguration",
                "NotImplemented",
                "NotImplementedException",
            }:
                raise
        else:
            if lock.get("ObjectLockConfiguration", {}).get("ObjectLockEnabled") == "Enabled":
                raise InvalidObject("Object Lock incompatible with physical purge")
