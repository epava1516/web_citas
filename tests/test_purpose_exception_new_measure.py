"""A full second measure workflow invalidates a waiting erasure exception."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from test_photo_reuse_races import observe_blocked
from test_processing_plans import REASON, decisions
from test_purpose_exception_consumption import approved, payload
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_intake import data
from test_rights_verification import read

from apps.core.models import User
from apps.listings.models import Favorite
from apps.safety.erasure_execution import execute as erase
from apps.safety.models import (
    ErasureExecution,
    PurposeExceptionReview,
    PurposeRestriction,
    RightsAction,
    RightsRequest,
)
from apps.safety.processing_execution import execute
from apps.safety.processing_plans import prepare
from apps.safety.processing_review import record
from apps.safety.rights_actions import act
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def private_client(user):
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    return client


def second_measure(actor, reviewer, subject):
    before = set(RightsRequest.objects.values_list("pk", flat=True))
    public = Client()
    assert public.post("/en/safety/rights/", data(public, kind="restriction")).status_code == 302
    case = RightsRequest.objects.exclude(pk__in=before).get()
    staff = private_client(actor)
    case = act(actor, case.pk, uuid4(), case.version, "claim", REASON)
    read(staff, case)
    case = act(actor, case.pk, uuid4(), case.version, "link", REASON, link_account_id=subject.pk)
    read(staff, case)
    proof = start(actor, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    independent = private_client(reviewer)
    read(independent, case)
    receive_event(reviewer, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(staff, case)
    values = decisions(case)
    for item in values:
        item["operation"] = "restrict" if item["purpose"] == "account_preferences" else "continue"
    plan = prepare(actor, case.pk, uuid4(), case.version, REASON, values)
    read(independent, case)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "approved")
    result = execute(
        actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True
    )
    return PurposeRestriction.objects.get(execution=result)


def test_new_real_measure_committed_during_case_wait_invalidates_old_exception(
    request, settings, monkeypatch
):
    case, actor, subject, plan, favorite, proposal, reviewer, _ = approved(
        request, settings, monkeypatch
    )
    values = payload(case, proposal)
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                erase(User.objects.get(pk=actor.pk), case.pk, plan.pk, **values)
                return "executed"
            except (PermissionDenied, ValidationError):
                return "denied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            measure = second_measure(
                User.objects.get(pk=actor.pk), User.objects.get(pk=reviewer.pk), subject
            )
            assert measure.subject_id == subject.pk and measure.active
            assert PurposeRestriction.objects.filter(subject=subject, active=True).count() == 2
            assert not future.done()
        assert future.result(timeout=30) == "denied"
    assert PurposeExceptionReview.objects.get(proposal=proposal).consumed_action_id is None
    assert not ErasureExecution.objects.exists()
    assert not RightsAction.objects.filter(request=case, operation="erasure_execute").exists()
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeRestriction.objects.filter(subject=subject, active=True).count() == 2
