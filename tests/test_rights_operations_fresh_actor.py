"""Finite public-service denials for stale operators, including authorized old replays."""

import json
import os
import sys
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db.models import F
from django.utils import timezone
from test_erasure_inventory import values as inventory_values
from test_operational_recovery_authority_wait import _snapshot
from test_privacy_publication_holds import values as hold_values
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_operations_authority_wait import _domain_queries
from test_rights_responses import ready
from test_rights_verification import payload as verification_payload
from test_rights_verification import prepared as verification_prepared
from test_rights_verification import read

from apps.core.models import User
from apps.safety.erasure_inventory import prepare
from apps.safety.privacy_holds import hold
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)
OPERATIONS = ["hold", "inventory", "start", "result"]
BASE_CHANGES = [
    "primary_permission", "inactive", "account_erased", "mfa_disabled",
    "mfa_version", "session_version",
]
CASES = [
    pytest.param(operation, change, False, id=f"{operation}-{change}")
    for operation in OPERATIONS for change in BASE_CHANGES
] + [
    pytest.param(operation, "review_permission", False, id=f"{operation}-review_permission")
    for operation in ["hold", "inventory", "result"]
] + [
    pytest.param(operation, "primary_permission", True, id=f"{operation}-revoked-replay")
    for operation in OPERATIONS
]


def _owned_serial_here(request, settings):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL rights service negatives only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()


def _actor_fields(actor):
    return (actor.is_active, actor.account_erased_at, actor.mfa_enabled,
            actor.mfa_version, actor.session_version)


def _prepare(request, settings, monkeypatch, operation):
    if operation in {"hold", "inventory"}:
        kind = "restriction" if operation == "hold" else "erase"
        case, original, client, _, _, person = ready(request, settings, monkeypatch, kind)
        case.refresh_from_db()
        read(client, case)
        case.refresh_from_db()
        proof = case.proofs.latest("created_at")
        assert proof.provider == "simulator" and proof.status == "passed"
        assert proof.case_version == case.version and proof.scope == kind
        actor = User.objects.get(pk=original.pk)
        values = hold_values(case) if operation == "hold" else inventory_values(case)
        service = hold if operation == "hold" else prepare
        return case, person, actor, "safety.execute_rights_request", lambda: service(
            actor, case.pk, **values
        )
    case, original, client, person, verifier, other = verification_prepared(request, settings)
    case.refresh_from_db()
    read(client, case)
    case.refresh_from_db()
    path, values = verification_payload(client, case, "start")
    if operation == "start":
        assert not case.proofs.exists()
        actor = User.objects.get(pk=original.pk)
        values = {key: value for key, value in values.items() if key != "operation"}
        return case, person, actor, "safety.review_rights_request", lambda: start(
            actor, case.pk, **values
        )
    assert client.post(path, values).status_code == 302
    case.refresh_from_db()
    read(other, case)
    case.refresh_from_db()
    proof = case.proofs.latest("created_at")
    actor = User.objects.get(pk=verifier.pk)
    assert proof.provider == "simulator" and proof.status == "pending"
    assert proof.case_version == case.version
    assert actor.pk not in (proof.initiated_by_id, case.assigned_to_id)
    _, values = verification_payload(other, case, "result", outcome="passed")
    event = simulate_event(proof.pk, **{
        key: value for key, value in values.items() if key != "operation"
    })
    return case, person, actor, "safety.verify_rights_scope", lambda: receive_event(actor, event)


def _invalidate(actor, change, primary):
    if change in {"primary_permission", "review_permission"}:
        name = primary if change == "primary_permission" else "safety.review_rights_request"
        app_label, codename = name.split(".")
        permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        external = User.objects.get(pk=actor.pk)
        assert external.user_permissions.filter(pk=permission.pk).exists()
        external.user_permissions.remove(permission)
        assert not User.objects.get(pk=actor.pk).has_perm(name)
        return
    changes = {
        "inactive": {"is_active": False},
        "account_erased": {"account_erased_at": timezone.now()},
        "mfa_disabled": {"mfa_enabled": False},
        "mfa_version": {"mfa_version": F("mfa_version") + 1},
        "session_version": {"session_version": F("session_version") + 1},
    }
    assert User.objects.filter(pk=actor.pk).update(**changes[change]) == 1
    current = User.objects.get(pk=actor.pk)
    if change == "inactive":
        assert not current.is_active
    elif change == "account_erased":
        assert current.account_erased_at is not None
    elif change == "mfa_disabled":
        assert not current.mfa_enabled
    else:
        assert getattr(current, change) == getattr(actor, change) + 1


@pytest.mark.parametrize("operation,change,replay", CASES)
def test_rights_service_denies_cached_revoked_operator_and_old_replay(
    request, settings, monkeypatch, record_property, operation, change, replay
):
    _owned_serial_here(request, settings)
    case, person, actor, primary, invoke = _prepare(request, settings, monkeypatch, operation)
    assert actor.is_active and actor.account_erased_at is None and actor.mfa_enabled
    assert not actor.is_superuser
    required = {primary, "safety.review_rights_request"}
    assert all(actor.has_perm(name) for name in required)
    assert "_perm_cache" in actor.__dict__ and "_user_perm_cache" in actor.__dict__
    cache = {name: frozenset(actor.__dict__[name]) for name in [
        "_perm_cache", "_user_perm_cache", "_group_perm_cache"
    ] if name in actor.__dict__}
    fields = _actor_fields(actor)
    queries = _domain_queries(case, person)
    if replay:
        initial = _snapshot(queries)
        assert invoke() is not None
        after = _snapshot(queries)
        target = {"hold": "holds", "inventory": "inventory", "start": "proofs",
                  "result": "proof_events"}[operation]
        assert after["sha256"] != initial["sha256"]
        assert after["tables"][target]["count"] == initial["tables"][target]["count"] + 1
    before = _snapshot(queries)
    observed = {"operation": operation, "change": change, "replay": replay,
                "legitimate_initial_authority": True, "legitimate_replay_reference": replay,
                "denied": False, "domain_before": before,
                "scope": "Public service call with naturally cached original actor; external ORM "
                         "revocation. Replay references retain a legitimate prior effect. No added "
                         "middleware, HTTP, concurrency, latency, identity or provider evidence."}
    try:
        _invalidate(actor, change, primary)
        assert _actor_fields(actor) == fields
        assert all(actor.has_perm(name) for name in required)
        assert all(frozenset(actor.__dict__[name]) == value for name, value in cache.items())
        with pytest.raises(PermissionDenied):
            invoke()
        observed["denied"] = True
        assert _snapshot(queries) == before
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["domain_after"] = _snapshot(queries)
        observed["domain_unchanged"] = observed["domain_after"] == before
        record_property("rights_operations_fresh_actor", json.dumps(
            observed, allow_nan=False, sort_keys=True,
        ))
