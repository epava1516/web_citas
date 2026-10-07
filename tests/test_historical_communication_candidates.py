"""Historical role evidence is accounted for without granting delivery authority."""

from uuid import uuid4

import pytest
import test_erasure_execution as fixture
from django.core.exceptions import ValidationError
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person, RepresentationAction, User
from apps.safety.communication_notices import authorized_targets
from apps.safety.erasure_execution import execute
from apps.safety.recipient_assessments import targets, validate_decisions
from apps.safety.rights_communications import snapshot
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


def test_previous_manager_is_reviewed_candidate_but_not_authorized_delivery(
    request, settings, monkeypatch
):
    original = fixture.prepared
    evidence = {}

    def with_retained_history(*args, **kwargs):
        result = original(*args, **kwargs)
        person = result[5]
        former = User.objects.create_user(username="synthetic-former-manager", email="former@example.invalid")
        unrelated = User.objects.create_user(username="synthetic-unrelated-manager", email="unrelated@example.invalid")
        row = RepresentationAction.objects.create(
            person=person, subject=person.subject, manager_version=person.manager_version,
            action="transfer", previous_manager_kind="individual",
            previous_manager_id=str(former.pk),
        )
        other = Person.objects.exclude(pk=person.pk).first()
        assert other is not None
        RepresentationAction.objects.create(
            person=other, subject=other.subject, manager_version=other.manager_version,
            action="transfer", previous_manager_kind="individual",
            previous_manager_id=str(unrelated.pk),
        )
        evidence.update(former=former.pk, unrelated=unrelated.pk, record=row.pk)
        return result

    monkeypatch.setattr(fixture, "prepared", with_retained_history)
    case, actor, _, _, _, _, plan, _, _, _ = fixture.plan_fixture(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, fixture.PURPOSES, fixture.REASON, True)
    case.refresh_from_db()
    with transaction.atomic():
        current, person, listing = locked_case(case.pk, lock_listing=True, allow_erased_account=True)
        source = snapshot(current, person, listing, execution.pk)
        actual_targets = authorized_targets(current, person)
    historical = next(c for c in source["candidates"] if c["reference"] == str(evidence["former"]) and c["kind"] == "individual")
    assert {"basis": "previous_representation", "record": str(evidence["record"])} in historical["evidence"]
    assert not any(c["reference"] == str(evidence["unrelated"]) for c in source["candidates"])
    assert not any(t["recipient"] == str(evidence["former"]) for t in actual_targets)
    assert source["notice_targets"] == actual_targets
    assert "historical_recipient_contact_authorization_and_delivery" in source["pending"]
    assert source["complete"] is False and case.status != "resolved"
    required = targets(source)
    decisions = {token: {"outcome": "pending", "reason": fixture.REASON, "evidence": fixture.REASON} for token in required}
    token = next(token for token, candidate in required.items() if candidate == historical)
    assert validate_decisions(source, decisions) == decisions
    incomplete = dict(decisions)
    incomplete.pop(token)
    with pytest.raises(ValidationError, match="Assess every"):
        validate_decisions(source, incomplete)
    false_delivery = dict(decisions)
    false_delivery[token] = decisions[token] | {"outcome": "communicated"}
    with pytest.raises(ValidationError, match="Recorded recipient receipt"):
        validate_decisions(source, false_delivery)
