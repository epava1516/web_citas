"""One reviewed access package: actual indexed records, copy and scoped decisions.

This is an internal preparation snapshot, not an assertion of legal sufficiency.
Unknown encrypted formats remain blocked, never silently declared excluded.
"""

import hashlib
import json
import os
import re
import stat
from datetime import datetime
from email.message import Message
from email.utils import getaddresses

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_variables
from redis import Redis, RedisError

from .models import RightsAccessScopeInventory
from .rights import fingerprint
from .rights_access_response_draft import checked_body
from .rights_access_scope_inventory import normalized, source
from .rights_exports import canonical


def scoped_origin_path(configured, *, kind, case=None, inventory=None):
    """A private directory retains separate immutable origins for concurrent cases."""
    if not configured:
        return configured
    try:
        metadata = os.lstat(configured)
        if not stat.S_ISDIR(metadata.st_mode):
            return configured
        if (
            stat.S_IMODE(metadata.st_mode) & 0o077
            or metadata.st_uid != os.geteuid()
            or case is None
            or inventory is None
        ):
            raise ValueError
        from scripts.collect_access_resource_logs import scoped_origin_name

        return os.path.join(configured, scoped_origin_name(kind, case.pk, inventory.pk))
    except (OSError, TypeError, ValueError):
        raise ValidationError("Private scoped resource origin required") from None


SECRET_MARKERS = ("password", "secret", "token", "digest", "receipt", "signature", "path")
JSON_FIELDS = frozenset(
    {
        "encrypted_payload",
        "encrypted_reason",
        "encrypted_response",
        "encrypted_result",
        "encrypted_manifest",
        "encrypted_decisions",
        "encrypted_inventory",
        "encrypted_body",
        "encrypted_coverage",
    }
)


def secret_name(name):
    return (
        name == "key"
        or name.endswith("_key")
        or any(marker in name.lower() for marker in SECRET_MARKERS)
    )


def safe_json(value):
    if isinstance(value, dict):
        return {
            key: safe_json(item)
            for key, item in value.items()
            if isinstance(key, str)
            and not secret_name(key)
            and key not in {"review_material", "evidence"}
        }
    if isinstance(value, list):
        return [safe_json(item) for item in value]
    return normalized(value)


@sensitive_variables()
def session_records(owner, cutoff):
    """Account for retained DB sessions, including expired rows, without capabilities.

    ``authenticated`` identifies a stored account association, not a currently
    valid credential. Expired rows remain personal data until actually removed.
    """
    result = {"copy": [], "evidence": [], "blocked": []}
    if settings.SESSION_ENGINE != "django.contrib.sessions.backends.db":
        result["blocked"].append({"resource": "sessions", "reason": "unsupported_session_store"})
        return result
    if not owner:
        return result
    security_fields = {
        "_auth_user_id",
        "_auth_user_backend",
        "_auth_user_hash",
        "account_version",
        "mfa_version",
        "_session_expiry",
    }
    supported = security_fields | {"django_language"}
    for row in Session.objects.order_by("pk").iterator(chunk_size=500):
        decoded = row.get_decoded()
        if str(decoded.get("_auth_user_id")) != str(owner):
            continue
        reference = fingerprint(canonical({"resource": "session", "key": row.pk}))
        unknown = sorted(set(decoded) - supported)
        if unknown:
            result["blocked"].append(
                {"resource": "sessions", "reference": reference, "fields": unknown}
            )
        language = decoded.get("django_language")
        if language is not None and language not in {"es", "en"}:
            result["blocked"].append(
                {"resource": "sessions", "reference": reference, "fields": ["django_language"]}
            )
        copy = {
            "expires_at": row.expire_date.isoformat(),
            "authenticated": True,
            "expired_at_cutoff": row.expire_date <= cutoff,
        }
        if language in {"es", "en"}:
            copy["language"] = language
        result["copy"].append(copy)
        result["evidence"].append(
            {
                "reference": reference,
                "content": fingerprint(canonical(normalized(decoded))),
                "expires_at": row.expire_date.isoformat(),
                "security_fields_excluded": sorted(set(decoded) & security_fields),
            }
        )
    return result


@sensitive_variables()
def account_mail_projection(message, *, owner, email):
    """Release the known account template only after checking its token ownership."""
    from apps.core.models import AccountToken

    prefix = "Enlace de un solo uso / Single-use link:\n"
    if (
        owner is None
        or message.subject != "Confirmación de cuenta / Account confirmation"
        or message.from_email != settings.DEFAULT_FROM_EMAIL
        or message.to != [email]
        or message.cc
        or message.bcc
        or message.reply_to
        or message.extra_headers
        or message.attachments
        or getattr(message, "alternatives", [])
        or not isinstance(message.body, str)
        or not message.body.startswith(prefix)
    ):
        return None
    route = re.fullmatch(
        re.escape(settings.PUBLIC_ORIGIN)
        + r"/(?:es|en)/account/token/([0-9a-fA-F-]{36})/([A-Za-z0-9_-]+)/",
        message.body[len(prefix) :],
    )
    if route is None:
        return None
    try:
        token = AccountToken.objects.filter(pk=route[1], user_id=owner).first()
    except (ValidationError, ValueError):
        return None
    if (
        token is None
        or token.purpose not in {"verify", "reset"}
        or not constant_time_compare(token.digest, hashlib.sha256(route[2].encode()).hexdigest())
    ):
        return None
    return {
        "subject": message.subject,
        "sender": message.from_email,
        "recipient": email,
        "body": prefix + "[redacted]",
        "purpose": token.purpose,
        "created_at": token.created_at.isoformat(),
    }


@sensitive_variables()
def mail_records(email, *, owner=None):
    """Account for retained mail; typed copies omit authentication capabilities."""
    result = {"records": [], "pending": [], "projected": []}
    if settings.EMAIL_BACKEND != "django.core.mail.backends.locmem.EmailBackend":
        result["pending"] = ["mail_backend_content_accounting"]
        return result
    from django.core import mail

    if not email:
        result["pending"] = ["mail_subject_association"]
        return result
    for position, message in enumerate(getattr(mail, "outbox", [])):
        recipients = message.recipients()
        if not any(
            address.casefold() == email.casefold() for _, address in getaddresses(recipients)
        ):
            continue
        attachments = []
        for attachment in message.attachments:
            if isinstance(attachment, Message):
                attachments.append({"mime_content": fingerprint(attachment.as_bytes().hex())})
            elif isinstance(attachment, (tuple, list)):
                attachments.append(normalized(attachment))
            else:
                raise ValidationError("Retained mail attachment requires a typed adapter")
        original = {
            "subject": message.subject,
            "body": message.body,
            "from_email": message.from_email,
            "to": message.to,
            "cc": message.cc,
            "bcc": message.bcc,
            "reply_to": message.reply_to,
            "headers": message.extra_headers,
            "attachments": attachments,
            "alternatives": normalized(getattr(message, "alternatives", [])),
        }
        result["records"].append(
            {
                "reference": fingerprint(canonical({"resource": "mail", "position": position})),
                "content": fingerprint(canonical(original)),
                "recipient_count": len(recipients),
                "attachment_count": len(message.attachments),
                "shared_recipients": len(recipients) != 1,
            }
        )
        projection = account_mail_projection(message, owner=owner, email=email)
        if projection is not None:
            result["projected"].append(
                {
                    "reference": result["records"][-1]["reference"],
                    "data": projection,
                    "technical_fields_excluded": ["authentication_link"],
                }
            )
    if len(result["records"]) != len(result["projected"]):
        result["pending"] = ["mail_body_headers_and_attachments_projection"]
    return result


@sensitive_variables()
def broker_records(blob_ids):
    """Read queued/reserved Redis messages atomically; never acknowledge or consume."""
    result = {"copy": [], "evidence": [], "blocked": []}
    options = settings.CELERY_BROKER_TRANSPORT_OPTIONS
    prefix = options.get("global_keyprefix")
    queue = settings.CELERY_TASK_DEFAULT_QUEUE
    if (
        not isinstance(prefix, str)
        or not prefix
        or getattr(settings, "CELERY_TASK_ROUTES", None)
        or getattr(settings, "CELERY_TASK_QUEUES", None)
        or options.get("priority_steps", [0, 3, 6, 9]) != [0, 3, 6, 9]
        or options.get("sep", "\x06\x16") != "\x06\x16"
        or options.get("unacked_key", "unacked") != "unacked"
    ):
        result["blocked"].append({"resource": "queues", "reason": "unsupported_transport_scope"})
        return result
    keys = [prefix + queue] + [prefix + queue + "\x06\x16" + str(p) for p in [3, 6, 9]]
    try:
        with Redis.from_url(
            settings.CELERY_BROKER_URL, socket_timeout=2, socket_connect_timeout=2
        ) as client:
            captured = client.eval_ro(
                """
                local values = {}
                local total = 0
                local function within_byte_limit(messages)
                    for _, raw in ipairs(messages) do
                        if string.len(raw) > 262144 then return false end
                        total = total + string.len(raw)
                        if total > 8388608 then return false end
                    end
                    return true
                end
                for i = 1, 4 do
                    if redis.call('LLEN', KEYS[i]) > 1000 then return {0} end
                    values[i] = redis.call('LRANGE', KEYS[i], 0, 999)
                    if not within_byte_limit(values[i]) then return {2} end
                end
                if redis.call('HLEN', KEYS[5]) > 1000 then return {0} end
                values[5] = redis.call('HVALS', KEYS[5])
                if not within_byte_limit(values[5]) then return {2} end
                return {1, values}
                """,
                5,
                *keys,
                prefix + "unacked",
            )
    except (RedisError, ValueError):
        result["blocked"].append({"resource": "queues", "reason": "broker_unavailable"})
        return result
    if captured[0] != 1:
        result["blocked"].append(
            {
                "resource": "queues",
                "reason": "bounded_read_bytes" if captured[0] == 2 else "bounded_read_limit",
            }
        )
        return result
    wire = [(raw, "queued") for messages in captured[1][:4] for raw in messages]
    wire.extend((raw, "reserved") for raw in captured[1][4])
    from .broker_message_projection import periodic_tasks

    periodic = periodic_tasks()
    for raw, state in wire:
        try:
            from .broker_message_projection import project_message

            projected_message = project_message(raw, blob_ids, state, periodic, queue=queue)
            if projected_message is not None:
                data, content = projected_message
                result["copy"].append(data)
                result["evidence"].append({"state": state, "content": content})
        except (KeyError, TypeError, ValueError, AttributeError):
            result["blocked"].append({"resource": "queues", "reason": "unsupported_message"})
    result["copy"].sort(key=canonical)
    result["evidence"].sort(key=canonical)
    return result


@sensitive_variables()
def log_records(
    identifiers, cutoff, *, subjects=None, case=None, inventory=None, owner=None, email=""
):
    """Associate real captured origins privately; no automatic log disclosure."""
    path = scoped_origin_path(
        settings.ACCESS_LOG_ORIGIN_BUNDLE, kind="logs", case=case, inventory=inventory
    )
    if not path:
        return {"configured": False, "pending": ["retained_log_origins"]}
    from scripts.collect_access_resource_logs import (
        MAX_SERVICE_BYTES,
        PROJECT,
        SERVICES,
        subject_log_signature,
    )

    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) & 0o077
                or metadata.st_uid != os.geteuid()
            ):
                raise ValueError
            ciphertext = stream.read(MAX_SERVICE_BYTES * len(SERVICES) * 2 + 1)
        if len(ciphertext) > MAX_SERVICE_BYTES * len(SERVICES) * 2:
            raise ValueError
        body = checked_body(ciphertext.decode())
        historical = body.get("schema") == "local-log-retained-origins-scoped-v1"
        if historical:
            from .retained_log_origins import MAX_CIPHERTEXT_BYTES, PENDING, checked_scoped_captures

            if len(ciphertext) > MAX_CIPHERTEXT_BYTES:
                raise ValueError
            records = checked_scoped_captures(body, case, inventory, cutoff)
            captured_at = cutoff
            pending = PENDING + ["historical_log_capture_coverage"]
        else:
            captured_at = datetime.fromisoformat(body["captured_at"])
            records = body["records"]
            pending = body["pending"]
        if not historical and (
            body["schema"] != "local-access-log-origins-v1"
            or body["project"] != PROJECT
            or captured_at.tzinfo is None
            or not cutoff <= captured_at <= timezone.now()
            or body["partial"] is not True
            or body["pending"]
            != [
                "subject_association_and_disclosure_review",
                "historical_or_removed_containers",
                "host_logs_and_mail_retention",
                "cache_and_backup_content_accounting",
            ]
            or len(body["records"]) != len(SERVICES)
            or {row["service"] for row in body["records"]} != set(SERVICES)
        ):
            raise ValueError
        candidates, origins, projected, projected_mail = [], [], [], []
        subjects = subjects or {}
        identifiers = {value for value in identifiers if isinstance(value, str) and len(value) >= 8}
        for row in records:
            origin = {
                key: row[key] for key in ["service", "container", "image", "container_created_at"]
            }
            if historical:
                origin.update({key: row[key] for key in ("capture_digest", "captured_at", "ciphertext_sha256")})
            for name in ["stdout", "stderr"]:
                content = row[name]
                if (
                    not isinstance(content, str)
                    or len(content.encode()) > MAX_SERVICE_BYTES
                    or hashlib.sha256(content.encode()).hexdigest() != row[name + "_sha256"]
                ):
                    raise ValueError
                origin[name + "_digest"] = fingerprint(content)
                from .console_mail_projection import console_mail_projections

                mail_lines = console_mail_projections(content, cutoff, owner=owner, email=email)
                for position, line in enumerate(content.splitlines()):
                    pieces = line.split(" ", 1)
                    try:
                        event = json.loads(pieces[1]) if len(pieces) == 2 else None
                    except (ValueError, TypeError):
                        event = None
                    associated_subject = (
                        isinstance(event, dict)
                        and isinstance(event.get("subject_kind"), str)
                        and isinstance(event.get("subject_id"), (str, int))
                        and not isinstance(event.get("subject_id"), bool)
                        and str(event["subject_id"]) in subjects.get(event["subject_kind"], set())
                    )
                    owned = (
                        associated_subject
                        and event.get("schema") == "subject-operation-v1"
                        and isinstance(event.get("subject_id"), str)
                    )
                    if not associated_subject and not any(value in line for value in identifiers):
                        continue
                    timestamp = datetime.fromisoformat(line.split(" ", 1)[0])
                    if timestamp.tzinfo is None:
                        raise ValueError
                    if timestamp > cutoff:
                        continue
                    if historical and timestamp > datetime.fromisoformat(row["captured_at"]):
                        raise ValueError
                    reference = fingerprint(
                        canonical(
                            {
                                "container": row["container"],
                                "stream": name,
                                "position": position,
                                "line": line,
                                **({"capture_digest": row["capture_digest"]} if historical else {}),
                            }
                        )
                    )
                    # Candidate contents may contain another person's data or credentials.
                    # Expose only references until a typed projection/redaction is reviewed.
                    candidates.append(
                        {
                            "service": row["service"],
                            "stream": name,
                            "record": reference,
                            "created_at": timestamp.isoformat(),
                            "content_digest": fingerprint(line),
                        }
                    )
                    if position in mail_lines:
                        projected_mail.append(
                            {
                                "reference": reference,
                                "data": mail_lines[position],
                                "technical_fields_excluded": [
                                    "authentication_link",
                                    "mime_headers",
                                ],
                            }
                        )
                    event_at = None
                    if owned and isinstance(event.get("created_at"), str):
                        try:
                            event_at = datetime.fromisoformat(event["created_at"])
                        except ValueError:
                            pass
                    if (
                        owned
                        and event_at is not None
                        and event_at.tzinfo is not None
                        and event_at <= timestamp
                        and isinstance(event.get("signature"), str)
                        and constant_time_compare(event["signature"], subject_log_signature(event))
                        and isinstance(event.get("operation"), str)
                        and isinstance(event.get("outcome"), str)
                        and set(event)
                        == {
                            "schema",
                            "subject_kind",
                            "subject_id",
                            "operation",
                            "outcome",
                            "created_at",
                            "signature",
                        }
                        and event["operation"]
                        in {
                            "media_processing_started",
                            "media_processing_completed",
                            "media_processing_failed",
                            "profile_viewed",
                            "profile_updated",
                            "contact_verified",
                            "rights_record_read",
                            "rights_response_issued",
                        }
                        and event["outcome"] in {"succeeded", "failed", "denied", "pending"}
                    ):
                        projected.append(
                            {
                                "reference": reference,
                                "data": {
                                    "created_at": event_at.isoformat(),
                                    "operation": event["operation"],
                                    "outcome": event["outcome"],
                                },
                                "technical_fields_excluded": [
                                    "schema",
                                    "subject_kind",
                                    "subject_id",
                                    "signature",
                                ],
                            }
                        )
            origins.append(origin)
        projected_references = {item["reference"] for item in projected + projected_mail}
        return {
            "configured": True,
            "captured_at": captured_at.isoformat(),
            "origins": origins,
            "candidates": candidates,
            "projected": projected,
            "projected_mail": projected_mail,
            "unprojected_candidates": [
                row["record"] for row in candidates if row["record"] not in projected_references
            ],
            "pending": pending,
        }
    except (OSError, KeyError, TypeError, ValueError, ValidationError):
        raise ValidationError("Retained log origin unavailable, stale or altered") from None


RESOURCE_CATEGORIES = frozenset({"logs", "mail", "caches", "backups", "unlinked_records"})


@sensitive_variables()
def retained_resource_records(case, person, inventory, dependencies, required):
    """Read a privileged, scoped origin census for the existing independent review.

    This verifies artifact integrity and scope, not the truth of an operator's
    census. Each source and its actual retained records remain review material.
    Missing categories, ambiguous association and unfinished censuses stay pending.
    """
    path = scoped_origin_path(
        getattr(settings, "ACCESS_RESOURCE_ORIGIN_BUNDLE", ""),
        kind="resources",
        case=case,
        inventory=inventory,
    )
    result = {
        "configured": False,
        "groups": [],
        "origins": [],
        "pending": sorted(RESOURCE_CATEGORIES),
    }
    if not path:
        return result
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) & 0o077
                or metadata.st_uid != os.geteuid()
            ):
                raise ValueError
            ciphertext = stream.read(32 * 1024 * 1024 + 1)
        if len(ciphertext) > 32 * 1024 * 1024:
            raise ValueError
        body = checked_body(ciphertext.decode())
        captured_at = datetime.fromisoformat(body["captured_at"])
        if (
            set(body)
            != {
                "schema",
                "request",
                "inventory",
                "source",
                "cutoff",
                "captured_at",
                "dependencies",
                "categories",
            }
            or body["schema"] != "access-retained-resources-v1"
            or body["request"] != str(case.pk)
            or type(body["inventory"]) is not int
            or body["inventory"] != inventory.pk
            or body["source"] != inventory.source_digest
            or body["cutoff"] != inventory.created_at.isoformat()
            or captured_at.tzinfo is None
            or not inventory.created_at <= captured_at <= timezone.now()
            or body["dependencies"] != dependencies
            or not isinstance(body["categories"], dict)
            or set(body["categories"]) != RESOURCE_CATEGORIES
        ):
            raise ValueError
        subjects = {
            "account": str(case.account_subject_id or (person.subject_id if person else "") or ""),
            "person": str(person.pk) if person else "",
        }
        result["configured"] = True
        result["pending"] = []
        result["digest"] = fingerprint(canonical(body))
        seen = set()
        covered = {category: set() for category in required}
        for category in sorted(RESOURCE_CATEGORIES):
            census = body["categories"][category]
            if (
                not isinstance(census, dict)
                or set(census) != {"reason", "origins", "pending"}
                or not isinstance(census["reason"], str)
                or not 20 <= len(census["reason"].strip()) <= 2000
                or not isinstance(census["pending"], list)
                or any(not isinstance(item, str) or not item for item in census["pending"])
                or not isinstance(census["origins"], list)
                or not census["origins"]
            ):
                raise ValueError
            result["pending"].extend(category + ":" + item for item in census["pending"])
            for origin in census["origins"]:
                if (
                    not isinstance(origin, dict)
                    or set(origin)
                    != {"reference", "method", "evidence", "records", "records_digest"}
                    or not isinstance(origin["reference"], str)
                    or not 1 <= len(origin["reference"]) <= 200
                    or origin["reference"] in seen
                    or origin["method"]
                    not in {"structured_archive", "restored_database", "configuration_inspection"}
                    or not isinstance(origin["evidence"], str)
                    or not 20 <= len(origin["evidence"].strip()) <= 2000
                    or not isinstance(origin["records"], list)
                    or len(origin["records"]) > 10000
                    or origin["records_digest"] != fingerprint(canonical(origin["records"]))
                ):
                    raise ValueError
                seen.add(origin["reference"])
                origin_reference = fingerprint(
                    canonical({"category": category, "origin": origin["reference"]})
                )
                scoped_count = 0
                for position, row in enumerate(origin["records"]):
                    if (
                        not isinstance(row, dict)
                        or set(row)
                        != {
                            "subject_kind",
                            "subject_id",
                            "created_at",
                            "content",
                            "source_reference",
                        }
                        or row["subject_kind"] not in subjects
                        or not isinstance(row["subject_id"], str)
                        or not row["subject_id"]
                        or not isinstance(row["content"], str)
                    ):
                        raise ValueError
                    created_at = datetime.fromisoformat(row["created_at"])
                    if created_at.tzinfo is None:
                        raise ValueError
                    if (
                        row["subject_id"] != subjects[row["subject_kind"]]
                        or created_at > inventory.created_at
                    ):
                        continue
                    source_reference = row["source_reference"]
                    if source_reference is not None:
                        if (
                            not isinstance(source_reference, str)
                            or source_reference not in required.get(category, {})
                            or source_reference in covered[category]
                            or fingerprint(row["content"]) != required[category][source_reference]
                        ):
                            raise ValueError
                        covered[category].add(source_reference)
                    scoped_count += 1
                    result["groups"].append(
                        {
                            "reference": fingerprint(
                                canonical(
                                    {"origin": origin_reference, "position": position, "row": row}
                                )
                            ),
                            "data": {
                                "category": category,
                                "created_at": created_at.isoformat(),
                                "content": row["content"],
                            },
                            "technical_fields_excluded": ["subject_kind", "subject_id"],
                        }
                    )
                result["origins"].append(
                    {
                        "category": category,
                        "reference": origin_reference,
                        "method": origin["method"],
                        "evidence": origin["evidence"],
                        "records_digest": origin["records_digest"],
                        "record_count": len(origin["records"]),
                        "scoped_count": scoped_count,
                        "scope_reason": census["reason"],
                    }
                )
        for category, records in required.items():
            if covered[category] != set(records):
                result["pending"].append(category + ":unaccounted_retained_records")
        return result
    except (OSError, KeyError, TypeError, ValueError, ValidationError):
        raise ValidationError("Retained resource census unavailable, stale or altered") from None


@sensitive_variables()
def snapshot(case, person, inventory, *, cutoff, projected):
    """Caller already authorized and audited; collect original reviewable values."""
    action = inventory.action
    reason = checked_body(action.encrypted_reason)
    if (
        not isinstance(reason, dict)
        or set(reason) != {"reason"}
        or not isinstance(reason["reason"], str)
        or not 20 <= len(reason["reason"].strip()) <= 200
    ):
        raise ValidationError("Access inventory inspection evidence changed")
    digest = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": inventory.case_version,
                "responses": inventory.response_version,
                "actor": inventory.actor_id,
                "session": inventory.original_session_version,
                "mfa": inventory.original_mfa_version,
                "proof": str(inventory.proof_id),
                "reason": reason["reason"],
            }
        )
    )
    if (
        inventory.request_id != case.pk
        or inventory.case_version != case.version
        or inventory.response_version != case.response_version
        or cutoff != inventory.created_at
        or action.request_id != case.pk
        or action.actor_id != inventory.actor_id
        or action.expected_version != inventory.case_version
        or action.operation != "access_scope_read"
        or action.payload_digest != digest
    ):
        raise ValidationError("Access inventory inspection evidence changed")
    groups = {}
    blocked = []
    correspondence = []

    @sensitive_variables()
    def capture(label, reference, values):
        data = {}
        technical = []
        for name, value in values.items():
            if (
                name
                in {
                    "id",
                    "pk",
                    "key",
                    "mfa_last_counter",
                    "mfa_version",
                    "session_version",
                    "is_staff",
                    "is_superuser",
                }
                or name.endswith("_id")
                or secret_name(name)
            ):
                technical.append(name)
            elif name.startswith("encrypted_"):
                if not value:
                    data[name.removeprefix("encrypted_")] = None
                elif name in JSON_FIELDS:
                    data[name.removeprefix("encrypted_")] = safe_json(checked_body(value))
                else:
                    blocked.append({"model": label, "reference": reference, "field": name})
            else:
                data[name] = normalized(value)
        matched = projected_fields(label, reference, values, data, projected)
        if matched:
            correspondence.append({"model": label, "reference": reference, "fields": matched})
            data = {name: value for name, value in data.items() if name not in matched}
        if data:
            groups.setdefault(label, []).append(
                {"reference": reference, "data": data, "technical_fields_excluded": technical}
            )

    manifest = source(case, person, value_sink=capture)
    if (
        manifest["digest"] != inventory.source_digest
        or checked_body(inventory.encrypted_inventory) != manifest
    ):
        raise ValidationError("Access delivery inventory source changed")
    owner = case.account_subject_id or (person.subject_id if person else None)
    mail_scope = mail_records(
        (projected.get("subject_account") or {}).get("email", ""), owner=owner
    )
    if mail_scope["projected"]:
        groups["operations.Mail"] = mail_scope["projected"]
    sessions = session_records(owner, cutoff)
    blocked.extend(sessions["blocked"])
    queued = broker_records({row["blob"] for row in manifest["media"]})
    blocked.extend(queued["blocked"])
    from .redis_history_scope import history_records

    redis_history = history_records(
        {row["blob"] for row in manifest["media"]}, cutoff, case=case, inventory=inventory
    )
    blocked.extend(
        {"resource": "redis_history", "reason": reason} for reason in redis_history["blocked"]
    )
    if redis_history["records"]:
        groups["operations.QueueHistory"] = redis_history["records"]
    if redis_history.get("result_records"):
        groups["operations.TaskResultHistory"] = redis_history["result_records"]
    log_origins = log_records(
        {
            str(case.pk),
            str(person.pk) if person else "",
            (projected.get("subject_account") or {}).get("email", ""),
        }
        | {row["blob"] for row in manifest["media"]},
        cutoff,
        subjects={
            "account": {str(owner)} if owner else set(),
            "person": {str(person.pk)} if person else set(),
            "photo_blob": {row["blob"] for row in manifest["media"]},
        },
        case=case,
        inventory=inventory,
        owner=owner,
        email=(projected.get("subject_account") or {}).get("email", ""),
    )
    if log_origins.get("projected_mail"):
        groups.setdefault("operations.Mail", []).extend(log_origins["projected_mail"])
    if log_origins.get("projected"):
        groups["operations.LogEvent"] = log_origins["projected"]
    resource_scope = retained_resource_records(
        case,
        person,
        inventory,
        {
            "logs": fingerprint(canonical(log_origins)),
            "mail": fingerprint(canonical(mail_scope)),
            "sessions": fingerprint(canonical(sessions)),
            "queues": fingerprint(canonical(queued)),
            **(
                {"redis_history": fingerprint(canonical(redis_history))}
                if redis_history["configured"]
                else {}
            ),
        },
        {
            "logs": {
                row["record"]: row["content_digest"]
                for row in log_origins.get("candidates", [])
                if row["record"] in log_origins.get("unprojected_candidates", [])
            },
            "mail": {
                row["reference"]: row["content"]
                for row in mail_scope["records"]
                if row["reference"] not in {item["reference"] for item in mail_scope["projected"]}
            },
        },
    )
    if resource_scope["groups"]:
        groups["operations.RetainedResource"] = resource_scope["groups"]
    procedure = {
        "kind": case.kind,
        "submitted": safe_json(checked_body(case.encrypted_payload)),
        "clarifications": [
            safe_json(checked_body(row.encrypted_payload))
            for row in case.messages.filter(created_at__lte=cutoff).order_by("pk")
        ],
        "previous_responses": [
            safe_json(checked_body(row.encrypted_response))
            for row in case.responses.filter(response_version__lte=case.response_version).order_by(
                "response_version"
            )
        ],
    }
    infrastructure = {
        "storage": settings.MEDIA_STORAGE_PROVIDER,
        "verification": settings.VERIFICATION_PROVIDER,
        "email": settings.EMAIL_BACKEND,
        "logging_configuration": fingerprint(canonical(settings.LOGGING)),
        "production": settings.PRODUCTION,
    }
    return {
        "source": manifest["digest"],
        "groups": groups,
        "blocked": blocked,
        "procedure": procedure,
        "sessions": sessions["copy"],
        "session_evidence": sessions["evidence"],
        "queued_processing": queued["copy"],
        "queue_evidence": queued["evidence"],
        "redis_history": redis_history,
        "log_origins": log_origins,
        "mail_scope": mail_scope,
        "resource_scope": resource_scope,
        "infrastructure": infrastructure,
        "projected_fields": correspondence,
    }


def project_group(model, rows, decision):
    """Apply sparse, motivated changes; preserve every other original field."""
    from copy import deepcopy

    from .rights_access_field_decision import released

    status = decision.get("status") if isinstance(decision, dict) else None
    expected = {"status", "reason", "changes"} if status == "redacted" else {"status", "reason"}
    if (
        not isinstance(decision, dict)
        or set(decision) != expected
        or status not in {"included", "omitted", "redacted"}
        or not isinstance(decision["reason"], str)
        or not 20 <= len(decision["reason"].strip()) <= 2000
    ):
        raise ValidationError("Explicit group disclosure decision and reason required")
    if status == "omitted":
        return [], [{"model": model, "count": len(rows), "reason": decision["reason"]}]
    changes = decision.get("changes", {})
    originals = {row["reference"]: row for row in rows}
    if (
        not isinstance(changes, dict)
        or set(changes) - set(originals)
        or (status == "redacted" and not changes)
    ):
        raise ValidationError("Changes must identify original records")
    records, exclusions = [], []
    for reference, row in originals.items():
        data = deepcopy(row["data"])
        fields = changes.get(reference, {})
        if (
            not isinstance(fields, dict)
            or set(fields) - set(data)
            or (reference in changes and not fields)
        ):
            raise ValidationError("Changes must identify original fields")
        for field, change in fields.items():
            outcome = change.get("status") if isinstance(change, dict) else None
            keys = {"status", "reason", "value"} if outcome == "redacted" else {"status", "reason"}
            if (
                not isinstance(change, dict)
                or set(change) != keys
                or outcome not in {"omitted", "redacted"}
                or not isinstance(change["reason"], str)
                or not 20 <= len(change["reason"].strip()) <= 2000
            ):
                raise ValidationError("Motivated original field omission or redaction required")
            value = released(data[field], outcome, change.get("value"))
            if outcome == "omitted":
                del data[field]
            else:
                data[field] = value
            exclusions.append(
                {
                    "model": model,
                    "reference": reference,
                    "field": field,
                    "status": outcome,
                    "reason": change["reason"],
                }
            )
        records.append({"reference": reference, "data": data})
    return records, exclusions


def compile_package(inventory, export, original, decisions, *, cutoff, projected):
    if not isinstance(decisions, dict) or set(decisions) != {"models", "resources"}:
        raise ValidationError("Reviewed model and infrastructure decisions required")
    if not isinstance(decisions["models"], dict) or set(decisions["models"]) != set(
        original["groups"]
    ):
        raise ValidationError("Account for every nonempty indexed model as a group")
    if original["blocked"]:
        raise ValidationError("Unsupported scoped records require a typed delivery adapter")
    records, exclusions = [], []
    for row in original.get("mail_scope", {}).get("projected", []):
        exclusions.append(
            {
                "model": "operations.Mail",
                "reference": row["reference"],
                "field": "authentication_link",
                "status": "redacted",
                "reason": "Authentication capabilities are withheld to protect account security.",
            }
        )
    for model, rows in original["groups"].items():
        if model == "operations.RetainedResource":
            resource_decision = decisions["models"][model]
            if resource_decision.get("status") != "omitted":
                changes = resource_decision.get("changes", {})
                if resource_decision.get("status") != "redacted" or any(
                    changes.get(row["reference"], {}).get("content", {}).get("status")
                    not in {"omitted", "redacted"}
                    for row in rows
                ):
                    raise ValidationError(
                        "Retained resource contents require explicit redaction or omission"
                    )
        projected_rows, omitted_fields = project_group(model, rows, decisions["models"][model])
        if projected_rows:
            records.append({"model": model, "records": projected_rows})
        exclusions.extend(omitted_fields)
    resources = decisions["resources"]
    metadata_digest = original.get("redis_history", {}).get("metadata_digest")
    resource_fields = {"status", "reason"}
    if metadata_digest:
        resource_fields.add("redis_metadata_digest")
    if (
        not isinstance(resources, dict)
        or set(resources) not in (resource_fields, resource_fields | {"origin_digest"})
        or resources["status"] != "reviewed"
        or not isinstance(resources["reason"], str)
        or not 20 <= len(resources["reason"].strip()) <= 2000
    ):
        raise ValidationError("Motivated infrastructure scope assessment required")
    if metadata_digest and resources["redis_metadata_digest"] != metadata_digest:
        raise ValidationError("Exact Redis metadata review digest required")
    # Local acceptance cannot accredit an external provider or production operations.
    config = original["infrastructure"]
    external = (
        config["storage"] != "local"
        or config["verification"] != "simulator"
        or config["production"]
    )
    census = original.get("resource_scope", {})
    pending = []
    if (
        not census.get("configured")
        or census.get("pending")
        or resources.get("origin_digest") != census.get("digest")
    ):
        pending.append("infrastructure_content_accounting")
    if external:
        pending.append("external_operation_scope")
    if cutoff != inventory.created_at:
        raise ValidationError("Inventory preparation cutoff required")
    pending.extend(original.get("redis_history", {}).get("pending", []))
    if "historical_log_capture_coverage" in original.get("log_origins", {}).get("pending", []):
        pending.extend(original["log_origins"]["pending"])
    package = {
        "schema": "access-delivery-v1",
        "export": str(export.pk),
        "inventory": inventory.pk,
        "source": original["source"],
        "cutoff": cutoff.isoformat(),
        "decisions": decisions,
        "review_material": original,
        "copy": {
            "base": projected,
            "additional_records": records,
            "exclusions": exclusions,
            "procedure": original["procedure"],
            "sessions": original["sessions"],
            "queued_processing": original["queued_processing"],
            "infrastructure_assessment": {key: resources[key] for key in ("status", "reason")},
        },
        "partial": bool(pending),
        "pending": pending,
    }
    package["digest"] = fingerprint(canonical(package))
    return package


@sensitive_variables()
def recipient_payload(body):
    """Project an already validated final response, never the reviewer envelope."""
    from copy import deepcopy

    package = body.get("access_package") if isinstance(body, dict) else None
    if (
        not isinstance(package, dict)
        or package.get("schema") != "access-delivery-v1"
        or package.get("partial") is not False
        or package.get("pending") != []
        or not isinstance(package.get("copy"), dict)
        or set(package["copy"])
        != {
            "base",
            "additional_records",
            "exclusions",
            "procedure",
            "sessions",
            "queued_processing",
            "infrastructure_assessment",
        }
    ):
        raise ValidationError("Complete validated recipient copy required")
    return {
        "schema": "access-recipient-copy-v1",
        "simulation": body["simulation"],
        "prepared_at": package["cutoff"],
        "response": body["text"],
        "copy": deepcopy(package["copy"]),
    }


@sensitive_variables()
def validate_package(package, case, person, export, actor, proof, projected):
    from datetime import datetime

    if not isinstance(package, dict) or package.get("schema") != "access-delivery-v1":
        raise ValidationError("Typed access delivery package required")
    try:
        cutoff = datetime.fromisoformat(package["cutoff"])
        inventory = RightsAccessScopeInventory.objects.select_for_update().get(
            pk=package["inventory"],
            request=case,
            actor=actor,
            proof=proof,
            case_version=case.version,
            response_version=case.response_version,
            original_session_version=actor.session_version,
            original_mfa_version=actor.mfa_version,
            purged_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
    except (KeyError, TypeError, ValueError, RightsAccessScopeInventory.DoesNotExist) as error:
        raise ValidationError("Current scoped delivery inventory required") from error
    original = snapshot(case, person, inventory, cutoff=cutoff, projected=projected)
    expected = compile_package(
        inventory, export, original, package.get("decisions"), cutoff=cutoff, projected=projected
    )
    if expected != package:
        raise ValidationError("Access package contents, scope or origin changed")
    return package


def projected_fields(model, reference, raw, data, projected):
    """Match only explicit typed projections, never arbitrary equal leaves."""
    candidates = []
    aliases = {
        "is_active": "active",
        "manager_kind": "manager_type",
        "previous_manager_kind": "previous_manager_type",
    }
    if model == "core.User" and projected.get("subject_account"):
        candidates = [projected["subject_account"]]
    elif model == "listings.Revision":
        for revision in projected.get("revisions", []):
            expected = fingerprint(canonical({"model": model, "pk": revision["revision"]}))
            if expected == reference:
                candidates = [revision | revision.get("contacts", {})]
    elif model == "listings.Rate":
        for revision in projected.get("revisions", []):
            if str(raw.get("revision_id")) == revision["revision"]:
                candidates = revision.get("rates", [])
    if not candidates:
        return []
    return sorted(
        name
        for name, value in data.items()
        if any(
            aliases.get(name, name) in row and row[aliases.get(name, name)] == value
            for row in candidates
        )
    )
