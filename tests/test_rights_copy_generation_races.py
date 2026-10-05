"""Direct-generation races with independent connections and observed PostgreSQL locks."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_compilation import review_all
from test_rights_exports import prepared

from apps.core.models import User
from apps.safety.models import RightsAction, RightsExport, RightsRequest
from apps.safety.rights_copy_page_review import generate_pages

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "change", ["replay", "conflict", "permission", "proof", "session", "mfa", "source"]
)
def test_direct_generation_serializes_and_rechecks_authority_after_observed_wait(
    request, settings, change
):
    case, actor, _, _, _, person = prepared(request, settings)
    review_all(case, actor)
    key = uuid4()
    pids = Queue()
    version = case.version

    def attempt(action_key):
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            assert user.has_perm("safety.review_rights_request")
            assert user.has_perm("safety.execute_rights_request")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                row = generate_pages(
                    user,
                    case.pk,
                    version,
                    action_key,
                    "Generate pages after observed PostgreSQL wait",
                )
            except (PermissionDenied, ValidationError):
                return "denied", None
            return "admitted", row.pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            keys = [key, uuid4() if change == "conflict" else key]
            futures = [pool.submit(attempt, value) for value in keys]
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
            elif change == "source":
                person.listing.revisions.all().update(
                    description="Source changed during observed wait"
                )
        results = [future.result(timeout=15) for future in futures]
    actions = RightsAction.objects.filter(request=case, operation="copy_pages_export")
    rows = RightsExport.objects.filter(action__request=case)
    if change == "replay":
        assert all(result[0] == "admitted" for result in results)
        assert results[0][1] == results[1][1]
        assert actions.count() == rows.count() == 1
        assert rows.get().case_version == version + 1
    elif change == "conflict":
        assert sorted(result[0] for result in results) == ["admitted", "denied"]
        assert actions.count() == rows.count() == 1
        assert rows.get().case_version == version + 1
    else:
        assert all(result[0] == "denied" for result in results)
        assert not actions.exists() and not rows.exists()
    case.refresh_from_db()
    assert case.version == version + (1 if change in {"replay", "conflict"} else 0)
    assert case.status == "reviewing"
    assert RightsAction.objects.filter(request=case, operation="export").count() == (
        1 if change in {"replay", "conflict"} else 0
    )
