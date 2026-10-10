"""Dual-reader binary export storage; original Fernet rows remain readable."""

import io

from botocore.exceptions import ClientError
from cryptography.fernet import InvalidToken
from django.conf import settings

from .crypto import cipher
from .object_storage.codec import InvalidObject
from .object_storage.factory import repository
from .object_storage.repository import PREFIX


def context(export_id, kind, identifier):
    if kind not in {"image", "part"}:
        raise ValueError("Unsupported export object kind")
    return f"rights-export/v1/{export_id}/{kind}/{identifier}".encode("ascii")


def seal_binary(content, export_id, kind, identifier):
    if not settings.RIGHTS_OBJECT_STORAGE_ENABLED:
        return cipher().encrypt(content).decode()
    return repository().write(io.BytesIO(content), context(export_id, kind, identifier))


def unseal_binary(value, export_id, kind, identifier):
    if not value.startswith(PREFIX):
        return cipher().decrypt(value.encode())
    output = io.BytesIO()
    try:
        repository().read(value, output, context(export_id, kind, identifier))
    except (InvalidObject, ClientError) as error:
        raise InvalidToken from error
    return output.getvalue()


def image_bytes(row):
    return unseal_binary(row.encrypted_content, row.export_id, "image", row.photo_id)


def part_bytes(row):
    return unseal_binary(row.encrypted_content, row.export_id, "part", row.position)


def purge_export_objects(exports):
    """Physical delete precedes SQL ref clearing; tombstones prevent restore replay."""
    from .models import RightsExportImage, RightsExportPart
    from .rights_object_delivery import purge_export_deliveries

    purge_export_deliveries(exports)
    repo = None
    for model in (RightsExportImage, RightsExportPart):
        refs = model.objects.filter(export__in=exports, encrypted_content__startswith=PREFIX)
        for value in refs.values_list("encrypted_content", flat=True).iterator(chunk_size=100):
            if repo is None:
                repo = repository()
            repo.purge(value)


def _verify_object(reference, owner_context):
    """Worker: physical authentication only; no ORM or authority decisions."""
    class Discard:
        def write(self, content):
            return len(content)

    # The dispatcher owns a separate transport scope per worker; crypto is fresh
    # on each factory invocation here, including every reference/context read.
    # Native decrypt releases plaintext to the sink only AFTER final AEAD/EOF.
    try:
        repository().read(reference, Discard(), owner_context)
    except (InvalidObject, ClientError) as error:
        raise InvalidToken from error


def _verify_objects_in_order(objects):
    """At most two physical jobs; expose failures in original iteration order.

    A later object's read may start speculatively, but cannot mask the earlier
    failure. Executor shutdown waits for every started job before returning.
    Metadata iteration and its exceptions remain on the caller's thread.
    """
    from collections import deque
    from concurrent.futures import Future, ThreadPoolExecutor
    from queue import Queue

    from .object_storage.read_clients import read_clients

    def worker(queue):
        # Scope belongs to this worker and this invocation, with a real finally
        # on thread exit. No initializer-only state or cross-thread borrowing.
        with read_clients():
            while True:
                item = queue.get()
                if item is None:
                    return
                reference, owner_context, result = item
                try:
                    _verify_object(reference, owner_context)
                except BaseException as error:
                    result.set_exception(error)
                else:
                    result.set_result(None)

    pending = deque()
    exhausted = False
    iterator = iter(objects)
    queues = [Queue(maxsize=1), Queue(maxsize=1)]
    dispatched = 0
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="rights-object-verify") as executor:
        workers = []
        try:
            for queue in queues:
                workers.append(executor.submit(worker, queue))
            while pending or not exhausted:
                while len(pending) < 2 and not exhausted:
                    try:
                        reference, owner_context = next(iterator)
                    except StopIteration:
                        exhausted = True
                    except Exception as error:
                        # Preserve earlier physical failure over later metadata.
                        failed = Future()
                        failed.set_exception(error)
                        pending.append(failed)
                        exhausted = True
                    else:
                        result = Future()
                        queues[dispatched % 2].put((reference, owner_context, result))
                        dispatched += 1
                        pending.append(result)
                if pending:
                    pending.popleft().result()
        finally:
            # No new object jobs after an observed failure. Sentinels follow
            # already queued jobs; wait for workers AND their close/reset finally.
            for queue in queues[:len(workers)]:
                queue.put(None)
            try:
                for completed in workers:
                    completed.result()
            finally:
                try:
                    close = getattr(iterator, "close", None)
                    if close is not None:
                        close()
                except Exception:
                    # Cursor teardown must not replace ordered domain failure.
                    pass


def verify_export_objects(export):
    """Mandatory physical guard before a DB validation seal may be trusted.

    Signed refs and SQL equality do not prove externally retained bytes unchanged.
    Each object verifies its purge tombstone, digest, complete AEAD and owner context.
    """
    from django.core.exceptions import ValidationError

    from .models import RightsExportImage, RightsExportPart

    def objects():
        # Materialize immutable inputs here: workers never touch ORM objects or
        # Django connections. Preserve original full model queries/post_init.
        for model, kind, identifier in ((RightsExportImage, "image", "photo_id"),
                                        (RightsExportPart, "part", "position")):
            rows = model.objects.filter(
                export=export, encrypted_content__startswith=PREFIX
            ).iterator(chunk_size=1)
            try:
                for row in rows:
                    yield row.encrypted_content, context(row.export_id, kind, getattr(row, identifier))
            finally:
                try:
                    rows.close()
                except Exception:
                    pass

    try:
        _verify_objects_in_order(objects())
    except (InvalidToken, OSError) as error:
        raise ValidationError("External export object unavailable or changed") from error


from celery import shared_task  # noqa: E402


@shared_task
def purge_orphan_export_objects():
    """Remove aborted-generation objects after one day; tombstones remain durable.

    Export generation is bounded well below the grace interval. Freeze writes in
    recovery; retained tombstones are a separate recovery authority, not a backup.
    """
    from datetime import timedelta

    from django.utils import timezone

    from .models import RightsExportImage, RightsExportPart

    if not settings.RIGHTS_OBJECT_STORAGE_ENABLED or settings.RECOVERY_MODE:
        return 0
    repo, live = repository(), set()
    for model in (RightsExportImage, RightsExportPart):
        for reference in (
            model.objects.filter(encrypted_content__startswith=PREFIX)
            .values_list("encrypted_content", flat=True)
            .iterator(chunk_size=100)
        ):
            live.add(repo.descriptor(reference)["key"])
    cutoff, deleted = timezone.now() - timedelta(days=1), 0
    for page in repo.client.get_paginator("list_objects_v2").paginate(
        Bucket=repo.bucket, Prefix="encrypted/v1/"
    ):
        for item in page.get("Contents", []):
            if item["Key"] not in live and item["LastModified"] < cutoff:
                # No reference ever committed; unlike a released artifact, no replay authority.
                repo.delete_unreferenced(item["Key"])
                deleted += 1
    return deleted
