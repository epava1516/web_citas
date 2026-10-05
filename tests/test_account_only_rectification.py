"""Account-only proposals use audited sources and never introduce editorial data."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_account_verification import setup_account
from test_rights_verification import read

from apps.core.models import Person
from apps.safety.crypto import unseal
from apps.safety.rights_rectification import preview, propose
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def verified(request, settings):
    case, actor, staff, subject, verifier, other = setup_account(request, settings)
    actor.user_permissions.add(Permission.objects.get(codename="execute_rights_request"))
    if hasattr(actor, "_perm_cache"):
        del actor._perm_cache
    if hasattr(actor, "_user_perm_cache"):
        del actor._user_perm_cache
    proof = start(actor, case.pk, uuid4(), case.version, "Synthetic own account source assessment")
    case.refresh_from_db()
    read(other, case)
    receive_event(
        verifier,
        simulate_event(
            proof.pk,
            uuid4(),
            case.version,
            "passed",
            "Independent synthetic own account assessment",
        ),
    )
    case.refresh_from_db()
    read(staff, case)
    return case, actor, staff, subject


def test_account_only_source_and_proposal_require_audit_without_mutating_user(request, settings):
    case, actor, staff, subject = verified(request, settings)
    changes = {
        "account": {
            "first_name": "Corrected synthetic name",
            "email": "new-account-only@example.invalid",
        }
    }
    reason = "Independently requested own account correction"
    before = subject.email, subject.first_name, subject.session_version
    key = uuid4()
    with pytest.raises(ValidationError, match="Read current"):
        propose(actor, case.pk, key, case.version, changes, reason)
    source = preview(
        actor, case.pk, case.version, "Inspect own account data for proposed correction"
    )
    assert source["account"]["email"] == subject.email and source["alias"] == ""
    assert subject.password not in str(source) and "authentication_digest" not in str(source)
    result = propose(actor, case.pk, key, case.version, changes, reason)
    assert propose(actor, case.pk, key, case.version, changes, reason).pk == result.pk
    assert result.account_subject_id == subject.pk and result.person_id is None
    assert result.source_revision_id is None and unseal(result.encrypted_changes) == changes
    assert changes["account"]["email"] not in result.encrypted_changes
    subject.refresh_from_db()
    assert (subject.email, subject.first_name, subject.session_version) == before
    assert not Person.objects.filter(subject=subject).exists()


def test_account_scope_rejects_editorial_fields_and_changed_source(request, settings):
    case, actor, _, subject = verified(request, settings)
    preview(actor, case.pk, case.version, "Inspect own account data for proposed correction")
    for changes in (
        {"alias": "Unauthorized profile"},
        {"account": {"first_name": "Synthetic"}, "title": "Unauthorized listing"},
    ):
        with pytest.raises(ValidationError, match="Account scope only"):
            propose(
                actor,
                case.pk,
                uuid4(),
                case.version,
                changes,
                "Independently requested own account correction",
            )
    subject.first_name = "Source changed"
    subject.save(update_fields=["first_name"])
    with pytest.raises(ValidationError):
        propose(
            actor,
            case.pk,
            uuid4(),
            case.version,
            {"account": {"first_name": "Synthetic"}},
            "Independently requested own account correction",
        )
    assert not case.actions.filter(operation="rectify_plan").exists()
