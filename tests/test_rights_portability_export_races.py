from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability import assessment
from test_rights_responses import ready
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import (
    RightsAction,
    RightsExport,
    RightsExportDownload,
    RightsExportPortabilityBinding,
    RightsRequest,
)
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability import save_assessment
from apps.safety.rights_portability_review import record as assessment_record
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_review import record
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = pytest.mark.django_db(transaction=True)


def prepared_selection(request, settings, monkeypatch, account_only):
    if account_only:
        case, author, _, subject, public, receipt = prepared_account(
            request, settings, monkeypatch, "portability"
        )
        person = None
    else:
        case, author, _, public, receipt, person = ready(
            request, settings, monkeypatch, "portability"
        )
        subject = None
    value = assessment()
    for item in value.values():
        item.update(
            status="eligible",
            basis="contract",
            origin="provided",
            automated=True,
            subject_related=True,
            third_party_reviewed=True,
            reason="Synthetic portability eligibility for observed race",
            evidence="Synthetic documented provenance and processing conditions",
        )
    dataset = "subject_account" if account_only else "profile"
    eligible_facts = dict(value[dataset])
    value[dataset].update(
        status="granular",
        origin="mixed",
        basis="unknown",
        subject_related=None,
        third_party_reviewed=None,
    )
    row = save_assessment(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Prepare synthetic portability assessment before observed race",
        value,
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_portability",
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
    assessment_record(reviewer, case.pk, row.pk, uuid4(), case.version, "inspect", reason)
    approved, _ = assessment_record(
        reviewer, case.pk, row.pk, uuid4(), case.version, "review", reason, "approved"
    )
    with transaction.atomic():
        locked, profile, listing = reviewer_case(author, case.pk)
        source = source_copy(profile, listing, locked)
    paths = ["/email"] if account_only else ["/alias"]
    selectors = {name: [] for name in value}
    ref = row_reference(dataset, 0, source[dataset])
    selectors[dataset] = [{"row": ref, "fields": paths}]
    evidence = {dataset: {ref: {paths[0]: eligible_facts}}}
    row = save_selection(
        author,
        case.pk,
        case.version,
        approved.pk,
        uuid4(),
        0,
        reason,
        selectors,
        field_evidence=evidence,
    )
    inspected, projection = record(reviewer, case.pk, case.version, row.pk, uuid4(), reason)
    assert len(projection["datasets"][dataset]) == 1
    assert set(projection["datasets"][dataset][0]["fields"]) == set(paths)
    assert projection["field_evidence"] == evidence
    decision, _ = record(
        reviewer, case.pk, case.version, row.pk, uuid4(), reason, "review", "approved"
    )
    return case, author, row, decision, person, subject, receipt


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize(
    "operation,change",
    [
        ("generate", change)
        for change in [
            "replay",
            "conflict",
            "proof",
            "source",
            "binding",
            "permission",
            "session",
            "mfa",
            "scope",
            "expiry",
            "selection_expiry",
            "channel",
        ]
    ]
    + [
        ("download", change)
        for change in [
            "replay",
            "proof",
            "source",
            "binding",
            "scope",
            "expiry",
            "selection_expiry",
            "channel",
        ]
    ],
)
def test_portability_export_rechecks_after_observed_wait(
    request, settings, monkeypatch, account_only, operation, change
):
    from test_rights_exports import url

    from apps.safety.rights_portability_export import generate

    case, author, selection, decision, person, subject, receipt = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    version = case.version
    reason = "Generate independently approved synthetic portable data"
    export = None
    if operation == "download":
        export = generate(author, case.pk, version, selection.pk, decision.pk, uuid4(), reason)
        case.refresh_from_db()
    baseline_actions = RightsAction.objects.filter(request=case).count()
    baseline_exports = RightsExport.objects.filter(action__request=case).count()
    key, pids = uuid4(), Queue()

    def attempt(action_key):
        connections.close_all()
        try:
            actor = User.objects.get(pk=author.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            if operation == "download":
                response = Client().post(url(receipt, export), {"key": action_key})
                return response.status_code
            try:
                result = generate(
                    actor, case.pk, version, selection.pk, decision.pk, action_key, reason
                )
                return result.pk
            except (ValidationError, PermissionDenied):
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            if change == "scope" and not account_only:
                # Profile operations lock Person before RightsRequest. The mutator
                # must follow the same order to avoid introducing a test deadlock.
                type(person).objects.select_for_update().get(pk=person.pk)
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
            if change == "proof":
                case.proofs.update(status="failed")
            elif change == "expiry":
                case.proofs.update(expires_at=timezone.now() - timedelta(seconds=1))
            elif change == "selection_expiry":
                type(selection).objects.filter(pk=selection.pk).update(
                    expires_at=timezone.now() - timedelta(seconds=1)
                )
            elif change == "channel":
                RightsRequest.objects.filter(pk=case.pk).update(receipt_digest="0" * 64)
            elif change == "scope":
                if account_only:
                    RightsRequest.objects.filter(pk=case.pk).update(account_subject=author)
                else:
                    type(person).objects.filter(pk=person.pk).update(
                        rights_version=person.rights_version + 1
                    )
            elif change == "source":
                if account_only:
                    User.objects.filter(pk=subject.pk).update(
                        first_name="Changed during observed wait"
                    )
                else:
                    person.listing.revisions.update(description="Changed during observed wait")
            elif change == "binding":
                if operation == "download":
                    RightsExportPortabilityBinding.objects.filter(export=export).update(
                        decision_digest="0" * 64
                    )
                else:
                    decision.action.payload_digest = "0" * 64
                    decision.action.save(update_fields=["payload_digest"])
            elif change == "permission":
                author.user_permissions.clear()
            elif change in {"session", "mfa"}:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=author.pk).update(**{field: getattr(author, field) + 1})
        results = [future.result(timeout=20) for future in futures]
    case.refresh_from_db()
    if operation == "generate":
        if change in {"replay", "conflict"}:
            if change == "replay":
                assert results[0] is not None and results[0] == results[1]
            else:
                assert sum(result is not None for result in results) == 1
            assert RightsExport.objects.filter(action__request=case).count() == baseline_exports + 1
            assert (
                RightsAction.objects.filter(request=case, operation="portability_export").count()
                == 1
            )
            assert RightsAction.objects.filter(request=case).count() == baseline_actions + 2
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
        assert case.version == version + 1
