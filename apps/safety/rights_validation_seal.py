"""Replay seals of the ordered results actually consumed by full validation.

Recording annotates each result row with a PostgreSQL SHA-256 before it reaches
Python. The buffered cursor strips that annotation and preserves the original
columns/order/DBAPI fetch semantics. Replaying later returns only the combined
hash: a different row, insertion, deletion or ordering always invalidates it.
Caller objects (including cached relations), code/configuration, expiries and
external image bytes remain independent inputs. Seals never grant authority.
"""

import hashlib
import re
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from functools import cache
from pathlib import Path
from uuid import UUID

from cryptography.fernet import InvalidToken
from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.db.models.signals import post_init
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from psycopg.types.json import Jsonb

from .canonical_kernel_loader import kernel_identity
from .crypto import seal, unseal
from .rights import fingerprint

_recording = ContextVar("rights_validation_recording", default=None)
SCHEMA = "ordered-consumed-select-sha256-v2"
EXPIRY_FIELDS = {"expires_at", "receipt_expires_at", "valid_until"}
_VOLATILE = re.compile(
    r"\b(now|current_timestamp|current_date|clock_timestamp|random|nextval|set_config)\b", re.I
)


@cache
def _code_version():
    root = Path(__file__).resolve().parents[2]
    digest = hashlib.sha256()
    for directory in (root / "apps", root / "config"):
        for path in sorted(directory.rglob("*.py")):
            digest.update(str(path.relative_to(root)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


@sensitive_variables()
def rule_version():
    # Configuration remains live: changing a policy/key in a running process
    # invalidates seals even when the code hash is unchanged. Never store values.
    values = sorted(
        (name, repr(getattr(settings, name))) for name in dir(settings) if name.isupper()
    )
    return fingerprint(repr((_code_version(), kernel_identity(), values)))


@sensitive_variables()
def _caller_values(instances):
    seen = set()

    def value(instance):
        if instance is None:
            return None
        if id(instance) in seen:
            return (instance._meta.label, str(instance.pk))
        seen.add(id(instance))
        fields = {
            field.attname: repr(getattr(instance, field.attname, None))
            for field in instance._meta.concrete_fields
        }
        relations = {
            name: value(related)
            for name, related in sorted(instance._state.fields_cache.items())
            if related is None or hasattr(related, "_meta")
        }
        return {"model": instance._meta.label, "fields": fields, "relations": relations}

    return [value(instance) for instance in instances]


@sensitive_variables()
def caller_digest(*instances):
    return fingerprint(repr(_caller_values(instances)))


def _expiries(instance, seen=None):
    if instance is None:
        return []
    seen = seen if seen is not None else set()
    if id(instance) in seen:
        return []
    seen.add(id(instance))
    values = [
        item
        for name, item in instance.__dict__.items()
        if name in EXPIRY_FIELDS and isinstance(item, datetime)
    ]
    for related in instance._state.fields_cache.values():
        if related is not None and hasattr(related, "_meta"):
            values.extend(_expiries(related, seen))
    return values


def _loaded(sender, instance, **kwargs):
    state = _recording.get()
    if state is not None:
        state["expiries"].extend(_expiries(instance))


post_init.connect(_loaded, dispatch_uid="rights_validation_seal_expiries")


class _ResultCursor:
    """An ordinary result cursor; no result annotation is visible to its caller."""

    def __init__(self, raw, rows, description):
        self.raw, self.rows, self.description = raw, deque(rows), description

    def __getattr__(self, name):
        return getattr(self.raw, name)

    def fetchone(self):
        return self.rows.popleft() if self.rows else None

    def fetchmany(self, size=None):
        size = self.raw.arraysize if size is None else size
        return [self.rows.popleft() for _ in range(min(size, len(self.rows)))]

    def fetchall(self):
        rows = list(self.rows)
        self.rows.clear()
        return rows

    def __iter__(self):
        return self

    def __next__(self):
        value = self.fetchone()
        if value is None:
            raise StopIteration
        return value


def _has_datetime(params):
    if params is None:
        return False
    values = params.values() if isinstance(params, dict) else params
    return any(
        isinstance(value, datetime) or (isinstance(value, (list, tuple)) and _has_datetime(value))
        for value in values
    )


_ROW_HASH = "encode(sha256(convert_to(row_to_json(q)::text, 'UTF8')), 'hex')"


def _annotated(sql):
    return f"SELECT q.*, {_ROW_HASH} AS _seal_hash FROM ({sql}) AS q"


@contextmanager
@sensitive_variables()
def recording():
    state = {"statements": [], "digests": [], "expiries": [], "supported": True}

    def wrapper(execute, sql, params, many, context):
        cursor = context["cursor"]
        if isinstance(cursor.cursor, _ResultCursor):
            cursor.cursor = cursor.cursor.raw
        if not isinstance(sql, str):
            # Driver composables must reach the executor unchanged. They cannot be
            # safely inspected or annotated here; decline the whole seal instead.
            state["supported"] = False
            return execute(sql, params, many, context)
        if many or not sql.lstrip().upper().startswith("SELECT") or _VOLATILE.search(sql):
            # A write or unsupported SQL must not become an accidentally partial seal.
            if not sql.lstrip().upper().startswith(("SAVEPOINT", "RELEASE", "ROLLBACK")):
                state["supported"] = False
            return execute(sql, params, many, context)
        execute(_annotated(sql), params, many, context)
        raw = cursor.cursor
        rows = raw.fetchall()
        description = raw.description[:-1]
        digest = hashlib.sha256("".join(row[-1] for row in rows).encode()).hexdigest()
        plain = [row[:-1] for row in rows]
        expiry_columns = [index for index, column in enumerate(description)
                          if column.name in EXPIRY_FIELDS]
        for index in expiry_columns:
            state["expiries"].extend(
                row[index] for row in plain if isinstance(row[index], datetime)
            )
        if not expiry_columns and _has_datetime(params):
            # A time-parameterized filter whose result exposes no expiry column (exists,
            # count, aggregates) cannot bound valid_until: replaying it with the recorded
            # instant could keep a stale answer. Decline the seal; full validation stays.
            state["supported"] = False
        state["statements"].append((sql, list(params) if params is not None else None))
        state["digests"].append(digest)
        cursor.cursor = _ResultCursor(raw, plain, description)
        return cursor

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


_REPLAY_PIPELINE_LIMIT = 8


def _replay_query(sql):
    return (
        "SELECT encode(sha256(convert_to(coalesce(string_agg(_seal_hash, ''), ''), "
        f"'UTF8')), 'hex') FROM ({_annotated(sql)}) AS sealed_rows"
    )


def _replay_serial(statements):
    digests = []
    with connection.cursor() as cursor:
        for sql, params in statements:
            cursor.execute(_replay_query(sql), params)
            digests.append(cursor.fetchone()[0])
    return digests


def _pipeline_connection():
    import psycopg

    # Only the actual PostgreSQL driver/connection supports this protocol. A
    # nested pipeline or recording context keeps the established serial path.
    raw = connection.connection
    supported = getattr(getattr(psycopg, 'Pipeline', None), 'is_supported', None)
    if (connection.vendor != "postgresql" or not isinstance(raw, psycopg.Connection)
            or not callable(getattr(raw, "pipeline", None))
            or getattr(raw, "_pipeline", None) is not None
            or _recording.get() is not None
            or not callable(supported) or not supported()):
        return None
    return raw


def _replay_pipeline(statements, raw):
    from contextlib import ExitStack

    digests = []
    for start in range(0, len(statements), _REPLAY_PIPELINE_LIMIT):
        # Cursor closure follows pipeline exit/drain, which itself precedes the
        # caller's savepoint rollback on errors. Sync/exit errors also need
        # Django translation: they occur outside cursor.execute().
        with connection.wrap_database_errors, ExitStack() as cursors:
            with raw.pipeline() as pipeline:
                pending = []
                for sql, params in statements[start:start + _REPLAY_PIPELINE_LIMIT]:
                    cursor = cursors.enter_context(connection.cursor())
                    cursor.execute(_replay_query(sql), params)
                    pending.append(cursor)
                pipeline.sync()
                for cursor in pending:
                    digests.append(cursor.fetchone()[0])
    return digests


def _replay(statements):
    # Individual statements and their server execution order are unchanged;
    # grouping only amortizes transport waits, never combines SQL snapshots.
    raw = _pipeline_connection()
    return _replay_serial(statements) if raw is None else _replay_pipeline(statements, raw)


@sensitive_variables()
def create(export, state, caller):
    from .models import RightsExportValidationSeal

    expiries = state["expiries"] + [value for item in caller.values() for value in _expiries(item)]
    if not state["supported"] or not state["statements"] or not expiries:
        return None
    try:
        encoded = [
            [sql, None if params is None else [encode(item) for item in params]]
            for sql, params in state["statements"]
        ]
    except (ValueError, TypeError):
        # An optional accelerator must never break an otherwise valid operation.
        return None
    return RightsExportValidationSeal.objects.create(
        export=export,
        rule_version=rule_version(),
        caller_digest=state.get("caller_digest") or caller_digest(*caller.values()),
        encrypted_statements=seal({"schema": SCHEMA, "statements": encoded}),
        result_digests=state["digests"],
        valid_until=min(expiries),
    )


@sensitive_variables()
def holds(export, caller):
    from .models import RightsExportValidationSeal

    if not connection.in_atomic_block:
        return False
    candidate = (
        RightsExportValidationSeal.objects.filter(
            export=export,
            rule_version=rule_version(),
            caller_digest=caller_digest(*caller.values()),
            valid_until__gt=timezone.now(),
        )
        .order_by("-pk")
        .first()
    )
    if candidate is None:
        return False
    try:
        value = unseal(candidate.encrypted_statements)
        if value.get("schema") != SCHEMA:
            return False
        statements = [
            (sql, None if params is None else [decode(item) for item in params])
            for sql, params in value["statements"]
        ]
        # SQL invalidated by a schema change rolls back only this savepoint.
        with transaction.atomic():
            return (
                _replay(statements) == candidate.result_digests
                and timezone.now() < candidate.valid_until
            )
    except (InvalidToken, ValueError, TypeError, KeyError, DatabaseError):
        return False
