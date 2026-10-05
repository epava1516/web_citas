from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_information import draft
from test_rights_exports import prepared
from test_rights_verification import read

from apps.core.models import LegalDocument, User
from apps.safety.models import RightsAction, RightsCopyInformationReview, RightsRequest
from apps.safety.rights_copy_information import record as save
from apps.safety.rights_information_policy import published_policy
from apps.safety.rights_information_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "change", ["replay", "conflict", "permission", "proof", "session", "mfa", "source", "policy"]
)
def test_independent_decision_rechecks_after_observed_case_wait(request, settings, change):
    case, author, _, _, _, person = prepared(request, settings)
    document = LegalDocument.objects.get(slug="privacy", language="es", active=True)
    with transaction.atomic():
        _, digest = published_policy(document.pk, "es")
    value = draft()
    for item in value["access"].values():
        item.update(status="reviewed", source="reviewer", text="Synthetic reviewed information")
    row = save(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        document.version,
        "Prepare synthetic draft for concurrent independent review",
        value,
        policy_document_id=document.pk,
        expected_policy_digest=digest,
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_copy_information",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    reason = "Independently approve synthetic information after observed wait"
    record(reviewer, case.pk, row.pk, uuid4(), case.version, "inspect", reason)
    key, pids = uuid4(), Queue()

    def attempt(action_key):
        connections.close_all()
        try:
            user = User.objects.get(pk=reviewer.pk)
            assert user.has_perm("safety.review_copy_information")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                result, _ = record(
                    user, case.pk, row.pk, action_key, case.version, "review", reason, "approved"
                )
                return "admitted", result.pk
            except (PermissionDenied, ValidationError):
                return "denied", None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            futures = [
                pool.submit(attempt, action_key)
                for action_key in [key, uuid4() if change == "conflict" else key]
            ]
            workers = [pids.get(timeout=5) for _ in range(2)]
            assert len(set(workers + [holder])) == 3
            for pid in workers:
                observe_blocked(pid, holder)
            assert not any(future.done() for future in futures)
            if change == "permission":
                reviewer.user_permissions.clear()
            elif change == "proof":
                case.proofs.update(status="failed")
            elif change in {"session", "mfa"}:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=reviewer.pk).update(**{field: getattr(reviewer, field) + 1})
            elif change == "source":
                person.listing.revisions.all().update(
                    description="Changed source during observed wait"
                )
            elif change == "policy":
                LegalDocument.objects.filter(pk=document.pk).update(
                    body="Changed policy during wait"
                )
        results = [future.result(timeout=15) for future in futures]
    decisions = RightsCopyInformationReview.objects.filter(information=row)
    actions = RightsAction.objects.filter(request=case, operation="copy_info_review")
    if change == "replay":
        assert all(result[0] == "admitted" for result in results)
        assert results[0][1] == results[1][1]
        assert decisions.count() == actions.count() == 1
    elif change == "conflict":
        assert sorted(result[0] for result in results) == ["admitted", "denied"]
        assert decisions.count() == actions.count() == 1
    else:
        assert all(result[0] == "denied" for result in results)
        assert not decisions.exists() and not actions.exists()
    case.refresh_from_db()
    assert case.version == row.action.expected_version and case.status == "reviewing"
