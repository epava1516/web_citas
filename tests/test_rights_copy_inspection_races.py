"""Observed PostgreSQL waits for inspection replay and stale authority."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared

from apps.core.models import User
from apps.safety.models import RightsAction, RightsRequest
from apps.safety.rights_copy_inspection import inspect_page

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("change", ["none", "permission", "proof", "session", "mfa"])
def test_inspection_rechecks_authority_after_observed_wait_and_replays_once(
    request, settings, change
):
    case, actor, _, _, _, _ = prepared(request, settings)
    key = uuid4()
    pids = Queue()
    version = case.version

    def attempt():
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            assert user.has_perm("safety.review_rights_request")
            assert user.has_perm("safety.execute_rights_request")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                value = inspect_page(
                    user, case.pk, version, key, "Inspect source after observed PostgreSQL wait"
                )
            except (PermissionDenied, ValidationError):
                return "denied", None
            return "admitted", value["entries"]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            futures = [pool.submit(attempt) for _ in range(2)]
            workers = [pids.get(timeout=5) for _ in range(2)]
            assert len(set(workers + [holder])) == 3
            for pid in workers:
                observe_blocked(pid, holder)
            assert not any(future.done() for future in futures)
            if change == "permission":
                actor.user_permissions.clear()
            elif change == "proof":
                case.proofs.update(status="failed")
            elif change in {"session", "mfa"}:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=actor.pk).update(**{field: getattr(actor, field) + 1})
        results = [future.result(timeout=15) for future in futures]
    actions = RightsAction.objects.filter(request=case, operation="copy_page_read")
    if change == "none":
        assert all(result[0] == "admitted" for result in results)
        assert results[0][1] == results[1][1] and actions.count() == 1
    else:
        assert all(result[0] == "denied" for result in results)
        assert not actions.exists()
    case.refresh_from_db()
    assert case.version == version and case.status == "reviewing"
