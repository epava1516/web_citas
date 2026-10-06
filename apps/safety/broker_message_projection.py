"""Shared validation of scoped queued/reserved Kombu messages."""

import base64
import json
import math
import re
from datetime import datetime
from uuid import UUID

from django.views.decorators.debug import sensitive_variables

from .rights_exports import canonical

HEADER_FIELDS = frozenset(
    "lang task id shadow eta expires group group_index retries timelimit root_id parent_id argsrepr kwargsrepr origin ignore_result replaced_task_nesting stamped_headers stamps compression".split()
)
PROPERTY_FIELDS = frozenset(
    "correlation_id reply_to delivery_mode delivery_info priority body_encoding delivery_tag".split()
)


@sensitive_variables()
def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON keys")
        value[key] = item
    return value


@sensitive_variables()
def load_json(raw):
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > 64:
                raise ValueError("JSON nesting limit")
        elif char in "]}":
            depth -= 1
    try:
        return json.loads(text, object_pairs_hook=unique_object)
    except RecursionError:
        raise ValueError("JSON nesting limit") from None


@sensitive_variables()
def validate_envelope(message, args, kwargs, links, *, queue=None):
    if not isinstance(message, dict) or set(message) - {
        "body",
        "content-type",
        "content-encoding",
        "headers",
        "properties",
    }:
        raise ValueError("Envelope fields")
    headers, properties = message["headers"], message["properties"]
    if (
        not isinstance(headers, dict)
        or set(headers) - HEADER_FIELDS
        or not isinstance(properties, dict)
        or set(properties) - PROPERTY_FIELDS
    ):
        raise ValueError("Unexamined envelope fields")
    if set(links) - {"callbacks", "errbacks", "chain", "chord"}:
        raise ValueError("Unknown links")
    if "argsrepr" in headers and headers["argsrepr"] not in {repr(args), repr(tuple(args))}:
        raise ValueError("Unexamined argument representation")
    if "kwargsrepr" in headers and headers["kwargsrepr"] != repr(kwargs):
        raise ValueError("Unexamined keyword representation")
    if headers.get("stamped_headers") not in (None, []) or headers.get("stamps") not in (None, {}):
        raise ValueError("Unexamined stamped fields")
    if headers.get("shadow") is not None:
        raise ValueError("Unexamined task alias")
    for field in ["retries", "group_index", "replaced_task_nesting"]:
        value = headers.get(field)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError("Metadata integer type")
    if "ignore_result" in headers and type(headers["ignore_result"]) is not bool:
        raise ValueError("Result flag type")
    if "lang" in headers and headers["lang"] != "py":
        raise ValueError("Task language")
    for field in ["eta", "expires"]:
        value = headers.get(field)
        if value is not None and (
            not isinstance(value, str)
            or len(value) > 64
            or datetime.fromisoformat(value).tzinfo is None
        ):
            raise ValueError("Metadata time type")
    for field in ["id", "root_id", "parent_id", "group"]:
        value = headers.get(field)
        if value is not None and (
            not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value)
        ):
            raise ValueError("Metadata identifier type")
    origin = headers.get("origin")
    if origin is not None and (
        not isinstance(origin, str) or not re.fullmatch(r"gen[0-9]+@[A-Za-z0-9_.-]{1,253}", origin)
    ):
        raise ValueError("Task origin type")
    limits = headers.get("timelimit")
    if limits is not None and (
        not isinstance(limits, (list, tuple))
        or len(limits) != 2
        or any(
            v is not None
            and (type(v) not in (int, float) or not 0 <= v <= 3600 or not math.isfinite(v))
            for v in limits
        )
    ):
        raise ValueError("Task time limits")
    for field in ["correlation_id", "reply_to", "delivery_tag"]:
        value = properties.get(field)
        if value not in (None, "") and (
            not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value)
        ):
            raise ValueError("Transport identifier type")
    if "delivery_mode" in properties and (
        type(properties["delivery_mode"]) is not int or properties["delivery_mode"] not in (1, 2)
    ):
        raise ValueError("Delivery mode")
    if "priority" in properties and (
        type(properties["priority"]) is not int or not 0 <= properties["priority"] <= 9
    ):
        raise ValueError("Delivery priority")
    delivery = properties.get("delivery_info", {})
    if not isinstance(delivery, dict) or set(delivery) - {"exchange", "routing_key", "redelivered"}:
        raise ValueError("Unexamined routing fields")
    for field in ["exchange", "routing_key"]:
        value = delivery.get(field)
        if value is not None and (
            not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{0,256}", value)
        ):
            raise ValueError("Routing identifier type")
    if "redelivered" in delivery and type(delivery["redelivered"]) is not bool:
        raise ValueError("Redelivery flag")
    if queue is not None and "routing_key" in delivery and delivery["routing_key"] != queue:
        raise ValueError("Routing outside configured queue")


@sensitive_variables()
def project_message(raw, blob_ids, state, periodic, *, queue=None):
    from .rights import fingerprint

    if len(raw) > 256 * 1024:
        raise ValueError("Message limit")
    message = load_json(raw)
    if state == "reserved":
        if not isinstance(message, list) or len(message) != 3:
            raise ValueError("Reserved format")
        if any(
            not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{0,256}", v)
            for v in message[1:]
        ):
            raise ValueError("Reserved routing type")
        if queue is not None and message[2] != queue:
            raise ValueError("Reserved routing outside queue")
        message = message[0]
    if not isinstance(message, dict):
        raise ValueError("Message envelope type")
    if (
        message.get("content-type") != "application/json"
        or message.get("content-encoding") != "utf-8"
        or message.get("headers", {}).get("compression")
        or message.get("properties", {}).get("body_encoding") != "base64"
    ):
        raise ValueError("Encoding")
    args, kwargs, links = load_json(base64.b64decode(message["body"], validate=True))
    if not isinstance(args, list) or not isinstance(kwargs, dict):
        raise ValueError("Arguments")
    if not isinstance(links, dict) or any(links.values()):
        raise ValueError("Links")
    validate_envelope(message, args, kwargs, links, queue=queue)
    headers = message["headers"]
    task = headers["task"]
    if task in periodic and not args and not kwargs:
        return None
    if task != "apps.mediafiles.tasks.process_blob" or len(args) != 1 or kwargs:
        raise ValueError("Task")
    if not isinstance(args[0], str):
        raise ValueError("Blob argument type")
    blob_id = str(UUID(args[0]))
    if blob_id not in blob_ids:
        return None
    retries = headers.get("retries", 0)
    if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
        raise ValueError("Retries")
    return (
        {
            "photo_reference": fingerprint(canonical({"blob": blob_id})),
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
