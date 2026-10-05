"""Independent exception review does not consume or lift any active restriction."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from test_processing_plans import REASON
from test_purpose_exception_preparation import prepared_exception
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.models import User
from apps.listings.models import Favorite
from apps.safety.erasure_execution import execute
from apps.safety.models import PurposeExceptionRead, PurposeExceptionReview, PurposeRestriction
from apps.safety.purpose_exceptions import propose, record

pytestmark = pytest.mark.django_db(transaction=True)


def ready(request, settings, monkeypatch):
    case, actor, subject, plan, favorite = prepared_exception(request, settings, monkeypatch)
    proposal = propose(
        actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, REASON
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(Permission.objects.get(codename="review_purpose_exception"))
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    return case, actor, subject, plan, favorite, proposal, reviewer, client


@pytest.mark.parametrize("outcome", ["approved", "rejected"])
def test_independent_inspection_required_and_decision_preserves_restriction(
    request, settings, monkeypatch, outcome
):
    case, actor, _, plan, favorite, proposal, reviewer, _ = ready(request, settings, monkeypatch)
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, proposal.pk, uuid4(), case.version, "review", REASON, outcome)
    with pytest.raises(PermissionDenied):
        record(actor, case.pk, proposal.pk, uuid4(), case.version, "review", REASON, outcome)
    key = uuid4()
    reading, body = record(reviewer, case.pk, proposal.pk, key, case.version, "inspect", REASON)
    assert body["basis"] == REASON and body["restrictions"][0]["mode"] == "restrict"
    assert (
        record(reviewer, case.pk, proposal.pk, key, case.version, "inspect", REASON)[0].pk
        == reading.pk
    )
    key = uuid4()
    review, body = record(
        reviewer, case.pk, proposal.pk, key, case.version, "review", REASON, outcome
    )
    assert body is None and review.outcome == outcome and review.consumed_action_id is None
    assert (
        record(reviewer, case.pk, proposal.pk, key, case.version, "review", REASON, outcome)[0].pk
        == review.pk
    )
    assert PurposeExceptionRead.objects.count() == PurposeExceptionReview.objects.count() == 1
    with pytest.raises(ValidationError, match="Purpose restricted"):
        execute(
            actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True
        )
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeRestriction.objects.get().active


def test_stale_measure_and_corrupt_proposal_deny_without_durable_read(
    request, settings, monkeypatch
):
    case, _, _, _, _, proposal, reviewer, _ = ready(request, settings, monkeypatch)
    measure = PurposeRestriction.objects.get()
    measure.version += 1
    measure.save(update_fields=["version"])
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, proposal.pk, uuid4(), case.version, "inspect", REASON)
    assert not PurposeExceptionRead.objects.exists()
    measure.version -= 1
    measure.save(update_fields=["version"])
    proposal.encrypted_scope = "damaged-encrypted-proposal"
    proposal.save(update_fields=["encrypted_scope"])
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, proposal.pk, uuid4(), case.version, "inspect", REASON)
    assert not PurposeExceptionRead.objects.exists() and not PurposeExceptionReview.objects.exists()


def test_private_review_http_requires_inspection_and_get_hides_grounds(
    request, settings, monkeypatch
):
    from django.urls import reverse

    case, _, _, _, favorite, proposal, reviewer, client = ready(request, settings, monkeypatch)
    path = reverse(
        "purpose_exception_review", kwargs={"case_id": case.pk, "proposal_id": proposal.pk}
    )
    assert client.get(path).status_code == 200
    payload = dict(
        key=uuid4(), version=case.version, operation="review", reason=REASON, outcome="approved"
    )
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    assert client.post(path, payload).status_code == 409
    inspection = payload | {"key": uuid4(), "operation": "inspect", "outcome": ""}
    response = client.post(path, inspection)
    assert response.status_code == 200 and response.context["body"]["basis"] == REASON
    assert client.post(path, payload).status_code == 200
    assert client.post(path, payload).status_code == 200
    page = client.get(path)
    assert page["Cache-Control"] == "private, no-store"
    assert REASON not in page.content.decode() and page.context["body"] is None
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeExceptionReview.objects.get().consumed_action_id is None
    reviewer.user_permissions.remove(Permission.objects.get(codename="review_purpose_exception"))
    assert client.get(path).status_code == 403
