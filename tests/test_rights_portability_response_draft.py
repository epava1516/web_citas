from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_covered_export_races import approved_coverage
from test_rights_verification import read

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsPortabilityResponseDraft
from apps.safety.rights_portability_export import generate
from apps.safety.rights_portability_response_draft import prepare
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Prepare a reviewed final explanation for the synthetic private delivery"
TEXT = "Your scoped private copy is available through this protected receipt. Excluded information is explained in this response and remains outside the copy."


def operator(user):
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    return client


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("outcome", ["approved", "rejected"])
def test_final_draft_requires_new_authorization_preserves_case_and_validates_replay(
    request, settings, monkeypatch, account_only, outcome
):
    case, author, selection, selected, coverage, decision, reviewer, profile, subject, _ = (
        approved_coverage(request, settings, monkeypatch, account_only)
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
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
    staff = operator(author)
    read(staff, case)
    with pytest.raises(ValidationError):
        prepare(
            author,
            case.pk,
            case.version,
            case.response_version,
            export.pk,
            uuid4(),
            REASON,
            TEXT,
            True,
        )
    proof = start(author, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    reviewer.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    reviewer = User.objects.get(pk=reviewer.pk)
    other = operator(reviewer)
    read(other, case)
    receive_event(reviewer, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(staff, case)
    original = case.version, case.response_version, case.status, case.initial_due_at
    key = uuid4()
    import apps.safety.rights_portability_response_draft as module

    real_validate = module.validate_export_binding

    def audited(*args):
        assert RightsAction.objects.filter(key=key, operation="portability_draft").exists()
        return real_validate(*args)

    monkeypatch.setattr(module, "validate_export_binding", audited)
    draft = prepare(
        author, case.pk, case.version, case.response_version, export.pk, key, REASON, TEXT, True
    )
    from django.db import transaction

    from apps.safety.rights_portability_response_evidence import validate_draft

    with transaction.atomic():
        assert validate_draft(draft, case, profile) == {"text": TEXT, "simulation": True}
    original_digest = draft.text_digest
    draft.text_digest = "0" * 64
    draft.save(update_fields=["text_digest"])
    with transaction.atomic(), pytest.raises(ValidationError, match="signature changed"):
        validate_draft(draft, case, profile)
    draft.text_digest = original_digest
    draft.save(update_fields=["text_digest"])
    assert draft.export_id == export.pk and draft.coverage_review_id == decision.pk
    assert draft.proof_id == proof.pk and draft.proof_id != export.proof_id
    assert TEXT not in draft.encrypted_response
    assert unseal(draft.encrypted_response) == {"text": TEXT, "simulation": True}
    assert (
        prepare(
            author, case.pk, case.version, case.response_version, export.pk, key, REASON, TEXT, True
        ).pk
        == draft.pk
    )
    from django.urls import reverse

    path = reverse("rights_portability_response_prepare", args=[case.pk])
    before_actions = RightsAction.objects.count()
    response = staff.get(path)
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert TEXT not in response.content.decode()
    assert RightsAction.objects.count() == before_actions
    data = {
        "key": str(key),
        "version": case.version,
        "response_version": case.response_version,
        "export": str(export.pk),
        "reason": REASON,
        "response": TEXT,
        "redaction_confirmed": True,
    }
    assert staff.post(path, data).status_code == 200
    assert Client().get(path).status_code == 302
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(author)
    assert csrf.post(path, data).status_code == 403
    assert RightsPortabilityResponseDraft.objects.count() == 1
    with pytest.raises(ValidationError, match="Conflicting"):
        prepare(
            author,
            case.pk,
            case.version,
            case.response_version,
            export.pk,
            key,
            REASON,
            TEXT + " Changed.",
            True,
        )
    from django.core.exceptions import PermissionDenied

    from apps.safety.rights_portability_response_review import inspect

    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    read(operator(reviewer), case)
    review_key = uuid4()
    real_body = module.checked_body

    def audited_body(ciphertext):
        assert RightsAction.objects.filter(key=review_key, operation="final_draft_read").exists()
        return real_body(ciphertext)

    monkeypatch.setattr(module, "checked_body", audited_body)
    inspected, public = inspect(reviewer, case.pk, case.version, draft.pk, review_key, REASON)
    assert inspected.pk == draft.pk and public["text"] == TEXT and public["simulation"] is True
    assert inspect(reviewer, case.pk, case.version, draft.pk, review_key, REASON)[0].pk == draft.pk
    with pytest.raises(PermissionDenied):
        inspect(author, case.pk, case.version, draft.pk, uuid4(), REASON)
    from apps.safety.rights_portability_response_review import record

    review_path = reverse("rights_portability_response_review", args=[case.pk, draft.pk])
    other = operator(reviewer)
    inspect_path = reverse("rights_inspect", args=[case.pk])
    before_actions = RightsAction.objects.count()
    navigation = other.get(inspect_path)
    assert navigation.status_code == 200 and review_path in navigation.content.decode()
    assert (
        TEXT not in navigation.content.decode() and RightsAction.objects.count() == before_actions
    )
    assert review_path not in staff.get(inspect_path).content.decode()
    before_actions = RightsAction.objects.count()
    response = other.get(review_path)
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert TEXT not in response.content.decode() and RightsAction.objects.count() == before_actions
    response = other.post(
        review_path,
        {"operation": "inspect", "key": str(review_key), "version": case.version, "reason": REASON},
    )
    assert response.status_code == 200 and TEXT in response.content.decode()
    assert staff.get(review_path).status_code == 403
    read_action = RightsAction.objects.get(key=review_key)
    with pytest.raises(ValidationError, match="Inspect the exact"):
        record(reviewer, case.pk, case.version, draft.pk, 0, uuid4(), REASON, outcome)
    decision_key = uuid4()
    approved = record(
        reviewer, case.pk, case.version, draft.pk, read_action.pk, decision_key, REASON, outcome
    )
    from apps.safety.rights_portability_response_evidence import validate_review

    with transaction.atomic():
        assert validate_review(approved, case, profile, require_approved=False)["text"] == TEXT
    if outcome == "rejected":
        with transaction.atomic(), pytest.raises(ValidationError, match="Approved final response"):
            validate_review(approved, case, profile)
    assert approved.outcome == outcome and approved.read_action_id == read_action.pk
    assert (
        record(
            reviewer,
            case.pk,
            case.version,
            draft.pk,
            read_action.pk,
            decision_key,
            REASON,
            outcome,
        ).pk
        == approved.pk
    )
    with pytest.raises(ValidationError, match="Conflicting"):
        record(
            reviewer,
            case.pk,
            case.version,
            draft.pk,
            read_action.pk,
            decision_key,
            REASON,
            ("rejected" if outcome == "approved" else "approved"),
        )
    response = other.post(
        review_path,
        {
            "operation": "review",
            "key": str(decision_key),
            "version": case.version,
            "read_id": read_action.pk,
            "reason": REASON,
            "outcome": outcome,
        },
    )
    assert response.status_code == 200 and TEXT not in response.content.decode()
    assert TEXT not in other.get(review_path).content.decode()
    assert Client().get(review_path).status_code == 302
    assert csrf.post(review_path, {}).status_code == 403
    approved.text_digest = "0" * 64
    approved.save(update_fields=["text_digest"])
    with pytest.raises(ValidationError, match="evidence changed"):
        record(
            reviewer,
            case.pk,
            case.version,
            draft.pk,
            read_action.pk,
            decision_key,
            REASON,
            outcome,
        )
    approved.text_digest = draft.text_digest
    approved.save(update_fields=["text_digest"])
    from django.db import transaction

    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.models import RightsRequest

    inventory_case = RightsRequest.objects.create(
        submission_key=uuid4(),
        kind="erase",
        person=profile,
        account_subject=subject if account_only else None,
        received_at=case.received_at,
        initial_due_at=case.initial_due_at,
        receipt_expires_at=case.receipt_expires_at,
    )

    def inventory_rows():
        with transaction.atomic():
            manifest = source_manifest(profile, inventory_case)
            assert TEXT not in str(manifest) and draft.encrypted_response not in str(manifest)
            return {item["model"]: item for item in manifest["entries"]}

    before = inventory_rows()
    for name in ["RightsPortabilityResponseDraft", "RightsPortabilityResponseReview"]:
        assert before["safety." + name]["count"] == 1
    approved.text_digest = "0" * 64
    approved.save(update_fields=["text_digest"])
    assert (
        inventory_rows()["safety.RightsPortabilityResponseReview"]["state_digest"]
        != before["safety.RightsPortabilityResponseReview"]["state_digest"]
    )
    approved.text_digest = draft.text_digest
    approved.save(update_fields=["text_digest"])
    assert inventory_rows() == before
    stale_reviewer = User.objects.get(pk=reviewer.pk)
    reviewer.session_version += 1
    reviewer.save(update_fields=["session_version"])
    with pytest.raises(PermissionDenied):
        record(
            stale_reviewer,
            case.pk,
            case.version,
            draft.pk,
            read_action.pk,
            decision_key,
            REASON,
            outcome,
        )
    with pytest.raises(ValidationError, match="Conflicting final draft inspection"):
        record(
            User.objects.get(pk=reviewer.pk),
            case.pk,
            case.version,
            draft.pk,
            read_action.pk,
            decision_key,
            REASON,
            outcome,
        )
    reviewer.session_version -= 1
    reviewer.save(update_fields=["session_version"])
    monkeypatch.setattr(module, "checked_body", real_body)
    draft.encrypted_response = "damaged"
    draft.save(update_fields=["encrypted_response"])
    with pytest.raises(ValidationError, match="encrypted evidence unavailable"):
        prepare(
            author, case.pk, case.version, case.response_version, export.pk, key, REASON, TEXT, True
        )
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original

    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.tasks import purge_expired_portability_response_drafts

    metadata = draft.action_id, draft.export_id, draft.coverage_review_id, draft.proof_id
    draft.expires_at = timezone.now() - timedelta(seconds=1)
    draft.save(update_fields=["expires_at"])
    assert purge_expired_portability_response_drafts() == 1
    assert purge_expired_portability_response_drafts() == 0
    draft.refresh_from_db()
    assert not draft.encrypted_response and draft.purged_at
    assert (draft.action_id, draft.export_id, draft.coverage_review_id, draft.proof_id) == metadata
