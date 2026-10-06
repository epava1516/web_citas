"""Minimal historical result evidence; payloads still require separate review."""

import json
from datetime import datetime

from django.views.decorators.debug import sensitive_variables

from .rights import fingerprint

PERIODIC_COUNTER_TASKS = frozenset(
    {
        "apps.safety.tasks.purge_expired_portability_assessments",
        "apps.safety.tasks.purge_expired_portability_selections",
        "apps.safety.tasks.purge_expired_portability_coverage",
        "apps.safety.tasks.purge_expired_portability_response_drafts",
        "apps.safety.tasks.purge_expired_access_response_drafts",
    }
)


def task_reference(value):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or not value.isascii()
        or any(ord(c) < 33 for c in value)
    ):
        raise ValueError("Task identity")
    return fingerprint(value)


@sensitive_variables()
def project_result(raw, key_id, links):
    if raw is None or len(raw) > 256 * 1024:
        raise ValueError("Result limit")
    body = json.loads(raw)
    if not isinstance(body, dict) or not {"task_id", "status", "result"}.issubset(body):
        raise ValueError("Result envelope")
    if set(body) - {"task_id", "status", "result", "traceback", "children", "date_done"}:
        raise ValueError("Unknown result fields")
    reference = task_reference(body["task_id"])
    if reference != task_reference(key_id):
        raise ValueError("Result identity")
    state = body["status"]
    if state not in {"PENDING", "STARTED", "RETRY", "FAILURE", "SUCCESS", "REVOKED"}:
        raise ValueError("Result state")
    if reference not in links:
        raise ValueError("Unassociated result")
    photo = links[reference]
    if isinstance(photo, dict):
        if (
            set(photo) != {"kind", "task"}
            or photo["kind"] != "periodic_counter"
            or photo["task"] not in PERIODIC_COUNTER_TASKS
        ):
            raise ValueError("Periodic task schema")
        value = body["result"]
        if (
            state != "SUCCESS"
            or type(value) is not int
            or not 0 <= value <= 200
            or body.get("traceback") is not None
            or body.get("children") not in (None, [])
        ):
            raise ValueError("Periodic counter schema")
        completed = body.get("date_done")
        if completed is not None:
            if (
                not isinstance(completed, str)
                or len(completed) > 64
                or datetime.fromisoformat(completed).tzinfo is None
            ):
                raise ValueError("Periodic completion time")
        return None
    if photo is None:
        return None
    return {
        "photo_reference": photo,
        "state": state,
        "historical": True,
        "payload_review_required": True,
        "original_time_known": False,
    }
