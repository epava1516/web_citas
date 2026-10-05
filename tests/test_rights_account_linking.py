"""An account reference never grants profile scope or identity authority."""

import pytest
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import action
from test_rights_linking import ready

from apps.core.models import Person, User
from apps.safety.models import RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


def account():
    return User.objects.create_user(username="account-only", email="account-only@example.invalid")


def test_account_link_is_audited_idempotent_and_creates_no_profile(request):
    case, _, staff = ready(request)
    case.kind = "access"
    case.save(update_fields=["kind"])
    subject = account()
    path, data = action(staff, case, "link")
    data["link_account_id"] = subject.pk
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    before = case.encrypted_payload, case.received_at, case.initial_due_at
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    case.refresh_from_db()
    assert case.account_subject_id == case.reported_subject_id == subject.pk
    assert case.person_id is None and case.referenced_revision_id is None
    assert case.manager_version is None and case.reported_agency_id is None
    assert case.scope_status == "unverified" and not case.proofs.exists()
    assert not Person.objects.filter(subject=subject).exists()
    assert (case.encrypted_payload, case.received_at, case.initial_due_at) == before
    assert RightsAction.objects.filter(request=case, operation="link").count() == 1


def test_account_link_rejects_conflict_mixed_reference_erased_and_representation(request):
    case, reviewer, staff = ready(request)
    subject = account()
    path, data = action(staff, case, "link")
    assert staff.post(path, data | {"link_account_id": subject.pk}).status_code == 409
    case.kind = "rectify"
    case.save(update_fields=["kind"])
    assert staff.post(path, data | {"link_account_id": reviewer.pk}).status_code == 403
    person = Person.objects.first()
    assert (
        staff.post(
            path, data | {"link_account_id": subject.pk, "link_person_id": person.pk}
        ).status_code
        == 409
    )
    from django.utils import timezone

    subject.account_erased_at = timezone.now()
    subject.save(update_fields=["account_erased_at"])
    assert staff.post(path, data | {"link_account_id": subject.pk}).status_code == 409
    case.refresh_from_db()
    assert case.account_subject_id is None and case.person_id is None
    assert not RightsAction.objects.filter(request=case, operation="link").exists()
