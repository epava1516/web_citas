from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_information import draft
from test_rights_exports import prepared
from test_rights_verification import read

from apps.core.models import LegalDocument, User
from apps.safety.models import RightsCopyInformationRead, RightsCopyInformationReview
from apps.safety.rights_copy_information import record as save
from apps.safety.rights_information_policy import published_policy
from apps.safety.rights_information_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("complete", [False, True])
def test_independent_review_requires_audited_read_and_resolved_information(
    request, settings, complete, monkeypatch
):
    case, author, _, _, _, person = prepared(request, settings)
    document = LegalDocument.objects.get(slug="privacy", language="es", active=True)
    with transaction.atomic():
        _, digest = published_policy(document.pk, "es")
    value = draft()
    if complete:
        for item in value["access"].values():
            item.update(status="reviewed", source="reviewer", text="Synthetic reviewed information")
    row = save(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        document.version,
        "Prepare synthetic information for independent review",
        value,
        policy_document_id=document.pk,
        expected_policy_digest=digest,
    )
    permissions = Permission.objects.filter(
        codename__in=["review_rights_request", "execute_rights_request", "review_copy_information"]
    )
    author.user_permissions.add(*permissions)
    author = User.objects.get(pk=author.pk)
    with pytest.raises(PermissionDenied):
        record(
            author,
            case.pk,
            row.pk,
            uuid4(),
            case.version,
            "inspect",
            "Inspect own information is prohibited",
        )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(*permissions)
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    reason = "Independently review synthetic additional access information"
    key = uuid4()
    with pytest.raises(ValidationError, match="Inspect this"):
        record(reviewer, case.pk, row.pk, key, case.version, "review", reason, "approved")
    from apps.safety import rights_information_review
    from apps.safety.models import RightsAction, RightsCopyInformation

    original_unseal = rights_information_review.unseal

    def audited_unseal(ciphertext):
        if ciphertext == row.encrypted_information:
            assert RightsAction.objects.filter(
                request=case, actor=reviewer, operation="copy_info_inspect"
            ).exists()
        return original_unseal(ciphertext)

    monkeypatch.setattr(rights_information_review, "unseal", audited_unseal)
    inspection_key = uuid4()
    inspection, body = record(
        reviewer, case.pk, row.pk, inspection_key, case.version, "inspect", reason
    )
    assert inspection.original_session_version == reviewer.session_version
    assert inspection.original_mfa_version == reviewer.mfa_version
    assert body == value
    assert (
        record(reviewer, case.pk, row.pk, inspection_key, case.version, "inspect", reason)[0].pk
        == inspection.pk
    )
    assert RightsCopyInformationRead.objects.count() == 1
    if not complete:
        with pytest.raises(ValidationError, match="Unresolved"):
            record(reviewer, case.pk, row.pk, key, case.version, "review", reason, "approved")
    outcome = "approved" if complete else "rejected"
    decision, body = record(reviewer, case.pk, row.pk, key, case.version, "review", reason, outcome)
    assert decision.original_session_version == reviewer.session_version
    assert decision.original_mfa_version == reviewer.mfa_version
    assert body is None and decision.read_id == inspection.pk
    assert (
        record(reviewer, case.pk, row.pk, key, case.version, "review", reason, outcome)[0].pk
        == decision.pk
    )
    assert RightsCopyInformationReview.objects.count() == 1
    from apps.safety.rights_information_review import validate_action_evidence

    with transaction.atomic():
        validate_action_evidence(inspection, row, case, row.proof)
        validate_action_evidence(decision, row, case, row.proof)
    decision.original_mfa_version += 1
    with transaction.atomic(), pytest.raises(ValidationError, match="evidence"):
        validate_action_evidence(decision, row, case, row.proof)
    decision.original_mfa_version -= 1
    from apps.safety.rights_information_review import validate_approved_evidence

    with transaction.atomic():
        if complete:
            assert (
                validate_approved_evidence(decision, row, case, row.proof, row.source_digest, value)
                == value
            )
        else:
            with pytest.raises(ValidationError, match="approved"):
                validate_approved_evidence(decision, row, case, row.proof, row.source_digest, value)
    if complete:
        from apps.safety.rights_information_export import consume_approved

        use_key = uuid4()
        used, approved_body = consume_approved(
            author,
            case.pk,
            case.version,
            decision.pk,
            use_key,
            "Prepare reviewed information for export generation",
        )
        assert used.pk == decision.pk and approved_body == value
        assert (
            consume_approved(
                author,
                case.pk,
                case.version,
                decision.pk,
                use_key,
                "Prepare reviewed information for export generation",
            )[0].pk
            == decision.pk
        )
        assert RightsAction.objects.filter(request=case, operation="copy_info_use").count() == 1
        RightsCopyInformationRead.objects.filter(pk=inspection.pk).update(
            original_session_version=inspection.original_session_version + 1
        )
        with transaction.atomic(), pytest.raises(ValidationError, match="evidence"):
            validate_approved_evidence(decision, row, case, row.proof, row.source_digest, value)
        RightsCopyInformationRead.objects.filter(pk=inspection.pk).update(
            original_session_version=inspection.original_session_version
        )
    from apps.safety.erasure_inventory import source_manifest

    manifest = source_manifest(person)
    entries = {item["model"]: item for item in manifest["entries"]}
    for model in ["RightsCopyInformationRead", "RightsCopyInformationReview"]:
        assert entries["safety." + model]["count"] == 1
        assert entries["safety." + model]["purpose"] == "dependent_evidence"
    assert reason not in str(manifest) and decision.action.encrypted_reason not in str(manifest)
    case.refresh_from_db()
    assert case.version == row.action.expected_version and case.status == "reviewing"
    from django.urls import reverse
    from django.utils.translation import override

    with override("en" if complete else "es"):
        path = reverse(
            "rights_information_review", kwargs={"case_id": case.pk, "information_id": row.pk}
        )
    with override("en" if complete else "es"):
        inspection_path = reverse("rights_inspect", kwargs={"case_id": case.pk})
    discovery = client.get(inspection_path)
    assert [item.pk for item in discovery.context["information_drafts"]] == [row.pk]
    assert path.encode() in discovery.content
    assert b"Synthetic reviewed information" not in discovery.content
    initial = client.get(path)
    assert initial.status_code == 200 and initial.context["body"] is None
    payload = {
        "key": uuid4(),
        "version": case.version,
        "operation": "inspect",
        "reason": reason,
        "outcome": "",
    }
    response = client.post(path, payload)
    assert response.status_code == 200 and response.context["body"] == value
    assert client.post(path, payload).status_code == 200
    assert client.get(path).context["body"] is None
    before = RightsAction.objects.count()
    original_ciphertext = row.encrypted_information
    RightsCopyInformation.objects.filter(pk=row.pk).update(
        encrypted_information="damaged ciphertext"
    )
    assert client.post(path, payload | {"key": uuid4()}).status_code == 409
    assert RightsAction.objects.count() == before
    RightsCopyInformation.objects.filter(pk=row.pk).update(
        encrypted_information=original_ciphertext
    )
    RightsCopyInformation.objects.filter(pk=row.pk).update(original_session_version=None)
    assert client.post(path, payload | {"key": uuid4()}).status_code == 409
    assert RightsAction.objects.count() == before
    RightsCopyInformation.objects.filter(pk=row.pk).update(
        original_session_version=row.original_session_version
    )
    from django.utils import timezone

    RightsCopyInformation.objects.filter(pk=row.pk).update(
        purged_at=timezone.now(), encrypted_information=""
    )
    assert client.post(path, payload | {"key": uuid4()}).status_code == 409
    assert RightsAction.objects.count() == before
    RightsCopyInformation.objects.filter(pk=row.pk).update(
        purged_at=None, encrypted_information=original_ciphertext
    )
    case.proofs.update(status="failed")
    assert client.post(path, payload | {"key": uuid4()}).status_code == 409
    assert RightsAction.objects.count() == before
    reviewer.user_permissions.clear()
    assert client.post(path, payload).status_code == 403


@pytest.mark.parametrize("kind", ["access", "portability"])
def test_account_review_evidence_inventory_is_scoped_and_excludes_current_procedure(
    request, settings, monkeypatch, kind
):
    from copy import copy

    from test_account_copy_races import prepared_account

    from apps.safety.account_erasure_inventory import source
    from apps.safety.models import RightsRequest

    case, author, _, subject, _, _ = prepared_account(request, settings, monkeypatch, kind)
    document = LegalDocument.objects.get(slug="privacy", language="es", active=True)
    with transaction.atomic():
        _, digest = published_policy(document.pk, "es")
    value = draft()
    if kind == "portability":
        value["portability"] = {"status": "pending", "reason": ""}
    row = save(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        document.version,
        "Save synthetic account information before independent review",
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
    reason = "Independently inspect and reject pending synthetic account information"
    record(reviewer, case.pk, row.pk, uuid4(), case.version, "inspect", reason)
    with pytest.raises(ValidationError, match="Unresolved"):
        record(reviewer, case.pk, row.pk, uuid4(), case.version, "review", reason, "approved")
    decision, _ = record(
        reviewer, case.pk, row.pk, uuid4(), case.version, "review", reason, "rejected"
    )
    # Cloned cases exercise inventory scope only, not accepted rights workflows.
    previous = copy(case)
    previous.pk, previous.submission_key = uuid4(), uuid4()
    previous._state.adding = True
    previous.save(force_insert=True)
    foreign = copy(previous)
    foreign.pk, foreign.submission_key = uuid4(), uuid4()
    foreign.account_subject = User.objects.exclude(pk=subject.pk).first()
    foreign._state.adding = True
    foreign.save(force_insert=True)

    def snapshot(case_id):
        with transaction.atomic():
            manifest = source(RightsRequest.objects.get(pk=case_id))
            assert reason not in str(manifest)
            assert decision.action.encrypted_reason not in str(manifest)
            return {item["model"]: item for item in manifest["entries"]}

    current, visible, excluded = snapshot(case.pk), snapshot(previous.pk), snapshot(foreign.pk)
    for model in ["RightsCopyInformationRead", "RightsCopyInformationReview"]:
        name = "safety." + model
        assert current[name]["count"] == excluded[name]["count"] == 0
        assert visible[name]["count"] == 1
    decision.action.encrypted_reason = "Opaque damaged synthetic decision reason"
    decision.action.save(update_fields=["encrypted_reason"])
    changed = snapshot(previous.pk)
    name = "safety.RightsCopyInformationReview"
    assert changed[name]["state_digest"] != visible[name]["state_digest"]
    assert snapshot(case.pk) == current and snapshot(foreign.pk) == excluded
