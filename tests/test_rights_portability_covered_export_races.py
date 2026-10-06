"""Covered export authority after an observed PostgreSQL wait, synthetic data."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from django.utils import timezone
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_portability_coverage_use import prepared_covered_selection

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsAction,
    RightsExport,
    RightsExportDownload,
    RightsPortabilityCoverage,
    RightsRequest,
)
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_inspection import inspect_page
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_review import record
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_export import generate
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


def approved_coverage(request, settings, monkeypatch, account_only):
    case, author, selection, selected_review, profile, subject, receipt = (
        prepared_covered_selection(request, settings, monkeypatch, account_only)
    )
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    chosen = unseal(selection.encrypted_selection)
    facts = {
        "status": "excluded",
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic excluded fields for observed covered export race",
        "evidence": "Synthetic coverage facts; no production legal finding",
    }
    omissions = {name: {} for name in SECTIONS}
    for dataset, reader in SECTIONS.items():
        for index, row in enumerate(reader(source)):
            ref = row_reference(dataset, index, row)
            selected = next(
                (
                    set(item["fields"])
                    for item in chosen["selection"][dataset]
                    if item["row"] == ref
                ),
                set(),
            )
            if any(item["path"] not in selected for item in scalar_fields(row)):
                omissions[dataset][ref] = {"all": facts}
    included = {item["photo"] for item in chosen.get("images", [])}
    image_omissions = {
        image["photo"]: facts
        for revision in source["revisions"]
        for image in revision["images"]
        if image["photo"] not in included
    }
    reason = "Approve synthetic coverage before observed export authority race"
    coverage = save_coverage(
        author,
        case.pk,
        case.version,
        selected_review.pk,
        uuid4(),
        0,
        reason,
        omissions,
        image_omissions,
    )
    reviewer = User.objects.get(pk=selected_review.action.actor_id)
    for dataset, index, page, binary in required_pages(source):
        inspect_page(
            reviewer,
            case.pk,
            case.version,
            coverage.pk,
            uuid4(),
            reason,
            dataset,
            index,
            page,
            binary=binary,
        )
    decision = record(reviewer, case.pk, case.version, coverage.pk, uuid4(), reason, "approved")
    return (
        case,
        author,
        selection,
        selected_review,
        coverage,
        decision,
        reviewer,
        profile,
        subject,
        receipt,
    )


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("operation", ["generate", "download"])
@pytest.mark.parametrize(
    "change",
    [
        "replay",
        "proof",
        "source",
        "coverage",
        "reviewer_permission",
        "reviewer_session",
        "channel",
        "expiry",
    ],
)
def test_covered_export_rechecks_after_observed_wait(
    request, settings, monkeypatch, account_only, operation, change
):
    (
        case,
        author,
        selection,
        selected_review,
        coverage,
        decision,
        reviewer,
        profile,
        subject,
        receipt,
    ) = approved_coverage(request, settings, monkeypatch, account_only)
    version, deadline = case.version, case.initial_due_at
    reason = "Generate full approved synthetic portability during observed wait"
    export = None
    if operation == "download":
        export = generate(
            author,
            case.pk,
            version,
            selection.pk,
            selected_review.pk,
            uuid4(),
            reason,
            coverage_review_id=decision.pk,
        )
        case.refresh_from_db()
    baseline_actions = RightsAction.objects.filter(request=case).count()
    baseline_exports = RightsExport.objects.filter(action__request=case).count()
    key, pids = uuid4(), Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=author.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            if operation == "download":
                return Client().post(url(receipt, export), {"key": key}).status_code
            try:
                return generate(
                    actor,
                    case.pk,
                    version,
                    selection.pk,
                    selected_review.pk,
                    key,
                    reason,
                    coverage_review_id=decision.pk,
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
            if change == "proof":
                case.proofs.update(status="failed")
            elif change == "source":
                if account_only:
                    User.objects.filter(pk=subject.pk).update(
                        first_name="Changed synthetic source during wait"
                    )
                else:
                    profile.listing.revisions.update(
                        description="Changed synthetic source during wait"
                    )
            elif change == "coverage":
                RightsPortabilityCoverage.objects.filter(pk=coverage.pk).update(
                    encrypted_coverage="tampered"
                )
            elif change == "reviewer_permission":
                reviewer.user_permissions.clear()
            elif change == "reviewer_session":
                User.objects.filter(pk=reviewer.pk).update(
                    session_version=reviewer.session_version + 1
                )
            elif change == "channel":
                RightsRequest.objects.filter(pk=case.pk).update(receipt_digest="0" * 64)
            elif change == "expiry":
                RightsPortabilityCoverage.objects.filter(pk=coverage.pk).update(
                    expires_at=timezone.now() - timedelta(seconds=1)
                )
        results = [future.result(timeout=30) for future in futures]
    case.refresh_from_db()
    if operation == "generate":
        if change == "replay":
            assert results[0] is not None and results[0] == results[1]
            assert RightsExport.objects.filter(action__request=case).count() == baseline_exports + 1
            assert RightsAction.objects.filter(request=case).count() == baseline_actions + 4
            assert case.version == version + 1
        else:
            assert results == [None, None]
            assert RightsExport.objects.filter(action__request=case).count() == baseline_exports
            assert RightsAction.objects.filter(request=case).count() == baseline_actions
            assert case.version == version
    else:
        assert results == ([200, 200] if change == "replay" else [404, 404])
        assert RightsExportDownload.objects.filter(export=export).count() == (
            1 if change == "replay" else 0
        )
        assert RightsAction.objects.filter(request=case).count() == baseline_actions
        assert case.version == version + 1
    assert case.status == "reviewing" and case.initial_due_at == deadline
