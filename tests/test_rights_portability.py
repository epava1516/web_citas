from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.rights_portability import DATASETS, checked_assessment


def assessment():
    return {
        name: {
            "status": "pending",
            "basis": "unknown",
            "origin": "unknown",
            "automated": None,
            "subject_related": None,
            "third_party_reviewed": None,
            "reason": "",
            "evidence": "",
        }
        for name in DATASETS
    }


def test_unknown_assessment_is_pending_and_returns_independent_copy():
    value = assessment()
    result = checked_assessment(value)
    assert result == value and result is not value
    result["profile"]["reason"] = "Changed copy"
    assert value["profile"]["reason"] == ""


@pytest.mark.parametrize(
    "field,invalid",
    [
        ("basis", "legitimate_interest"),
        ("origin", "inferred"),
        ("origin", "mixed"),
        ("automated", None),
        ("automated", 1),
        ("subject_related", False),
        ("third_party_reviewed", None),
        ("basis", []),
        ("reason", ""),
    ],
)
def test_eligibility_requires_verified_conditions(field, invalid):
    value = assessment()
    value["favorites"].update(
        status="eligible",
        basis="contract",
        origin="observed",
        automated=True,
        subject_related=True,
        third_party_reviewed=True,
        reason="Synthetic reviewer verified every condition",
        evidence="Synthetic documented source and processing basis",
    )
    assert checked_assessment(value)["favorites"]["status"] == "eligible"
    damaged = deepcopy(value)
    damaged["favorites"][field] = invalid
    with pytest.raises(ValidationError):
        checked_assessment(damaged)


def test_missing_dataset_and_unexplained_exclusion_are_rejected():
    value = assessment()
    value.pop("profile")
    with pytest.raises(ValidationError):
        checked_assessment(value)
    value = assessment()
    value["profile"]["status"] = "excluded"
    with pytest.raises(ValidationError):
        checked_assessment(value)


@pytest.mark.parametrize("origin", ["unknown", "mixed", "provided"])
def test_exclusion_cannot_replace_unresolved_or_eligible_conditions(origin):
    value = assessment()
    value["profile"].update(
        status="excluded",
        origin=origin,
        reason="Synthetic explanation without a resolved exclusion ground",
        evidence="Synthetic evidence with unresolved processing conditions",
    )
    with pytest.raises(ValidationError):
        checked_assessment(value)
    value["profile"]["automated"] = False
    assert checked_assessment(value)["profile"]["status"] == "excluded"


@pytest.mark.parametrize(
    "field,ground",
    [
        ("basis", "legal_obligation"),
        ("basis", "legitimate_interest"),
        ("origin", "inferred"),
        ("origin", "third_party"),
        ("subject_related", False),
    ],
)
def test_exclusion_requires_an_explicit_negative_condition(field, ground):
    value = assessment()
    value["profile"].update(
        status="excluded",
        reason="Synthetic independently documented exclusion ground",
        evidence="Synthetic provenance evidence supporting this decision",
    )
    value["profile"][field] = ground
    assert checked_assessment(value)["profile"]["status"] == "excluded"


@pytest.mark.django_db(transaction=True)
def test_portability_assessment_persists_encrypted_replays_and_rejects_source_change(
    request, settings, monkeypatch
):
    from uuid import uuid4

    from test_account_copy_races import prepared_account

    from apps.core.models import User
    from apps.safety.crypto import unseal
    from apps.safety.models import RightsAction, RightsExport, RightsPortabilityAssessment
    from apps.safety.rights_portability import save_assessment

    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    key = uuid4()
    reason = "Prepare synthetic pending dataset eligibility assessment"
    original = (case.version, case.status, case.scope_status)
    value = assessment()
    row = save_assessment(actor, case.pk, case.version, key, 0, reason, value)
    assert unseal(row.encrypted_assessment) == value
    assert row.encrypted_assessment != str(value)
    assert save_assessment(actor, case.pk, case.version, key, 0, reason, value).pk == row.pk
    assert RightsPortabilityAssessment.objects.count() == 1
    assert RightsAction.objects.filter(operation="portability_save").count() == 1
    assert not RightsExport.objects.exists()
    case.refresh_from_db()
    assert (case.version, case.status, case.scope_status) == original
    User.objects.filter(pk=subject.pk).update(first_name="Changed synthetic source")
    with pytest.raises(ValidationError):
        save_assessment(actor, case.pk, case.version, key, 0, reason, value)
    assert RightsPortabilityAssessment.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_portability_form_records_pending_draft_without_disclosing_it_on_get(
    request, settings, monkeypatch
):
    from uuid import uuid4

    from django.urls import reverse
    from test_account_copy_races import prepared_account

    from apps.safety.models import RightsPortabilityAssessment

    case, actor, staff, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    path = reverse("rights_portability_prepare", kwargs={"case_id": case.pk})
    response = staff.get(path)
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    values = dict(response.context["form"].initial)
    private_reason = "PRIVATE_SYNTHETIC_PORTABILITY_REASON"
    values.update(reason=private_reason)
    values.update(
        {
            "datasets-TOTAL_FORMS": "9",
            "datasets-INITIAL_FORMS": "9",
            "datasets-MIN_NUM_FORMS": "9",
            "datasets-MAX_NUM_FORMS": "9",
        }
    )
    for index, name in enumerate(DATASETS):
        row = assessment()[name]
        values[f"datasets-{index}-dataset"] = name
        for field, value in row.items():
            values[f"datasets-{index}-{field}"] = "unknown" if value is None else value
    assert staff.post(path, values).status_code == 200
    assert staff.post(path, values).status_code == 200
    assert RightsPortabilityAssessment.objects.count() == 1
    assert private_reason.encode() not in staff.get(path).content
    duplicate = values | {"key": uuid4(), "datasets-1-dataset": DATASETS[0]}
    assert staff.post(path, duplicate).status_code == 409
    assert RightsPortabilityAssessment.objects.count() == 1
    actor.user_permissions.clear()
    assert staff.get(path).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_saved_portability_inspection_is_audited_and_corruption_rolls_back(
    request, settings, monkeypatch
):
    from uuid import uuid4

    from test_account_copy_races import prepared_account

    from apps.safety.models import RightsAction
    from apps.safety.rights_portability import inspect_assessment, save_assessment

    case, actor, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    value = assessment()
    row = save_assessment(
        actor,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Store synthetic assessment before audited consultation",
        value,
    )
    purpose = "Inspect saved synthetic assessment with audit evidence"
    key = uuid4()
    loaded, body = inspect_assessment(actor, case.pk, case.version, row.pk, key, purpose)
    assert loaded.pk == row.pk and body == value
    assert inspect_assessment(actor, case.pk, case.version, row.pk, key, purpose)[1] == value
    assert RightsAction.objects.filter(operation="portability_read").count() == 1
    type(row).objects.filter(pk=row.pk).update(original_mfa_version=row.original_mfa_version + 1)
    with pytest.raises(ValidationError, match="evidence changed"):
        inspect_assessment(actor, case.pk, case.version, row.pk, uuid4(), purpose)
    assert RightsAction.objects.filter(operation="portability_read").count() == 1
    type(row).objects.filter(pk=row.pk).update(original_mfa_version=row.original_mfa_version)
    type(row).objects.filter(pk=row.pk).update(
        encrypted_assessment="Corrupted synthetic ciphertext"
    )
    with pytest.raises(ValidationError):
        inspect_assessment(actor, case.pk, case.version, row.pk, uuid4(), purpose)
    assert RightsAction.objects.filter(operation="portability_read").count() == 1


@pytest.mark.django_db(transaction=True)
def test_saved_assessment_http_audit_and_get_hides_private_evidence(request, settings, monkeypatch):
    from uuid import uuid4

    from django.urls import reverse
    from test_account_copy_races import prepared_account

    from apps.safety.models import RightsAction
    from apps.safety.rights_portability import save_assessment

    case, actor, staff, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    value = assessment()
    private_evidence = "PRIVATE_SYNTHETIC_ASSESSMENT_EVIDENCE"
    value["profile"]["evidence"] = private_evidence
    row = save_assessment(
        actor,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Save synthetic assessment before HTTP audit",
        value,
    )
    path = reverse("rights_portability_prepare", kwargs={"case_id": case.pk})
    assert private_evidence.encode() not in staff.get(path).content
    data = {
        "operation": "inspect",
        "key": uuid4(),
        "case_version": case.version,
        "assessment_id": row.pk,
        "purpose": "Inspect synthetic saved portability evidence",
    }
    response = staff.post(path, data)
    assert response.status_code == 200 and private_evidence.encode() in response.content
    assert "no-store" in response["Cache-Control"]
    assert staff.post(path, data).status_code == 200
    assert RightsAction.objects.filter(operation="portability_read").count() == 1
    assert private_evidence.encode() not in staff.get(path).content


@pytest.mark.django_db(transaction=True)
def test_expired_assessment_purge_preserves_audit_and_blocks_read(request, settings, monkeypatch):
    from datetime import timedelta
    from uuid import uuid4

    from django.utils import timezone
    from test_account_copy_races import prepared_account

    from apps.safety.models import RightsAction
    from apps.safety.rights_portability import inspect_assessment, save_assessment
    from apps.safety.tasks import purge_expired_portability_assessments

    case, actor, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    row = save_assessment(
        actor,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Store synthetic assessment before expiry test",
        assessment(),
    )
    assert purge_expired_portability_assessments() == 0
    type(row).objects.filter(pk=row.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert purge_expired_portability_assessments() == 1
    assert purge_expired_portability_assessments() == 0
    row.refresh_from_db()
    assert row.encrypted_assessment == "" and row.purged_at
    assert RightsAction.objects.filter(pk=row.action_id).exists()
    with pytest.raises(ValidationError):
        inspect_assessment(
            actor,
            case.pk,
            case.version,
            row.pk,
            uuid4(),
            "Reject reading purged synthetic assessment",
        )
    assert not RightsAction.objects.filter(operation="portability_read").exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("account_only", [False, True])
def test_assessment_inventory_is_scoped_opaque_and_detects_changed_ciphertext(
    request, settings, monkeypatch, account_only
):
    from uuid import uuid4

    from django.db import transaction
    from test_account_copy_races import prepared_account
    from test_rights_responses import ready

    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.models import RightsRequest
    from apps.safety.rights_portability import save_assessment

    if account_only:
        case, actor, _, subject, _, _ = prepared_account(
            request, settings, monkeypatch, "portability"
        )
        person = None
    else:
        case, actor, _, _, _, person = ready(request, settings, monkeypatch, "portability")
        subject = None
    row = save_assessment(
        actor,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Store synthetic assessment for scoped inventory",
        assessment(),
    )
    with transaction.atomic():
        if account_only:
            current = source_manifest(None, case)
            assert (
                next(
                    item
                    for item in current["entries"]
                    if item["model"] == "safety.RightsPortabilityAssessment"
                )["count"]
                == 0
            )
            inventory_case = RightsRequest.objects.create(
                submission_key=uuid4(),
                account_subject=subject,
                kind="erase",
                received_at=case.received_at,
                initial_due_at=case.initial_due_at,
                receipt_expires_at=case.receipt_expires_at,
            )
        else:
            inventory_case = case
        if account_only:
            current = source_manifest(None, case)
        original = source_manifest(person, inventory_case)
        entry = next(
            item
            for item in original["entries"]
            if item["model"] == "safety.RightsPortabilityAssessment"
        )
        assert entry["count"] == 1
        assert row.encrypted_assessment not in str(original)
        type(row).objects.filter(pk=row.pk).update(
            encrypted_assessment="Damaged opaque synthetic assessment"
        )
        changed = source_manifest(person, inventory_case)
        changed_entry = next(
            item
            for item in changed["entries"]
            if item["model"] == "safety.RightsPortabilityAssessment"
        )
        assert changed_entry["count"] == 1
        assert changed_entry["state_digest"] != entry["state_digest"]
        assert "Damaged opaque synthetic assessment" not in str(changed)
        if account_only:
            assert source_manifest(None, case) == current
