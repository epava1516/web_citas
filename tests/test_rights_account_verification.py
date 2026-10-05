"""Account scope authority remains independent and stale account state is rejected."""

from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_account_linking import account
from test_rights_assignment import action
from test_rights_verification import prepared, read

from apps.safety.models import RightsProofEvent
from apps.safety.rights_verification import authorized_proof, receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def setup_account(request, settings):
    case, actor, staff, _, verifier, other = prepared(request, settings)
    subject = account()
    # Existing fixture supplies independent actors; reset to an unlinked received scope.
    case.person = None
    case.referenced_revision = None
    case.manager_version = None
    case.reported_agency = None
    case.reported_individual = None
    case.reported_subject = None
    case.kind = "rectify"
    case.save()
    read(staff, case)
    path, values = action(staff, case, "link")
    assert staff.post(path, values | {"link_account_id": subject.pk}).status_code == 302
    case.refresh_from_db()
    read(staff, case)
    return case, actor, staff, subject, verifier, other


def test_account_proof_independent_pass_and_state_invalidation(request, settings):
    case, actor, staff, subject, verifier, other = setup_account(request, settings)
    proof = start(actor, case.pk, uuid4(), case.version, "Synthetic own account scope assessment")
    assert proof.person_id is None and proof.account_subject_id == subject.pk
    assert (
        subject.email not in proof.account_source_digest and len(proof.account_source_digest) == 64
    )
    case.refresh_from_db()
    event = simulate_event(
        proof.pk,
        uuid4(),
        case.version,
        "passed",
        "Independent synthetic assessment of own account scope",
    )
    with pytest.raises(PermissionDenied):
        receive_event(actor, event)
    with pytest.raises(ValidationError):
        receive_event(verifier, event)
    read(other, case)
    assert receive_event(verifier, event).pk == proof.pk
    assert receive_event(verifier, event).pk == proof.pk
    case.refresh_from_db()
    with transaction.atomic():
        assert authorized_proof(case, None, "rectify").pk == proof.pk
    subject.first_name = "Changed after independent check"
    subject.save(update_fields=["first_name"])
    with transaction.atomic(), pytest.raises(ValidationError):
        authorized_proof(case, None, "rectify")
    assert RightsProofEvent.objects.filter(proof=proof).count() == 1
    settings.PRODUCTION = True
    with transaction.atomic(), pytest.raises(ValidationError):
        authorized_proof(case, None, "rectify")


@pytest.mark.parametrize("field", ["email", "session_version", "mfa_version"])
def test_account_state_change_before_result_never_passes(request, settings, field):
    case, actor, _, subject, verifier, other = setup_account(request, settings)
    proof = start(actor, case.pk, uuid4(), case.version, "Synthetic own account scope assessment")
    case.refresh_from_db()
    read(other, case)
    event = simulate_event(
        proof.pk,
        uuid4(),
        case.version,
        "passed",
        "Independent synthetic assessment of own account scope",
    )
    setattr(
        subject,
        field,
        "changed@example.invalid" if field == "email" else getattr(subject, field) + 1,
    )
    subject.save(update_fields=[field])
    with pytest.raises(ValidationError):
        receive_event(verifier, event)
    proof.refresh_from_db()
    case.refresh_from_db()
    assert proof.status == "pending" and case.scope_status == "unverified"
    assert not RightsProofEvent.objects.filter(proof=proof).exists()
