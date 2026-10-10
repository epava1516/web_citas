"""Validation seals: replay-proven equality of every database input of a full validation.

A full ``validate_export_binding`` is a deterministic function of the rows its queries return,
the objects its caller passes, the current time (only through ``expires_at`` comparisons), the
code, and the image files it reads. A seal records, after a full validation succeeds:

- every SELECT it executed with its parameters (encrypted) and the PostgreSQL md5 of the
  ordered result of each, computed by replaying the statement inside the same transaction;
- a digest of every concrete field of the caller's case, subject and export objects;
- a rule version (hash of the application code);
- ``valid_until``: the earliest ``expires_at`` of any row the validation loaded.

A later validation of the same inputs replays the statements and asks PostgreSQL only for the
md5 of each result. Equal digests, equal caller digest, equal rule version and a current time
before ``valid_until`` mean the full validation would read identical database inputs and reach
the same result; image bytes are still re-read and hashed by the caller. Any difference runs the
full validation, exactly as before. Nothing here grants authority or replaces caller checks.
"""

import hashlib
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from functools import cache
from pathlib import Path
from uuid import UUID

from cryptography.fernet import InvalidToken
from django.db import connection
from django.db.models.signals import post_init
from django.utils import timezone
from psycopg.types.json import Jsonb

from .crypto import seal, unseal
from .rights import fingerprint

_recording = ContextVar("rights_validation_recording", default=None)


@cache
def rule_version():
    """Hash of every application module: any code change invalidates every seal."""
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def caller_digest(*instances):
    values = []
    for instance in instances:
        if instance is None:
            values.append(None)
            continue
        fields = {
            field.attname: repr(getattr(instance, field.attname, None))
            for field in instance._meta.concrete_fields
        }
        values.append(
            {
                "model": instance._meta.label,
                "pk": str(instance.pk),
                "fields": dict(sorted(fields.items())),
            }
        )
    return fingerprint(repr(values))


def _loaded(sender, instance, **kwargs):
    state = _recording.get()
    if state is None:
        return
    value = getattr(instance, "__dict__", {}).get("expires_at")
    if isinstance(value, datetime):
        state["expiries"].append(value)


post_init.connect(_loaded, dispatch_uid="rights_validation_seal_expiries")


@contextmanager
def recording():
    """Capture SELECT statements and loaded expiries of the enclosed full validation."""
    state = {"statements": [], "expiries": []}

    def wrapper(execute, sql, params, many, context):
        if not many and sql.lstrip().upper().startswith("SELECT"):
            state["statements"].append((sql, list(params) if params is not None else None))
        return execute(sql, params, many, context)

    token = _recording.set(state)
    try:
        with connection.execute_wrapper(wrapper):
            yield state
    finally:
        _recording.reset(token)


def encode(value):
    """Typed JSON form of a SQL parameter, decoded back to an equal Python value."""
    if isinstance(value, Jsonb):
        return {"jsonb": value.obj}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return {"float": repr(value)}
    if isinstance(value, UUID):
        return {"uuid": str(value)}
    if isinstance(value, datetime):
        return {"datetime": value.isoformat()}
    if isinstance(value, date):
        return {"date": value.isoformat()}
    if isinstance(value, Decimal):
        return {"decimal": str(value)}
    if isinstance(value, (list, tuple)):
        return {"list": [encode(item) for item in value]}
    if isinstance(value, (bytes, memoryview)):
        return {"bytes": bytes(value).hex()}
    raise TypeError(f"Unsupported sealed parameter type: {type(value).__name__}")


def decode(value):
    if not isinstance(value, dict):
        return value
    ((kind, item),) = value.items()
    return {
        "jsonb": Jsonb,
        "float": float,
        "uuid": UUID,
        "datetime": datetime.fromisoformat,
        "date": date.fromisoformat,
        "decimal": Decimal,
        "bytes": bytes.fromhex,
        "list": lambda items: [decode(entry) for entry in items],
    }[kind](item)


def _replay(statements):
    digests = []
    with connection.cursor() as cursor:
        for sql, params in statements:
            # Ordering by the row text makes the digest independent of result order.
            cursor.execute(
                f"SELECT md5(coalesce(string_agg(q::text, '|' ORDER BY q::text), '')) "
                f"FROM ({sql}) AS q",
                params,
            )
            digests.append(cursor.fetchone()[0])
    return digests


def create(export, state, caller):
    from .models import RightsExportValidationSeal

    statements = state["statements"]
    expiries = state["expiries"] + [
        value
        for value in (getattr(item, "expires_at", None) for item in caller.values())
        if isinstance(value, datetime)
    ]
    return RightsExportValidationSeal.objects.create(
        export=export,
        rule_version=rule_version(),
        caller_digest=caller_digest(*caller.values()),
        encrypted_statements=seal(
            {
                "statements": [
                    [sql, None if params is None else [encode(item) for item in params]]
                    for sql, params in statements
                ]
            }
        ),
        result_digests=_replay(statements),
        valid_until=min(expiries) if expiries else timezone.now(),
    )


def holds(export, caller):
    """True only when replaying every recorded statement returns identical results."""
    from .models import RightsExportValidationSeal

    now = timezone.now()
    candidate = (
        RightsExportValidationSeal.objects.filter(
            export=export,
            rule_version=rule_version(),
            caller_digest=caller_digest(*caller.values()),
            valid_until__gt=now,
        )
        .order_by("-pk")
        .first()
    )
    if candidate is None:
        return False
    try:
        statements = [
            (sql, None if params is None else [decode(item) for item in params])
            for sql, params in unseal(candidate.encrypted_statements)["statements"]
        ]
    except (InvalidToken, ValueError, TypeError, KeyError):
        return False
    return _replay(statements) == candidate.result_digests
