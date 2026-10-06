"""Atomic final issuance under observed PostgreSQL contention, synthetic accounts."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_response_draft import REASON
from test_rights_portability_response_races import ready_final_draft

from apps.core.models import User
from apps.safety.models import (
    RightsAction,
    RightsNotice,
    RightsPortabilityClosure,
    RightsPortabilityResponseDraft,
    RightsPortabilityResponseReview,
    RightsRequest,
    RightsResponse,
)
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_response_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "change",
    [
        "replay",
        "author_permission",
        "author_session",
        "author_mfa",
        "reviewer_permission",
        "reviewer_session",
        "reviewer_mfa",
        "proof",
        "source",
        "ciphertext",
        "expiry",
        "decision",
    ],
)
def test_closure_revalidates_after_observed_lock_wait(request, settings, monkeypatch, change):
    case, author, reviewer, subject, proof, draft, read_action = ready_final_draft(
        request, settings, monkeypatch
    )
    decision = record(
        reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, "approved"
    )
    original = case.version, case.response_version, case.status, case.initial_due_at
    baseline = RightsAction.objects.filter(request=case).count()
    key, pids = uuid4(), Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=author.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                return close(actor, case.pk, original[0], original[1], decision.pk, key, REASON).pk
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
            if change.endswith("permission"):
                (author if change.startswith("author") else reviewer).user_permissions.clear()
            elif change.endswith("session") or change.endswith("mfa"):
                actor = author if change.startswith("author") else reviewer
                field = "session_version" if change.endswith("session") else "mfa_version"
                User.objects.filter(pk=actor.pk).update(**{field: getattr(actor, field) + 1})
            elif change == "proof":
                case.proofs.filter(pk=proof.pk).update(status="failed")
            elif change == "source":
                User.objects.filter(pk=subject.pk).update(first_name="Changed synthetic source")
            elif change == "ciphertext":
                RightsPortabilityResponseDraft.objects.filter(pk=draft.pk).update(
                    encrypted_response="damaged"
                )
            elif change == "expiry":
                RightsPortabilityResponseDraft.objects.filter(pk=draft.pk).update(
                    expires_at=timezone.now() - timedelta(seconds=1)
                )
            elif change == "decision":
                RightsPortabilityResponseReview.objects.filter(pk=decision.pk).update(
                    text_digest="0" * 64
                )
        results = [future.result(timeout=30) for future in futures]
    case.refresh_from_db()
    counts = [
        model.objects.count() for model in (RightsResponse, RightsNotice, RightsPortabilityClosure)
    ]
    if change == "replay":
        assert results[0] is not None and results[0] == results[1]
        assert counts == [1, 1, 1]
        assert RightsAction.objects.filter(request=case).count() == baseline + 1
        assert (case.version, case.response_version, case.status, case.initial_due_at) == (
            original[0] + 1,
            original[1] + 1,
            "resolved",
            original[3],
        )
    else:
        assert results == [None, None]
        assert counts == [0, 0, 0]
        assert RightsAction.objects.filter(request=case).count() == baseline
        assert (case.version, case.response_version, case.status, case.initial_due_at) == original
