from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from test_account_copy_races import prepared_account
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability import assessment
from test_rights_responses import ready
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import RightsAction, RightsPortabilitySelectionReview, RightsRequest
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability import save_assessment
from apps.safety.rights_portability_review import record as assessment_record
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_review import record
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("granular", [False, True], ids=["plain", "mixed_fields"])
@pytest.mark.parametrize(
    "change", ["replay", "conflict", "permission", "proof", "session", "mfa", "source"]
)
def test_selection_decision_rechecks_after_observed_case_wait(
    request, settings, monkeypatch, change, account_only, granular
):
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
    if granular:
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
    evidence = {dataset: {ref: {paths[0]: eligible_facts}}} if granular else None
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
    if granular:
        assert projection["field_evidence"] == evidence
    key, pids = uuid4(), Queue()

    def attempt(action_key):
        connections.close_all()
        try:
            user = User.objects.get(pk=reviewer.pk)
            assert user.has_perm("safety.review_portability")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                result, _ = record(
                    user, case.pk, case.version, row.pk, action_key, reason, "review", "approved"
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
                if account_only:
                    User.objects.filter(pk=subject.pk).update(
                        first_name="Changed source during observed wait"
                    )
                else:
                    person.listing.revisions.all().update(
                        description="Changed source during observed wait"
                    )
        results = [future.result(timeout=15) for future in futures]
    decisions = RightsPortabilitySelectionReview.objects.filter(selection=row)
    actions = RightsAction.objects.filter(request=case, operation="selection_review")
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

    if change == "replay":
        from test_rights_exports import url

        from apps.safety.rights_portability_export import generate

        version = case.version
        key = uuid4()
        decision = decisions.get()
        export = generate(author, case.pk, version, row.pk, decision.pk, key, reason)
        assert generate(author, case.pk, version, row.pk, decision.pk, key, reason).pk == export.pk
        response = public.post(url(receipt, export), {"key": uuid4()})
        assert response.status_code == 200
        assert response.json()["datasets"][dataset] == projection["datasets"][dataset]
        assert "field_evidence" not in response.json()

    if change in {"replay", "conflict"}:
        from apps.safety.erasure_inventory import source_manifest

        with transaction.atomic():
            inventory_case = RightsRequest.objects.create(
                submission_key=uuid4(),
                kind="erase",
                account_subject=subject if account_only else None,
                person=person if not account_only else None,
                received_at=case.received_at,
                initial_due_at=case.initial_due_at,
                receipt_expires_at=case.receipt_expires_at,
            )
            manifest = source_manifest(person, inventory_case)
            items = {item["model"]: item for item in manifest["entries"]}
            for model in [
                "RightsPortabilitySelection",
                "RightsPortabilitySelectionRead",
                "RightsPortabilitySelectionReview",
            ]:
                assert items["safety." + model]["count"] == 1
            assert row.encrypted_selection not in str(manifest)
            if change == "replay":
                assert items["safety.RightsExportPortabilityBinding"]["count"] == 1
                assert export.encrypted_payload not in str(manifest)
                before_digest = items["safety.RightsExportPortabilityBinding"]["state_digest"]
                from apps.safety.models import RightsExportPortabilityBinding

                RightsExportPortabilityBinding.objects.filter(export=export).update(
                    decision_digest="0" * 64
                )
                changed = source_manifest(person, inventory_case)
                changed_items = {item["model"]: item for item in changed["entries"]}
                assert (
                    changed_items["safety.RightsExportPortabilityBinding"]["state_digest"]
                    != before_digest
                )
