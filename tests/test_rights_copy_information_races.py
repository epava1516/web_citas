"""Information-save races with independent connections and observed PostgreSQL locks."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_information import draft
from test_rights_exports import prepared

from apps.core.models import User
from apps.safety.models import RightsAction, RightsCopyInformation, RightsRequest
from apps.safety.rights import fingerprint
from apps.safety.rights_copy_information import inspect, record
from apps.safety.rights_exports import canonical, reviewer_case, source_copy

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "change", ["replay", "conflict", "permission", "proof", "session", "mfa", "source"]
)
def test_information_save_serializes_versions_and_rechecks_authority_after_observed_wait(
    request, settings, change
):
    case, actor, _, _, _, person = prepared(request, settings)
    information = draft()
    with transaction.atomic():
        current, current_person, listing = reviewer_case(actor, case.pk)
        source_digest = fingerprint(canonical(source_copy(current_person, listing, current)))
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
                row = record(
                    user,
                    case.pk,
                    version,
                    action_key,
                    0,
                    "synthetic-policy-v1",
                    "Save information after observed PostgreSQL wait",
                    information,
                    expected_source_digest=source_digest,
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
    actions = RightsAction.objects.filter(request=case, operation="copy_info_save")
    rows = RightsCopyInformation.objects.filter(request=case)
    if change == "replay":
        assert all(result[0] == "admitted" for result in results)
        assert results[0][1] == results[1][1]
        assert actions.count() == rows.count() == 1
        assert rows.get().version == 1
    elif change == "conflict":
        assert sorted(result[0] for result in results) == ["admitted", "denied"]
        assert actions.count() == rows.count() == 1
        assert rows.get().version == 1
    else:
        assert all(result[0] == "denied" for result in results)
        assert not actions.exists() and not rows.exists()
    case.refresh_from_db()
    assert case.version == version and case.status == "reviewing"


@pytest.mark.parametrize(
    "change", ["replay", "permission", "proof", "session", "mfa", "source", "purge"]
)
def test_information_read_rechecks_authority_and_body_after_observed_wait(
    request, settings, change
):
    case, actor, _, _, _, person = prepared(request, settings)
    information = draft()
    with transaction.atomic():
        current, current_person, listing = reviewer_case(actor, case.pk)
        source_digest = fingerprint(canonical(source_copy(current_person, listing, current)))
    saved = record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        0,
        "synthetic-policy-v1",
        "Save draft before concurrent audited reads",
        information,
        expected_source_digest=source_digest,
    )
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
                row, body = inspect(
                    user,
                    case.pk,
                    version,
                    action_key,
                    saved.pk,
                    "Read information after observed PostgreSQL wait",
                )
                assert body == information
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
            elif change == "purge":
                RightsCopyInformation.objects.filter(pk=saved.pk).update(
                    encrypted_information="", purged_at=timezone.now()
                )
            elif change == "source":
                person.listing.revisions.all().update(
                    description="Source changed during observed wait"
                )
        results = [future.result(timeout=15) for future in futures]
    actions = RightsAction.objects.filter(request=case, operation="copy_info_read")
    rows = RightsCopyInformation.objects.filter(request=case)
    if change == "replay":
        assert all(result[0] == "admitted" for result in results)
        assert results[0][1] == results[1][1]
        assert actions.count() == rows.count() == 1
        assert rows.get().version == 1
    else:
        assert all(result[0] == "denied" for result in results)
        assert not actions.exists()
        assert rows.count() == 1
    case.refresh_from_db()
    assert case.version == version and case.status == "reviewing"
