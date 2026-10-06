"""General rights-action authority after observed PostgreSQL wait; synthetic identities."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import User
from apps.safety.models import RightsAction, RightsRequest
from apps.safety.rights_actions import act

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("replay", [False, True])
@pytest.mark.parametrize(
    "operation, codename",
    [
        ("unassign", "manage_rights_assignment"),
        ("withdraw", "execute_rights_request"),
        ("extend", "extend_rights_deadline"),
    ],
)
def test_specific_rights_permission_is_revalidated_after_observed_wait(
    request, settings, monkeypatch, operation, codename, replay
):
    case, author, _, _, _, _ = ready(
        request,
        settings,
        monkeypatch,
        kind="representation" if operation == "withdraw" else "access",
    )
    permission = Permission.objects.get(codename=codename)
    author.user_permissions.add(permission)
    data = {
        "key": uuid4(),
        "version": case.version,
        "operation": operation,
        "reason": "Clarify synthetic request before observed authority revocation",
    }
    if operation == "extend":
        data.update(additional_months=1, extension_reason="complexity")
    existing = act(author, case.pk, **data) if replay else None
    case.refresh_from_db()
    original = case.version, case.response_version, case.status, case.initial_due_at
    baseline = RightsAction.objects.filter(request=case, operation=operation).count()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=author.pk)
            # Prime the same permission cache that the HTTP/service caller may carry.
            assert actor.has_perm("safety.review_rights_request")
            assert actor.has_perm("safety." + codename)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                return act(actor, case.pk, **data).pk
            except (PermissionDenied, ValidationError):
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            worker = pids.get(timeout=5)
            assert worker != holder
            observe_blocked(worker, holder)
            author.user_permissions.remove(permission)
        result = future.result(timeout=30)
    assert result is None, f"Revoked {codename} still returned action {result}; replay={replay}"
    assert RightsAction.objects.filter(request=case, operation=operation).count() == baseline
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original
    if existing:
        assert RightsAction.objects.get(key=data["key"]).request_id == existing.pk
    author.user_permissions.add(permission)
    # Positive control: restoring just this permission permits the same operation/key.
    allowed = act(User.objects.get(pk=author.pk), case.pk, **data)
    assert allowed.pk == case.pk
    assert RightsAction.objects.get(key=data["key"]).operation == operation
