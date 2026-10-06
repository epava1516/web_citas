"""Private per-subject association of a retained AOF prefix, never replayed."""

import json
from io import BytesIO

from django.views.decorators.debug import sensitive_variables

from .broker_message_projection import periodic_tasks, project_message
from .redis_retained_history import inspect_aof
from .rights import fingerprint
from .rights_exports import canonical


@sensitive_variables()
def scoped_history(raw, blob_ids, *, prefix, queue, origin_digest):
    queues = {
        (prefix + queue + suffix).encode() for suffix in ["", "\x06\x163", "\x06\x166", "\x06\x169"]
    }
    reserved = (prefix + "unacked").encode()
    database = 0
    records = []
    blocked = []
    periodic = periodic_tasks()
    task_links = {}
    conflicting_tasks = set()

    from .redis_result_projection import PERIODIC_COUNTER_TASKS, project_result, task_reference

    def visit(offset, command, arguments):
        nonlocal database
        if command == "SELECT":
            try:
                database = int(arguments[1]) if len(arguments) == 2 else None
            except (TypeError, ValueError):
                database = None
                blocked.append("unknown_database")
            return
        if database != 0 or len(arguments) < 2:
            return
        key = arguments[1]
        if key in queues and command in {"LPUSH", "RPUSH"}:
            messages = list(enumerate(arguments[2:]))
            state = "queued"
        elif key == reserved and command in {"HSET", "HMSET"}:
            if len(arguments) < 4 or len(arguments) % 2:
                blocked.append("invalid_reserved_command")
                return
            messages = list(enumerate(arguments[3::2]))
            state = "reserved"
        else:
            return
        for position, message in messages:
            if len(records) >= 1000:
                blocked.append("history_record_limit")
                return
            try:
                if message is None:
                    raise ValueError("Unmaterialized message")
                projected = project_message(message, blob_ids, state, periodic)
                envelope = json.loads(message)
                if state == "reserved":
                    envelope = envelope[0]
                task_name = envelope["headers"]["task"]
                if (
                    task_name == "apps.mediafiles.tasks.process_blob"
                    or task_name in PERIODIC_COUNTER_TASKS
                ):
                    task = task_reference(envelope["headers"]["id"])
                    photo = (
                        {"kind": "periodic_counter", "task": task_name}
                        if task_name in PERIODIC_COUNTER_TASKS
                        else projected[0]["photo_reference"]
                        if projected
                        else None
                    )
                    if task in task_links and task_links[task] != photo:
                        blocked.append("conflicting_historical_task_identity")
                        conflicting_tasks.add(task)
                        task_links[task] = None
                    elif task in conflicting_tasks:
                        task_links[task] = None
                    elif len(task_links) >= 1000:
                        blocked.append("history_task_link_limit")
                    else:
                        task_links[task] = photo
                if projected is None:
                    continue
                data, content = projected
            except (KeyError, TypeError, ValueError, AttributeError):
                blocked.append("unsupported_historical_message")
                continue
            data = data | {"historical": True, "original_time_known": False}
            records.append(
                {
                    "reference": fingerprint(
                        canonical({"origin": origin_digest, "offset": offset, "position": position})
                    ),
                    "data": data,
                    "technical_fields_excluded": [
                        "broker_arguments",
                        "task_id",
                        "routing",
                        "original_command_time",
                    ],
                }
            )

    inspection = inspect_aof(BytesIO(raw), on_command=visit)
    result_records = []
    result_pending = []
    technical_results = []
    database = 0

    def results_visit(offset, command, arguments):
        nonlocal database
        if command == "SELECT":
            try:
                database = int(arguments[1]) if len(arguments) == 2 else None
            except (TypeError, ValueError):
                database = None
            return
        if database != 0 or len(arguments) < 2:
            return
        key = arguments[1]
        marker = b"celery-task-meta-"
        if key is None or marker not in key or command not in {"SET", "SETEX", "PSETEX"}:
            return
        namespace, key_id = key.rsplit(marker, 1)
        if namespace not in {b"", prefix.encode()}:
            blocked.append("unsupported_result_namespace")
            return
        try:
            if len(result_records) >= 1000:
                raise ValueError("Result count limit")
            position = 2 if command == "SET" else 3
            data = project_result(arguments[position], key_id.decode("ascii"), task_links)
            if data is None:
                link = task_links.get(task_reference(key_id.decode("ascii")))
                if isinstance(link, dict):
                    if len(technical_results) >= 1000:
                        raise ValueError("Technical result count limit")
                    technical_results.append(
                        {
                            "reference": fingerprint(
                                canonical({"origin": origin_digest, "result_offset": offset})
                            ),
                            "reason": "known_periodic_counter_without_subject_arguments",
                        }
                    )
                return
        except (IndexError, KeyError, TypeError, ValueError, AttributeError):
            blocked.append("unsupported_or_unassociated_historical_result")
            return
        result_pending.append("historical_result_payload_review")
        result_records.append(
            {
                "reference": fingerprint(
                    canonical({"origin": origin_digest, "result_offset": offset})
                ),
                "data": data,
                "technical_fields_excluded": [
                    "task_id",
                    "result_payload",
                    "traceback",
                    "children",
                    "date_done",
                ],
            }
        )

    result_inspection = inspect_aof(BytesIO(raw), on_command=results_visit)
    blocked.extend(result_inspection["pending"])
    return {
        "result_records": result_records,
        "technical_result_evidence": technical_results,
        "pending": sorted(set(result_pending)),
        "records": records,
        "inspection": inspection,
        "blocked": sorted(set(blocked + inspection["pending"])),
        "origin_digest": origin_digest,
        "partial": True,
    }


@sensitive_variables()
def history_records(blob_ids, cutoff):
    import base64
    import hashlib
    import os
    import stat
    from datetime import datetime
    from urllib.parse import urlparse

    from django.conf import settings
    from django.core.exceptions import ValidationError

    from .redis_retained_history import MAX_BYTES
    from .rights_access_response_draft import checked_body

    path = getattr(settings, "ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE", "")
    if not path:
        return {"configured": False, "records": [], "blocked": [], "pending": []}
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) & 0o077
                or metadata.st_uid != os.geteuid()
            ):
                raise ValueError
            encrypted = stream.read(128 * 1024 * 1024 + 1)
        if len(encrypted) > 128 * 1024 * 1024:
            raise ValueError
        body = checked_body(encrypted.decode())
        if (
            set(body) != {"schema", "project", "captured_at", "sha256", "content_base64", "partial"}
            or body["schema"] != "local-redis-aof-origin-v1"
            or body["project"] != "web-modelos"
            or body["partial"] is not True
        ):
            raise ValueError
        captured = datetime.fromisoformat(body["captured_at"])
        if captured.tzinfo is None or captured > cutoff:
            raise ValueError
        raw = base64.b64decode(body["content_base64"], validate=True)
        if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != body["sha256"]:
            raise ValueError
        options = settings.CELERY_BROKER_TRANSPORT_OPTIONS
        if (
            urlparse(settings.CELERY_BROKER_URL).path not in {"", "/0"}
            or set(options) != {"global_keyprefix"}
            or not isinstance(options.get("global_keyprefix"), str)
            or not options["global_keyprefix"]
            or not isinstance(settings.CELERY_TASK_DEFAULT_QUEUE, str)
            or not settings.CELERY_TASK_DEFAULT_QUEUE
            or getattr(settings, "CELERY_TASK_ROUTES", None)
            or getattr(settings, "CELERY_TASK_QUEUES", None)
        ):
            raise ValueError
        result = scoped_history(
            raw,
            blob_ids,
            prefix=options["global_keyprefix"],
            queue=settings.CELERY_TASK_DEFAULT_QUEUE,
            origin_digest=fingerprint(canonical(body)),
        )
        return result | {
            "configured": True,
            "captured_at": captured.isoformat(),
            "pending": sorted(set(result["pending"] + ["historical_redis_coverage"])),
        }
    except (OSError, KeyError, TypeError, ValueError, ValidationError):
        raise ValidationError(
            "Retained Redis history origin unavailable, out of cutoff or altered"
        ) from None
