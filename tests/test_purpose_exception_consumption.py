"""Approved exceptions allow one exact erasure; restriction and audit remain durable."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.test import Client
from test_processing_plans import REASON
from test_purpose_exception_review import ready
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Favorite
from apps.safety.erasure_execution import execute
from apps.safety.models import (
    ErasureExecution,
    PurposeExceptionReview,
    PurposeRestriction,
    RightsAction,
)
from apps.safety.purpose_exceptions import record

pytestmark = pytest.mark.django_db(transaction=True)


def approved(request, settings, monkeypatch):
    values = ready(request, settings, monkeypatch)
    case, _, _, _, _, proposal, reviewer, _ = values
    record(reviewer, case.pk, proposal.pk, uuid4(), case.version, "inspect", REASON)
    record(reviewer, case.pk, proposal.pk, uuid4(), case.version, "review", REASON, "approved")
    return values


def payload(case, proposal):
    return dict(
        key=uuid4(),
        version=case.version,
        purposes=["account_preferences"],
        reason=REASON,
        confirmed=True,
        exception_id=proposal.pk,
    )


def test_exact_consumption_and_replay_preserve_active_measure(request, settings, monkeypatch):
    case, actor, subject, plan, favorite, proposal, _, _ = approved(request, settings, monkeypatch)
    data = payload(case, proposal)
    result = execute(actor, case.pk, plan.pk, **data)
    review = PurposeExceptionReview.objects.get(proposal=proposal)
    assert review.consumed_action_id == result.action_id
    assert not Favorite.objects.filter(pk=favorite.pk).exists()
    assert execute(actor, case.pk, plan.pk, **data).pk == result.pk
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **(data | {"key": uuid4()}))
    assert ErasureExecution.objects.count() == 1
    measure = PurposeRestriction.objects.get()
    assert measure.active and measure.version == 1
    subject.refresh_from_db()
    own = Client()
    own.force_login(subject)
    session = own.session
    session["account_version"] = subject.session_version
    session.save()
    assert own.get("/en/favorites/").status_code == 409


def test_failure_after_consumption_rolls_back_use_action_and_deletion(
    request, settings, monkeypatch
):
    case, actor, _, plan, favorite, proposal, _, _ = approved(request, settings, monkeypatch)
    original = QuerySet.delete

    def fail_preferences(query):
        if query.model is Favorite:
            raise ValidationError("Synthetic failure after exception consumption")
        return original(query)

    monkeypatch.setattr(QuerySet, "delete", fail_preferences)
    with pytest.raises(ValidationError, match="Synthetic failure"):
        execute(actor, case.pk, plan.pk, **payload(case, proposal))
    assert PurposeExceptionReview.objects.get(proposal=proposal).consumed_action_id is None
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert not ErasureExecution.objects.exists()
    assert not RightsAction.objects.filter(request=case, operation="erasure_execute").exists()


@pytest.mark.parametrize("change", ["measure", "approval"])
def test_changed_measure_or_approval_signature_denies_without_consumption(
    request, settings, monkeypatch, change
):
    case, actor, _, plan, favorite, proposal, _, _ = approved(request, settings, monkeypatch)
    if change == "measure":
        measure = PurposeRestriction.objects.get()
        measure.version += 1
        measure.save(update_fields=["version"])
    else:
        review = PurposeExceptionReview.objects.get(proposal=proposal)
        review.action.payload_digest = "0" * 64
        review.action.save(update_fields=["payload_digest"])
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **payload(case, proposal))
    assert PurposeExceptionReview.objects.get(proposal=proposal).consumed_action_id is None
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert not ErasureExecution.objects.exists()
