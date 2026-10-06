"""Legacy response authority after observed PostgreSQL wait; synthetic identities."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready, values

from apps.core.models import User
from apps.safety.models import RightsNotice, RightsRequest, RightsResponse
from apps.safety.rights_responses import issue

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("replay", [False, True])
@pytest.mark.parametrize("change", ["permission", "session", "mfa"])
def test_legacy_response_denies_authority_revoked_during_observed_wait(
    request, settings, monkeypatch, change, replay
):
    case, author, _, _, _, _ = ready(request, settings, monkeypatch)
    data = values(case)
    existing = issue(author, case.pk, **data) if replay else None
    case.refresh_from_db()
    original = case.version, case.response_version, case.status, case.initial_due_at
    baseline = RightsResponse.objects.count(), RightsNotice.objects.count()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=author.pk)
            # Prime the same permission cache that the HTTP/service caller may carry.
            assert actor.has_perm("safety.review_rights_request")
            assert actor.has_perm("safety.respond_rights_request")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                return issue(actor, case.pk, **data).pk
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
    assert result is None, f"Revoked {change} still returned response {result}; replay={replay}"
    assert (RightsResponse.objects.count(), RightsNotice.objects.count()) == baseline
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original
    if existing:
        assert RightsResponse.objects.get(pk=existing.pk).key == data["key"]
