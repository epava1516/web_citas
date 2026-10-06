"""Observed PostgreSQL wait: independent coverage reads recheck authority."""

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
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsAction,
    RightsPortabilityCoverage,
    RightsPortabilityCoverageRead,
    RightsPortabilityCoverageReview,
    RightsRequest,
)
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_inspection import inspect_page
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_review import record as review_coverage
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_coverage_use import consume_approved_coverage
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    ("operation", "change"),
    [
        (operation, change)
        for operation in ["inspect", "review", "approve", "use"]
        for change in [
            "replay",
            "permission",
            "proof",
            "session",
            "mfa",
            "source",
            "ciphertext",
            "expiry",
        ]
    ]
    + [("use", change) for change in ["author_permission", "author_session", "author_mfa"]],
)
def test_independent_coverage_read_rechecks_after_observed_wait(
    request, settings, monkeypatch, change, operation
):
    case, author, selection, decision, _, subject, _ = prepared_selection(
        request, settings, monkeypatch, True
    )
    reason = "Inspect synthetic coverage during observed PostgreSQL wait"
    omissions = {name: {} for name in SECTIONS}
    if operation in {"approve", "use"}:
        with transaction.atomic():
            locked, person, listing = reviewer_case(author, case.pk)
            source = source_copy(person, listing, locked)
        chosen = unseal(selection.encrypted_selection)["selection"]
        facts = {
            "status": "excluded",
            "basis": "other",
            "origin": "inferred",
            "automated": True,
            "subject_related": True,
            "third_party_reviewed": True,
            "reason": "Synthetic fixture exclusion without production factual claim",
            "evidence": "Synthetic fixture exclusion before observed approval race",
        }
        for dataset, reader in SECTIONS.items():
            for index, item in enumerate(reader(source)):
                reference = row_reference(dataset, index, item)
                selected = next(
                    (
                        set(entry["fields"])
                        for entry in chosen[dataset]
                        if entry["row"] == reference
                    ),
                    set(),
                )
                if any(field["path"] not in selected for field in scalar_fields(item)):
                    omissions[dataset][reference] = {"all": facts}
    row = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        uuid4(),
        0,
        reason,
        omissions,
        {},
        allow_partial=True,
    )
    reviewer = User.objects.get(pk=decision.action.actor_id)
    if operation in {"review", "approve", "use"}:
        with transaction.atomic():
            locked, person, listing = reviewer_case(reviewer, case.pk)
            source = source_copy(person, listing, locked)
        for dataset, index, page, binary in required_pages(source):
            inspect_page(
                reviewer,
                case.pk,
                case.version,
                row.pk,
                uuid4(),
                reason,
                dataset,
                index,
                page,
                binary=binary,
            )
    approval = (
        review_coverage(reviewer, case.pk, case.version, row.pk, uuid4(), reason, "approved")
        if operation == "use"
        else None
    )
    reads_before = RightsPortabilityCoverageRead.objects.filter(coverage=row).count()
    key, pids = uuid4(), Queue()
    baseline = RightsAction.objects.filter(request=case).count()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=author.pk if operation == "use" else reviewer.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                if operation == "use":
                    return consume_approved_coverage(
                        actor, case.pk, case.version, approval.pk, key, reason
                    )[0].pk
                if operation in {"review", "approve"}:
                    return review_coverage(
                        actor,
                        case.pk,
                        case.version,
                        row.pk,
                        key,
                        reason,
                        "approved" if operation == "approve" else "rejected",
                    ).pk
                action, _ = inspect_page(
                    actor, case.pk, case.version, row.pk, key, reason, "subject_account"
                )
                return action.pk
            except (ValidationError, PermissionDenied):
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
            assert not any(future.done() for future in futures)
            if change == "author_permission":
                author.user_permissions.clear()
            elif change in {"author_session", "author_mfa"}:
                field = "session_version" if change == "author_session" else "mfa_version"
                User.objects.filter(pk=author.pk).update(**{field: getattr(author, field) + 1})
            elif change == "permission":
                reviewer.user_permissions.clear()
            elif change == "proof":
                case.proofs.update(status="failed")
            elif change in {"session", "mfa"}:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=reviewer.pk).update(**{field: getattr(reviewer, field) + 1})
            elif change == "source":
                User.objects.filter(pk=subject.pk).update(
                    first_name="Changed synthetic source during wait"
                )
            elif change == "ciphertext":
                RightsPortabilityCoverage.objects.filter(pk=row.pk).update(
                    encrypted_coverage="tampered"
                )
            elif change == "expiry":
                RightsPortabilityCoverage.objects.filter(pk=row.pk).update(
                    expires_at=timezone.now() - timedelta(seconds=1)
                )
        results = [future.result(timeout=30) for future in futures]
    if change == "replay":
        assert results[0] is not None and results[0] == results[1]
        assert RightsPortabilityCoverageRead.objects.filter(
            coverage=row
        ).count() == reads_before + (operation == "inspect")
        assert RightsAction.objects.filter(request=case).count() == baseline + (
            2 if operation in {"inspect", "use"} else 1
        )
        if operation in {"review", "approve"}:
            assert RightsPortabilityCoverageReview.objects.filter(coverage=row).count() == 1
    else:
        assert results == [None, None]
        assert RightsPortabilityCoverageRead.objects.filter(coverage=row).count() == reads_before
        assert RightsPortabilityCoverageReview.objects.filter(coverage=row).count() == (
            1 if operation == "use" else 0
        )
        assert RightsAction.objects.filter(request=case).count() == baseline
    case.refresh_from_db()
    assert case.version == row.action.expected_version and case.status == "reviewing"
