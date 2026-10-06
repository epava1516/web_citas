"""Shared validation of scoped queued/reserved Kombu messages."""

import base64
import json

from django.views.decorators.debug import sensitive_variables

from .rights_exports import canonical


@sensitive_variables()
def project_message(raw, blob_ids, state, periodic):
    from .rights import fingerprint

    if len(raw) > 256 * 1024:
        raise ValueError("Message limit")
    message = json.loads(raw)
    if state == "reserved":
        if not isinstance(message, list) or len(message) != 3:
            raise ValueError("Reserved format")
        message = message[0]
    if (
        message.get("content-type") != "application/json"
        or message.get("content-encoding") != "utf-8"
        or message.get("headers", {}).get("compression")
        or message.get("properties", {}).get("body_encoding") != "base64"
    ):
        raise ValueError("Encoding")
    args, kwargs, links = json.loads(base64.b64decode(message["body"], validate=True))
    if not isinstance(args, list) or not isinstance(kwargs, dict):
        raise ValueError("Arguments")
    if not isinstance(links, dict) or any(links.values()):
        raise ValueError("Links")
    headers = message["headers"]
    task = headers["task"]
    if task in periodic and not args and not kwargs:
        return None
    if task != "apps.mediafiles.tasks.process_blob" or len(args) != 1 or kwargs:
        raise ValueError("Task")
    if str(args[0]) not in blob_ids:
        return None
    retries = headers.get("retries", 0)
    if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
        raise ValueError("Retries")
    return (
        {
            "photo_reference": fingerprint(canonical({"blob": str(args[0])})),
            "state": state,
            "retries": retries,
        },
        fingerprint(canonical(message)),
    )


def periodic_tasks():
    periodic = {
        "apps.listings.tasks.expire_listings",
        "apps.mediafiles.tasks.recover_media_jobs",
        "apps.mediafiles.tasks.erase_media_files",
        "apps.mediafiles.tasks.cleanup_prepared_media",
    }
    from . import tasks

    periodic.update(
        "apps.safety.tasks." + name
        for name in dir(tasks)
        if callable(getattr(tasks, name)) and hasattr(getattr(tasks, name), "delay")
    )
    return periodic
