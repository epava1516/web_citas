"""Final draft approval after a real observed PostgreSQL wait, synthetic account."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_covered_export_races import approved_coverage
from test_rights_portability_response_draft import REASON, TEXT, operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import (
    RightsAction,
    RightsPortabilityResponseDraft,
    RightsPortabilityResponseReview,
    RightsRequest,
)
from apps.safety.rights_portability_export import generate
from apps.safety.rights_portability_response_draft import prepare
from apps.safety.rights_portability_response_review import inspect, record
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def ready_final_draft(
    request, settings, monkeypatch, *, with_receipt=False, account_only=True, binary=False
):
    case, author, selection, selected, _, decision, reviewer, _, subject, receipt = (
        approved_coverage(request, settings, monkeypatch, account_only, binary=binary)
    )
    respond = Permission.objects.get(codename="respond_rights_request")
    author.user_permissions.add(respond)
    reviewer.user_permissions.add(respond, Permission.objects.get(codename="verify_rights_scope"))
    author, reviewer = User.objects.get(pk=author.pk), User.objects.get(pk=reviewer.pk)
    export = generate(
        author,
        case.pk,
        case.version,
        selection.pk,
        selected.pk,
        uuid4(),
        REASON,
        coverage_review_id=decision.pk,
    )
    case.refresh_from_db()
    staff, other = operator(author), operator(reviewer)
    read(staff, case)
    proof = start(author, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    read(other, case)
    receive_event(reviewer, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(staff, case)
    read(other, case)
    draft = prepare(
        author, case.pk, case.version, case.response_version, export.pk, uuid4(), REASON, TEXT, True
    )
    read_key = uuid4()
    inspect(reviewer, case.pk, case.version, draft.pk, read_key, REASON)
    result = (case, author, reviewer, subject, proof, draft, RightsAction.objects.get(key=read_key))
    return (*result, receipt) if with_receipt else result


@pytest.mark.parametrize("operation", ["inspect", "review"])
@pytest.mark.parametrize(
    "change",
    [
        "replay",
        "reviewer_permission",
        "reviewer_session",
        "reviewer_mfa",
        "author_permission",
        "author_session",
        "proof",
        "source",
        "ciphertext",
        "expiry",
    ],
)
def test_final_approval_rechecks_authority_after_observed_wait(
    request, settings, monkeypatch, change, operation
):
    case, author, reviewer, subject, proof, draft, read_action = ready_final_draft(
        request, settings, monkeypatch
    )
    original = case.version, case.response_version, case.status, case.initial_due_at
    baseline = RightsAction.objects.filter(request=case).count()
    key, pids = uuid4(), Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=reviewer.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                if operation == "inspect":
                    return inspect(actor, case.pk, case.version, draft.pk, key, REASON)[0].pk
                return record(
                    actor, case.pk, case.version, draft.pk, read_action.pk, key, REASON, "approved"
                ).pk
            except (PermissionDenied, ValidationError):
                return None
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
            if change == "reviewer_permission":
                reviewer.user_permissions.clear()
            elif change == "reviewer_session":
                User.objects.filter(pk=reviewer.pk).update(
                    session_version=reviewer.session_version + 1
                )
            elif change == "reviewer_mfa":
                User.objects.filter(pk=reviewer.pk).update(mfa_version=reviewer.mfa_version + 1)
            elif change == "author_permission":
                author.user_permissions.clear()
            elif change == "author_session":
                User.objects.filter(pk=author.pk).update(session_version=author.session_version + 1)
            elif change == "proof":
                case.proofs.filter(pk=proof.pk).update(status="failed")
            elif change == "source":
                User.objects.filter(pk=subject.pk).update(
                    first_name="Changed synthetic source during wait"
                )
            elif change == "ciphertext":
                RightsPortabilityResponseDraft.objects.filter(pk=draft.pk).update(
                    encrypted_response="damaged"
                )
            elif change == "expiry":
                RightsPortabilityResponseDraft.objects.filter(pk=draft.pk).update(
                    expires_at=timezone.now() - timedelta(seconds=1)
                )
        results = [future.result(timeout=30) for future in futures]
    if change == "replay":
        assert results[0] is not None and results[0] == results[1]
        assert RightsPortabilityResponseReview.objects.filter(draft=draft).count() == (
            1 if operation == "review" else 0
        )
        assert RightsAction.objects.filter(request=case).count() == baseline + 1
    else:
        assert results == [None, None]
        assert not RightsPortabilityResponseReview.objects.filter(draft=draft).exists()
        assert RightsAction.objects.filter(request=case).count() == baseline
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original
