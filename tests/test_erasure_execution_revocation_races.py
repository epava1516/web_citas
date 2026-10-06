"""Scoped erasure authority after observed PostgreSQL wait; synthetic identities."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_erasure_execution import payload, plan_fixture
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AccountToken, RecoveryCode, User
from apps.listings.models import Favorite
from apps.safety.erasure_execution import execute
from apps.safety.models import ErasureExecution, RightsAction, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("replay", [False, True])
@pytest.mark.parametrize("change", ["permission", "session", "mfa"])
def test_erasure_denies_authority_revoked_during_observed_wait(
    request, settings, monkeypatch, change, replay
):
    case, author, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch
    )
    data = payload(case)
    existing = execute(author, case.pk, plan.pk, **data) if replay else None
    case.refresh_from_db()
    original = case.version, case.response_version, case.status, case.initial_due_at
    def effects():
        return (
            ErasureExecution.objects.count(),
            RightsAction.objects.filter(operation="erasure_execute").count(),
            AccountToken.objects.filter(user=person.subject).count(),
            RecoveryCode.objects.filter(user=person.subject).count(),
            Favorite.objects.filter(user=person.subject).count(),
        )

    baseline = effects()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=author.pk)
            # Prime the same permission cache that the HTTP/service caller may carry.
            assert actor.has_perm("safety.review_rights_request")
            assert actor.has_perm("safety.execute_rights_request")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                return execute(actor, case.pk, plan.pk, **data).pk
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
            if change == "permission":
                author.user_permissions.clear()
            else:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=author.pk).update(**{field: getattr(author, field) + 1})
        result = future.result(timeout=30)
    assert result is None, f"Revoked {change} still returned erasure {result}; replay={replay}"
    assert effects() == baseline
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original
    if existing:
        assert ErasureExecution.objects.get(pk=existing.pk).action.key == data["key"]
