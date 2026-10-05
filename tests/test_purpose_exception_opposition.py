"""A scoped erasure exception must preserve a real opposition cessation ledger."""

import pytest
from test_purpose_exception_consumption import approved, payload
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Favorite
from apps.safety.erasure_execution import execute
from apps.safety.models import PurposeExceptionReview, PurposeRestriction

pytestmark = pytest.mark.django_db(transaction=True)


def test_opposition_cessation_exception_consumes_without_resuming_ordinary_processing(
    request, settings, monkeypatch
):
    import test_processing_execution
    import test_processing_review

    original_account = test_processing_review.prepared_account
    original_plan = test_processing_execution.prepare

    def opposition_account(request, settings, monkeypatch, kind):
        return original_account(request, settings, monkeypatch, "object")

    def cessation_plan(user, case_id, key, version, reason, decisions):
        for item in decisions:
            if item["purpose"] == "account_preferences":
                item["operation"] = "cease"
        return original_plan(user, case_id, key, version, reason, decisions)

    monkeypatch.setattr(test_processing_review, "prepared_account", opposition_account)
    monkeypatch.setattr(test_processing_execution, "prepare", cessation_plan)
    case, actor, subject, plan, favorite, proposal, _, _ = approved(request, settings, monkeypatch)
    measure = PurposeRestriction.objects.select_related("execution__action__request").get()
    assert measure.mode == "cease" and measure.execution.action.request.kind == "object"
    result = execute(actor, case.pk, plan.pk, **payload(case, proposal))
    assert (
        PurposeExceptionReview.objects.get(proposal=proposal).consumed_action_id == result.action_id
    )
    assert not Favorite.objects.filter(pk=favorite.pk).exists()
    measure.refresh_from_db()
    subject.refresh_from_db()
    assert measure.active and measure.mode == "cease" and subject.is_active
