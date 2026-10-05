"""Real restriction and erasure plans; a prepared exception never authorizes treatment."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.utils import timezone
from test_processing_execution import prepared
from test_processing_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_intake import data
from test_rights_verification import read

from apps.core.models import User
from apps.listings.models import Favorite
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute as erase
from apps.safety.erasure_inventory import prepare as inventory
from apps.safety.erasure_plans import record as erasure_plan
from apps.safety.models import (
    ErasureExecution,
    PurposeExceptionProposal,
    PurposeRestriction,
    RightsRequest,
)
from apps.safety.processing_execution import execute
from apps.safety.purpose_exceptions import propose
from apps.safety.rights_actions import act
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def prepared_exception(request, settings, monkeypatch):
    case, actor, subject, plan, favorite, independent = prepared(request, settings, monkeypatch)
    execute(actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True)
    before = set(RightsRequest.objects.values_list("pk", flat=True))
    public = Client()
    assert public.post("/en/safety/rights/", data(public, kind="erase")).status_code == 302
    erase_case = RightsRequest.objects.exclude(pk__in=before).get()
    executor = User.objects.get(pk=actor.pk)
    executor.user_permissions.add(Permission.objects.get(codename="review_purpose_exception"))
    executor = User.objects.get(pk=actor.pk)
    staff = Client()
    staff.force_login(executor)
    session = staff.session
    session["mfa_version"] = executor.mfa_version
    session.save()
    erase_case = act(executor, erase_case.pk, uuid4(), erase_case.version, "claim", REASON)
    read(staff, erase_case)
    erase_case = act(
        executor,
        erase_case.pk,
        uuid4(),
        erase_case.version,
        "link",
        REASON,
        link_account_id=subject.pk,
    )
    read(staff, erase_case)
    proof = start(executor, erase_case.pk, uuid4(), erase_case.version, REASON)
    erase_case.refresh_from_db()
    verifier = User.objects.get(username="fixture-v1-visitor")
    read(independent, erase_case)
    receive_event(verifier, simulate_event(proof.pk, uuid4(), erase_case.version, "passed", REASON))
    erase_case.refresh_from_db()
    read(staff, erase_case)
    snapshot = inventory(executor, erase_case.pk, uuid4(), erase_case.version, REASON)
    decisions = [
        dict(
            purpose=p,
            operation="erase" if p == "account_preferences" else "retain",
            basis=REASON,
            reason=REASON,
            scope=REASON,
            review_on=None
            if p == "account_preferences"
            else (timezone.localdate() + timedelta(days=7)).isoformat(),
        )
        for p in sorted({row["purpose"] for row in unseal(snapshot.encrypted_manifest)["entries"]})
    ]
    plan = erasure_plan(
        executor, erase_case.pk, snapshot.pk, uuid4(), erase_case.version, decisions
    )
    return erase_case, executor, subject, plan, favorite


def test_proposal_binds_real_measure_and_plan_without_granting_erasure(
    request, settings, monkeypatch
):
    case, actor, subject, plan, favorite = prepared_exception(request, settings, monkeypatch)
    values = dict(
        key=uuid4(),
        version=case.version,
        purposes=["account_preferences"],
        reason=REASON,
        basis="Synthetic grounds requiring an independent human review",
    )
    proposal = propose(actor, case.pk, plan.pk, **values)
    snapshot = unseal(proposal.encrypted_scope)
    assert snapshot["approved"] is False and snapshot["consumed"] is False
    assert snapshot["subject"] == str(subject.pk) and snapshot["plan"] == str(plan.pk)
    measure = PurposeRestriction.objects.get()
    assert snapshot["restrictions"][0]["id"] == measure.pk
    assert snapshot["restrictions"][0]["version"] == measure.version
    assert propose(actor, case.pk, plan.pk, **values).pk == proposal.pk
    with pytest.raises(ValidationError):
        propose(actor, case.pk, plan.pk, **(values | {"basis": REASON}))
    with pytest.raises(ValidationError, match="Purpose restricted"):
        erase(actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True)
    assert PurposeExceptionProposal.objects.count() == 1
    assert not ErasureExecution.objects.exists()
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    measure.refresh_from_db()
    case.refresh_from_db()
    assert measure.active and case.version == values["version"]


def test_proposal_denies_fresh_permission_and_changed_plan_without_side_effects(
    request, settings, monkeypatch
):
    case, actor, _, plan, _ = prepared_exception(request, settings, monkeypatch)
    permission = Permission.objects.get(codename="review_purpose_exception")
    actor.user_permissions.remove(permission)
    values = dict(
        key=uuid4(),
        version=case.version,
        purposes=["account_preferences"],
        reason=REASON,
        basis=REASON,
    )
    with pytest.raises(PermissionDenied):
        propose(actor, case.pk, plan.pk, **values)
    actor.user_permissions.add(permission)
    from apps.safety.crypto import seal

    body = unseal(plan.encrypted_decisions)
    body["decisions"][0]["basis"] = "Modified grounds after the original plan was signed"
    plan.encrypted_decisions = seal(body)
    plan.save(update_fields=["encrypted_decisions"])
    with pytest.raises(ValidationError):
        propose(actor, case.pk, plan.pk, **values)
    assert not PurposeExceptionProposal.objects.exists()


def test_private_http_preparation_replay_and_get_hide_grounds(request, settings, monkeypatch):
    from django.urls import reverse

    case, actor, _, plan, favorite = prepared_exception(request, settings, monkeypatch)
    staff = Client()
    staff.force_login(actor)
    session = staff.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    path = reverse("purpose_exception_prepare", kwargs={"case_id": case.pk, "plan_id": plan.pk})
    payload = dict(
        key=uuid4(),
        version=case.version,
        purposes=["account_preferences"],
        reason=REASON,
        basis="Private synthetic exception grounds for independent review",
    )
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    response = staff.post(path, payload)
    assert response.status_code == 200
    assert payload["basis"] not in response.content.decode()
    assert staff.post(path, payload).status_code == 200
    assert PurposeExceptionProposal.objects.count() == 1
    page = staff.get(path)
    assert payload["basis"] not in page.content.decode() and REASON not in page.content.decode()
    assert page["Cache-Control"] == "private, no-store"
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    actor.user_permissions.remove(Permission.objects.get(codename="review_purpose_exception"))
    assert staff.get(path).status_code == 403
