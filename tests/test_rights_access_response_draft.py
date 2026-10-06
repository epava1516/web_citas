from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccessResponseDraft, RightsAction, RightsResponse
from apps.safety.rights_access_response_draft import prepare
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Prepare synthetic access explanation bound to approved information"
TEXT = "Your private access copy contains the reviewed information. The remaining scope requires further review before a final decision can be issued."


@pytest.mark.parametrize("account_only", [False, True])
def test_access_draft_requires_fresh_proof_and_does_not_close(
    request, settings, monkeypatch, account_only
):
    case, author, staff, _, _, _, _, _, decision, document, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    export = generate(
        author,
        case.pk,
        uuid4(),
        case.version,
        REASON,
        preview(author, case.pk, case.version, REASON),
        information_review_id=decision.pk,
    )
    case.refresh_from_db()
    read(staff, case)

    def invoke(key, text=TEXT):
        return prepare(
            author, case.pk, case.version, case.response_version, export.pk, key, REASON, text, True
        )

    with pytest.raises(ValidationError):
        invoke(uuid4())
    assert not RightsAccessResponseDraft.objects.exists()
    verifier = User.objects.get(username="fixture-v1-visitor")
    verifier.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    verifier = User.objects.get(pk=verifier.pk)
    proof = fresh(case, author, staff, verifier, operator(verifier))
    original = case.version, case.response_version, case.status, case.initial_due_at
    key = uuid4()
    import apps.safety.rights_access_response_draft as module

    real_validate = module.validate_export_binding

    def audited(*args):
        assert RightsAction.objects.filter(key=key, operation="access_draft").exists()
        return real_validate(*args)

    monkeypatch.setattr(module, "validate_export_binding", audited)
    row = invoke(key)
    assert invoke(key).pk == row.pk
    assert row.proof_id == proof.pk and row.information_review_id == decision.pk
    assert TEXT not in row.encrypted_response
    assert unseal(row.encrypted_response) == {"text": TEXT, "simulation": True}
    with pytest.raises(ValidationError, match="Conflicting"):
        invoke(key, TEXT + " Changed scope.")
    from django.core.exceptions import PermissionDenied
    from django.db import transaction

    from apps.safety.rights_access_response_evidence import validate_review
    from apps.safety.rights_access_response_review import inspect, record

    verifier.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    verifier = User.objects.get(pk=verifier.pk)
    read(operator(verifier), case)
    with pytest.raises(PermissionDenied):
        inspect(author, case.pk, case.version, row.pk, uuid4(), REASON)
    with pytest.raises(ValidationError, match="Inspect the exact"):
        record(verifier, case.pk, case.version, row.pk, 0, uuid4(), REASON, "approved")
    read_key = uuid4()
    inspected, body = inspect(verifier, case.pk, case.version, row.pk, read_key, REASON)
    assert inspected.pk == row.pk and body["text"] == TEXT
    inspection = RightsAction.objects.get(key=read_key)
    decision_key = uuid4()
    reviewed = record(
        verifier, case.pk, case.version, row.pk, inspection.pk, decision_key, REASON, "approved"
    )
    assert (
        record(
            verifier, case.pk, case.version, row.pk, inspection.pk, decision_key, REASON, "approved"
        ).pk
        == reviewed.pk
    )
    with transaction.atomic():
        assert (
            validate_review(reviewed, case, None if account_only else case.person)["text"] == TEXT
        )
    from django.test import Client
    from django.urls import reverse

    from apps.safety.rights_access_close import close

    with pytest.raises(ValidationError, match="Complete reviewed access delivery"):
        close(author, case.pk, case.version, case.response_version, reviewed.pk, uuid4(), REASON)
    assert not RightsResponse.objects.exists()
    close_path = reverse("rights_access_close", args=[case.pk, reviewed.pk])
    assert staff.get(close_path).status_code == 200
    assert operator(verifier).get(close_path).status_code == 403
    blocked = staff.post(
        close_path,
        {
            "key": uuid4(),
            "version": case.version,
            "response_version": case.response_version,
            "reason": REASON,
        },
    )
    assert blocked.status_code == 409 and TEXT not in blocked.content.decode()
    assert not RightsResponse.objects.exists()

    path = reverse("rights_access_response_prepare", args=[case.pk])
    review_path = reverse("rights_access_response_review", args=[case.pk, row.pk])
    before = RightsAction.objects.count()
    assert staff.get(path).status_code == 200
    assert TEXT not in staff.get(path).content.decode()
    other = operator(verifier)
    inspection_path = reverse("rights_inspect", args=[case.pk])
    assert path in staff.get(inspection_path).content.decode()
    assert review_path in other.get(inspection_path).content.decode()
    assert review_path not in staff.get(inspection_path).content.decode()
    page = other.get(review_path)
    assert page.status_code == 200 and "no-store" in page["Cache-Control"]
    assert TEXT not in page.content.decode() and RightsAction.objects.count() == before
    assert staff.get(review_path).status_code == 403
    assert Client().get(path).status_code == 302
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(verifier)
    assert csrf.post(review_path, {}).status_code == 403
    response = other.post(
        review_path,
        {"operation": "inspect", "key": read_key, "version": case.version, "reason": REASON},
    )
    assert response.status_code == 200 and TEXT in response.content.decode()
    response = other.post(
        review_path,
        {
            "operation": "review",
            "key": decision_key,
            "version": case.version,
            "reason": REASON,
            "read_id": inspection.pk,
            "outcome": "approved",
        },
    )
    assert response.status_code == 200 and TEXT not in response.content.decode()

    reviewed.text_digest = "0" * 64
    reviewed.save(update_fields=["text_digest"])
    with transaction.atomic(), pytest.raises(ValidationError, match="signatures changed"):
        validate_review(reviewed, case, None if account_only else case.person)

    row.encrypted_response = "damaged"
    row.save(update_fields=["encrypted_response"])
    with pytest.raises(ValidationError, match="encrypted evidence unavailable"):
        invoke(key)
    row.encrypted_response = module.seal({"text": TEXT, "simulation": True})
    row.save(update_fields=["encrypted_response"])
    document.body = "Changed synthetic privacy policy"
    document.save(update_fields=["body"])
    with pytest.raises(ValidationError):
        invoke(key)
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original
    assert not RightsResponse.objects.exists()
    assert RightsAccessResponseDraft.objects.count() == 1

    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.tasks import purge_expired_access_response_drafts

    metadata = row.action_id, row.export_id, row.information_review_id, row.proof_id
    assert purge_expired_access_response_drafts() == 0
    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save(update_fields=["expires_at"])
    assert purge_expired_access_response_drafts() == 1
    assert purge_expired_access_response_drafts() == 0
    row.refresh_from_db()
    assert not row.encrypted_response and row.purged_at
    assert (row.action_id, row.export_id, row.information_review_id, row.proof_id) == metadata
