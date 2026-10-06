from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information

from apps.safety.rights import fingerprint
from apps.safety.rights_access_evidence_refs import bind_references
from apps.safety.rights_exports import canonical, generate, preview

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_export_preparation_references_reject_changed_or_unrelated_evidence(
    request, settings, monkeypatch, account_only
):
    case, author, _, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    reason = "Synthetic access reference scope verification"
    export = generate(
        author,
        case.pk,
        uuid4(),
        case.version,
        reason,
        preview(author, case.pk, case.version, reason),
        information_review_id=decision.pk,
    )
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
    refs = {"information": {"action": action.pk, "digest": fingerprint(canonical(snapshot))}}
    with pytest.raises(RuntimeError):
        bind_references(case, export, refs)
    with transaction.atomic():
        result = bind_references(case, export, refs)
        assert result["information"]["action"] == action.pk
        assert action.encrypted_reason not in str(result)
        for change in ["payload_digest", "encrypted_reason", "expected_version", "operation"]:
            original = getattr(action, change)
            invalid = original + 1 if change == "expected_version" else "altered"
            type(action).objects.filter(pk=action.pk).update(**{change: invalid})
            with pytest.raises(ValidationError):
                bind_references(case, export, refs)
            type(action).objects.filter(pk=action.pk).update(**{change: original})
        with pytest.raises(ValidationError):
            bind_references(
                case,
                export,
                {
                    "information": {
                        "action": export.action_id,
                        "digest": refs["information"]["digest"],
                    }
                },
            )
        with pytest.raises(ValidationError):
            bind_references(
                case,
                export,
                {"information": {"action": True, "digest": refs["information"]["digest"]}},
            )
        assert bind_references(case, export, refs) == result
