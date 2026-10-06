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
