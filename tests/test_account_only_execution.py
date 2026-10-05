"""Full own-account correction with independent review and real receipt acknowledgement."""

from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from test_privacy_release import fresh
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_account_linking import account
from test_rights_assignment import action
from test_rights_intake import data
from test_rights_verification import read

from apps.core.models import Agency, Person, User
from apps.safety.account_email_confirmation import start as start_confirmation
from apps.safety.crypto import unseal
from apps.safety.models import RightsRequest
from apps.safety.rectification_execution import execute, notify
from apps.safety.rectification_review import inspect, review
from apps.safety.rights_actions import act
from apps.safety.rights_rectification import preview, propose

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independent synthetic correction of own account data"


@pytest.mark.parametrize("email", [False, True])
@pytest.mark.parametrize("agency", [False, True])
def test_account_without_profile_review_receive_and_execute(request, settings, email, agency):
    request.getfixturevalue("directory")
    settings.RIGHTS_VERIFICATION_BACKEND = "simulator"
    public = Client()
    receipt = public.post("/en/safety/rights/", data(public, kind="rectify")).url
    case = RightsRequest.objects.get()
    original, staff = reviewer()
    original.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "manage_rights_assignment",
                "verify_rights_scope",
            ]
        )
    )
    original = User.objects.get(pk=original.pk)
    path, values = action(staff, case, "claim")
    assert staff.post(path, values).status_code == 302
    read(staff, case)
    subject = account()
    if agency:
        owned = Agency.objects.first()
        owned.owner = subject
        owned.save(update_fields=["owner"])
    profile_before = list(Person.objects.order_by("pk").values())
    path, values = action(staff, case, "link")
    assert staff.post(path, values | {"link_account_id": subject.pk}).status_code == 302
    independent = User.objects.get(username="fixture-v1-visitor")
    independent.mfa_enabled = True
    independent.mfa_version = 1
    independent.save(update_fields=["mfa_enabled", "mfa_version"])
    independent.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "verify_rights_scope",
                "review_rectification",
                "respond_rights_request",
            ]
        )
    )
    independent = User.objects.get(pk=independent.pk)
    other = Client()
    other.force_login(independent)
    session = other.session
    session["mfa_version"] = independent.mfa_version
    session.save()
    fresh(case, original, staff, independent, other)
    preview(original, case.pk, case.version, "Read own account source before proposal")
    changes = {"account": {"first_name": "Corrected own account"}}
    if email:
        changes["account"]["email"] = "confirmed-own-account@example.invalid"
    proposal = propose(
        original,
        case.pk,
        uuid4(),
        case.version,
        changes,
        REASON,
    )
    case.refresh_from_db()
    act(original, case.pk, uuid4(), case.version, "unassign", REASON)
    case.refresh_from_db()
    act(independent, case.pk, uuid4(), case.version, "claim", REASON)
    fresh(case, independent, other, original, staff)
    preview(independent, case.pk, case.version, "Read own account source before review")
    inspect(
        independent, case.pk, proposal.pk, case.version, "Read own account proposal before review"
    )
    review(independent, case.pk, proposal.pk, uuid4(), case.version, "approved", REASON)
    fresh(case, independent, other, original, staff)
    preview(independent, case.pk, case.version, "Read own account source before notification")
    inspect(
        independent,
        case.pk,
        proposal.pk,
        case.version,
        "Read approved own account proposal before notification",
    )
    confirmation = None
    if email:
        settings.ACCOUNT_CORRECTION_DELIVERY_BACKEND = "simulator"
        confirmation = start_confirmation(
            independent, case.pk, proposal.pk, uuid4(), case.version, REASON
        )
        destination = Client(enforce_csrf_checks=True)
        gateway = destination.get(urlsplit(unseal(confirmation.encrypted_delivery)["url"]).path)
        assert gateway.status_code == 302
        form_page = destination.get(gateway["Location"])
        confirmation.refresh_from_db()
        assert form_page.status_code == 200 and confirmation.confirmed_at is None
        assert destination.post(gateway["Location"], {"confirmed": "on"}).status_code == 403
        assert (
            destination.post(
                gateway["Location"],
                {"confirmed": "on", "csrfmiddlewaretoken": destination.cookies["csrftoken"].value},
            ).status_code
            == 200
        )
        fresh(case, independent, other, original, staff)
        preview(
            independent, case.pk, case.version, "Read account source after destination confirmation"
        )
        inspect(
            independent,
            case.pk,
            proposal.pk,
            case.version,
            "Read approved account correction after destination confirmation",
        )
    notification = notify(independent, case.pk, proposal.pk, uuid4(), case.version, REASON)
    assert (
        public.post(
            receipt + f"response/{notification.response_id}/acknowledge/", {"received": "yes"}
        ).status_code
        == 302
    )
    fresh(case, independent, other, original, staff)
    preview(independent, case.pk, case.version, "Read own account source before execution")
    inspect(
        independent,
        case.pk,
        proposal.pk,
        case.version,
        "Read received own account proposal before execution",
    )
    before = subject.email, subject.session_version, subject.password, subject.mfa_version
    key, version = uuid4(), case.version
    result = execute(independent, case.pk, proposal.pk, key, version, REASON)
    assert execute(independent, case.pk, proposal.pk, key, version, REASON).pk == result.pk
    subject.refresh_from_db()
    case.refresh_from_db()
    assert subject.first_name == "Corrected own account"
    if email:
        assert subject.email == changes["account"]["email"]
        assert subject.session_version == before[1] + 1
        confirmation.refresh_from_db()
        assert confirmation.consumed_at and not confirmation.encrypted_delivery
    else:
        assert (subject.email, subject.session_version) == before[:2]
    assert (subject.password, subject.mfa_version) == before[2:]
    assert list(Person.objects.order_by("pk").values()) == profile_before
    assert result.corrected_revision_id is None and result.resulting_rights_version is None
    assert not Person.objects.filter(subject=subject).exists()
    assert case.status == "reviewing" and case.scope_status == "unverified"
