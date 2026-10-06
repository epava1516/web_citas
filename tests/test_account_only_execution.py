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
def test_account_without_profile_review_receive_and_execute(
    request,
    settings,
    email,
    agency,
    recipient_flow=False,
    final_flow=False,
    pending=True,
    race=False,
):
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

    if recipient_flow:
        from django.core.exceptions import PermissionDenied, ValidationError
        from django.urls import reverse

        from apps.safety import recipient_assessments, recipient_review
        from apps.safety.models import RightsAction, RightsRectificationRecipientInventory

        independent.user_permissions.add(
            Permission.objects.get(codename="manage_rights_assignment")
        )
        independent = User.objects.get(pk=independent.pk)
        fresh(case, independent, other, original, staff)
        recipient_path = reverse("rectification_recipients", args=[case.pk, result.pk])
        before_actions = RightsAction.objects.count()
        assert other.get(recipient_path).status_code == 200
        assert RightsAction.objects.count() == before_actions
        inventory_key = uuid4()
        values = {"key": inventory_key, "version": case.version, "purpose": REASON}
        posted = other.post(recipient_path, values)
        assert posted.status_code == 200, posted.content.decode()
        inventory = RightsRectificationRecipientInventory.objects.get(action__key=inventory_key)
        assert other.post(recipient_path, values).status_code == 200
        recipients = posted.context["inventory"]
        assert recipients["person"] is None
        assert recipients["account_subject"] == str(subject.pk)
        assert recipients["pending"] and not recipients["complete"]
        assert "Corrected own account" not in str(recipients)
        assert before[2] not in str(recipients)
        assert all(item["kind"] == "account" for item in recipients["candidates"])
        assert not Person.objects.filter(subject=subject).exists()
        assessment_path = reverse("recipient_assessment", args=[case.pk, inventory.pk])
        assert other.get(assessment_path).status_code == 200
        inspected = other.post(
            assessment_path,
            {
                "operation": "inspect",
                "version": case.version,
                "key": uuid4(),
                "purpose": REASON,
            },
        )
        assert inspected.status_code == 200, inspected.content.decode()
        assessments = {
            target: {
                "outcome": "pending" if pending else "not_disclosed",
                "reason": REASON,
                "evidence": "Synthetic concrete recipient evidence awaiting scope resolution",
            }
            for target in recipient_assessments.targets(recipients)
        }
        assessment = recipient_assessments.propose(
            independent, case.pk, inventory.pk, uuid4(), case.version, assessments
        )
        case.refresh_from_db()
        assert case.status == "reviewing"
        original.user_permissions.add(
            *Permission.objects.filter(
                codename__in=["review_recipient_assessment", "review_rectification"]
            )
        )
        original = User.objects.get(pk=original.pk)
        act(independent, case.pk, uuid4(), case.version, "unassign", REASON)
        case.refresh_from_db()
        act(original, case.pk, uuid4(), case.version, "claim", REASON)
        fresh(case, original, staff, independent, other)
        with pytest.raises(PermissionDenied):
            recipient_review.inspect(independent, case.pk, assessment.pk, case.version, REASON)
        data_read, decisions_read = recipient_review.inspect(
            original, case.pk, assessment.pk, case.version, REASON
        )
        assert data_read["account_subject"] == str(subject.pk)
        assert decisions_read == assessments
        previous_name = subject.first_name
        subject.first_name = "Changed after executed correction"
        subject.save(update_fields=["first_name"])
        with pytest.raises(ValidationError):
            recipient_review.inspect(original, case.pk, assessment.pk, case.version, REASON)
        subject.first_name = previous_name
        subject.save(update_fields=["first_name"])
        decision = recipient_review.review(
            original, case.pk, assessment.pk, uuid4(), case.version, "accepted", REASON
        )
        assert decision.assessment_id == assessment.pk
        case.refresh_from_db()
        assert case.status == "reviewing" and case.scope_status == "unverified"
        assert list(Person.objects.order_by("pk").values()) == profile_before
        if final_flow:
            from apps.safety import rectification_final
            from apps.safety.models import RightsAction, RightsNotice, RightsResponse

            original.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
            original = User.objects.get(pk=original.pk)
            fresh(case, original, staff, independent, other)
            read(other, case)
            text = "La rectificación solicitada ha sido aplicada y revisada. Consulta el resultado privado. / The requested correction has been applied and reviewed."
            draft_key = uuid4()
            final_path = reverse("rectification_final", args=[case.pk])
            metadata = staff.get(final_path)
            assert metadata.status_code == 200
            assert metadata["Cache-Control"] == "private, no-store"
            submitted = {
                "key": draft_key,
                "version": case.version,
                "responses": case.response_version,
                "operation": "prepare",
                "recipient_review": decision.pk,
                "reason": REASON,
                "text": text,
                "confirmed": True,
            }
            prepared_response = staff.post(final_path, submitted)
            assert prepared_response.status_code == 302, prepared_response.content.decode()
            draft = RightsAction.objects.get(key=draft_key)
            assert text.encode() not in staff.get(final_path).content
            assert (
                rectification_final.prepare(
                    original,
                    case.pk,
                    case.version,
                    case.response_version,
                    decision.pk,
                    draft_key,
                    REASON,
                    text,
                    True,
                ).pk
                == draft.pk
            )
            with pytest.raises(PermissionDenied):
                rectification_final.inspect(
                    original, case.pk, case.version, case.response_version, draft.pk, REASON
                )
            inspected_response = other.post(
                final_path,
                {
                    "operation": "inspect",
                    "key": uuid4(),
                    "version": case.version,
                    "responses": case.response_version,
                    "draft": draft.pk,
                    "purpose": REASON,
                },
            )
            assert inspected_response.status_code == 200, inspected_response.content.decode()
            assert text.encode() in inspected_response.content
            inspected = inspected_response.context["material"]
            audited = RightsAction.objects.get(
                pk=inspected_response.context["form"].initial["read"]
            )
            assert inspected["evidence"]["pending"] is pending
            assert text.encode() not in other.get(final_path).content
            review_key = uuid4()
            reviewed_response = other.post(
                final_path,
                {
                    "operation": "review",
                    "key": review_key,
                    "version": case.version,
                    "responses": case.response_version,
                    "draft": draft.pk,
                    "read": audited.pk,
                    "outcome": "approved",
                    "reason": REASON,
                },
            )
            assert reviewed_response.status_code == 302, reviewed_response.content.decode()
            approved = RightsAction.objects.get(key=review_key)
            version, responses = case.version, case.response_version
            counts = RightsResponse.objects.count(), RightsNotice.objects.count()
            closure_key = uuid4()
            close_data = {
                "operation": "close",
                "key": closure_key,
                "version": version,
                "responses": responses,
                "review": approved.pk,
            }
            before_name = subject.first_name
            subject.first_name = "Changed after final independent review"
            subject.save(update_fields=["first_name"])
            assert staff.post(final_path, close_data).status_code == 409
            subject.first_name = before_name
            subject.save(update_fields=["first_name"])
            old_session_version = independent.session_version
            independent.session_version += 1
            independent.save(update_fields=["session_version"])
            assert staff.post(final_path, close_data).status_code == 403
            independent.session_version = old_session_version
            independent.save(update_fields=["session_version"])
            audit_cipher = audited.encrypted_reason
            audited.encrypted_reason = "damaged encrypted audited read"
            audited.save(update_fields=["encrypted_reason"])
            assert staff.post(final_path, close_data).status_code == 409
            audited.encrypted_reason = audit_cipher
            audited.save(update_fields=["encrypted_reason"])
            if pending:
                assert staff.post(final_path, close_data).status_code == 409
                with pytest.raises(ValidationError, match="Unresolved recipient"):
                    rectification_final.close(
                        original, case.pk, version, responses, approved.pk, closure_key
                    )
                case.refresh_from_db()
                assert case.status == "reviewing" and case.version == version
                assert (RightsResponse.objects.count(), RightsNotice.objects.count()) == counts
            else:
                if race:
                    from concurrent.futures import ThreadPoolExecutor
                    from threading import Barrier

                    from django.db import close_old_connections, connections

                    barrier = Barrier(2)

                    def concurrently_close():
                        close_old_connections()
                        try:
                            participant = User.objects.get(pk=original.pk)
                            barrier.wait(timeout=20)
                            return rectification_final.close(
                                participant, case.pk, version, responses, approved.pk, closure_key
                            ).pk
                        finally:
                            connections.close_all()

                    with ThreadPoolExecutor(max_workers=2) as pool:
                        futures = [pool.submit(concurrently_close) for _ in range(2)]
                        results = [future.result(timeout=40) for future in futures]
                    assert results[0] == results[1]
                    with pytest.raises(ValidationError):
                        rectification_final.close(
                            original, case.pk, version, responses, approved.pk, uuid4()
                        )
                issued = staff.post(final_path, close_data)
                assert issued.status_code == 302, issued.content.decode()
                result = RightsResponse.objects.get(key=closure_key)
                assert (
                    rectification_final.close(
                        original, case.pk, version, responses, approved.pk, closure_key
                    ).pk
                    == result.pk
                )
                case.refresh_from_db()
                assert case.status == "resolved" and case.version == version + 1
                assert case.response_version == responses + 1 and result.kind == "rectify_complete"
                assert RightsResponse.objects.count() == counts[0] + 1
                assert RightsNotice.objects.count() == counts[1] + 1
                assert unseal(result.encrypted_response)["simulation"] is True
                assert list(Person.objects.order_by("pk").values()) == profile_before


@pytest.mark.parametrize("email", [False, True])
def test_account_recipient_flow_does_not_require_or_modify_owned_agency_profiles(
    request, settings, email
):
    test_account_without_profile_review_receive_and_execute(
        request, settings, email=email, agency=True, recipient_flow=True
    )


@pytest.mark.parametrize("pending", [True, False])
def test_account_final_rectification_review_and_atomic_close(request, settings, pending):
    test_account_without_profile_review_receive_and_execute(
        request,
        settings,
        email=False,
        agency=True,
        recipient_flow=True,
        final_flow=True,
        pending=pending,
    )


def test_account_final_rectification_concurrent_close(request, settings):
    test_account_without_profile_review_receive_and_execute(
        request,
        settings,
        email=False,
        agency=True,
        recipient_flow=True,
        final_flow=True,
        pending=False,
        race=True,
    )
