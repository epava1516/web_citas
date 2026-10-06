from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccessCoverage, RightsAction
from apps.safety.rights import fingerprint
from apps.safety.rights_access_coverage import UNPROJECTED
from apps.safety.rights_access_coverage_store import required_references, save
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import canonical, generate, preview
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_audited_coverage_preserves_open_request_and_rejects_stale_replay(
    request, settings, monkeypatch, account_only
):
    case, author, staff, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    reason = "Synthetic coverage preparation with exact evidence references"
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    source = preview(author, case.pk, case.version, reason)
    export = generate(
        author, case.pk, uuid4(), case.version, reason, source, information_review_id=decision.pk
    )
    delivered = unseal(export.encrypted_payload)
    verifier = User.objects.get(username="fixture-v1-visitor")
    verifier.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    verifier = User.objects.get(pk=verifier.pk)
    fresh(case, author, staff, verifier, operator(verifier))
    declarations = {
        "sections": {
            section: [
                {
                    "row": row_reference(section, index, row),
                    "delivered_index": index,
                    "decisions": {},
                }
                for index, row in enumerate(project(source))
            ]
            for section, project in SECTIONS.items()
        },
        "boundaries": {
            name: {
                "status": "excluded",
                "reason": "Synthetic declaration awaiting independent evidence validation",
                "evidence": "Synthetic referenced information review, not final approval",
            }
            for name in set(source["pending_review"])
            | set(delivered["pending_review"])
            | UNPROJECTED
        },
    }
    action = decision.action
    snapshot = {
        "action": action.pk,
        "request": str(action.request_id),
        "actor": action.actor_id,
        "version": action.expected_version,
        "operation": action.operation,
        "payload": action.payload_digest,
        "reason_ciphertext": fingerprint(action.encrypted_reason),
    }
    refs = {
        label: {"action": action.pk, "digest": fingerprint(canonical(snapshot))}
        for label in required_references(declarations)
    }
    key = uuid4()

    def invoke():
        return save(
            author,
            case.pk,
            case.version,
            case.response_version,
            export.pk,
            key,
            reason,
            delivered,
            declarations,
            refs,
            fingerprint(canonical(source)),
            fingerprint(canonical(delivered)),
        )

    import apps.safety.rights_access_coverage_store as module

    real_validate = module.validate_transport

    def audited(*args):
        assert RightsAction.objects.filter(key=key, operation="access_coverage").exists()
        return real_validate(*args)

    monkeypatch.setattr(module, "validate_transport", audited)
    original = case.version, case.response_version, case.status
    row = invoke()
    assert invoke().pk == row.pk
    assert reason not in row.encrypted_coverage
    assert unseal(row.encrypted_coverage)["bound_references"]
    row.binding_digest = "0" * 64
    row.save(update_fields=["binding_digest"])
    with pytest.raises(ValidationError, match="references changed"):
        invoke()
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status) == original
    assert RightsAccessCoverage.objects.count() == 1
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.tasks import purge_expired_access_coverage

    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save(update_fields=["expires_at"])
    assert purge_expired_access_coverage() == 1
    assert purge_expired_access_coverage() == 0
    row.refresh_from_db()
    assert row.purged_at and not row.encrypted_coverage
