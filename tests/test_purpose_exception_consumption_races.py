"""Observed PostgreSQL waits: a consumed exception cannot retain stale authority."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone
from test_photo_reuse_races import observe_blocked
from test_processing_plans import REASON
from test_purpose_exception_consumption import approved, payload
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.listings.models import Favorite
from apps.safety.erasure_execution import execute
from apps.safety.models import (
    ErasureExecution,
    PurposeExceptionReview,
    PurposeRestriction,
    RightsRequest,
)
from apps.safety.purpose_calendar import record as follow_up

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("scenario", ["replay", "conflict", "revoked", "follow_up"])
def test_waiting_consumers_revalidate_and_consume_once(request, settings, monkeypatch, scenario):
    case, actor, _, plan, favorite, proposal, reviewer, _ = approved(request, settings, monkeypatch)
    values = payload(case, proposal)
    second = values if scenario != "conflict" else values | {"key": uuid4()}
    pids = Queue()

    def attempt(data):
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            assert user.has_perm("safety.review_purpose_exception")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                return execute(user, case.pk, plan.pk, **data).pk
            except (PermissionDenied, ValidationError):
                return "denied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt, values)
            observe_blocked(pids.get(timeout=5), holder)
            other = pool.submit(attempt, second)
            observe_blocked(pids.get(timeout=5), holder)
            assert not first.done() and not other.done()
            if scenario == "revoked":
                actor.user_permissions.remove(
                    Permission.objects.get(codename="review_purpose_exception")
                )
            elif scenario == "follow_up":
                reviewer.user_permissions.add(
                    Permission.objects.get(codename="review_purpose_calendar")
                )
                reviewer = User.objects.get(pk=reviewer.pk)
                measure = PurposeRestriction.objects.select_related(
                    "execution__action__request"
                ).get()
                original = measure.execution.action.request
                follow_up(
                    reviewer,
                    measure.pk,
                    uuid4(),
                    measure.version,
                    original.version,
                    "follow_up",
                    REASON,
                    timezone.localdate() + timedelta(days=7),
                )
        results = [first.result(timeout=30), other.result(timeout=30)]
    review = PurposeExceptionReview.objects.get(proposal=proposal)
    if scenario in {"revoked", "follow_up"}:
        assert results == ["denied", "denied"]
        assert review.consumed_action_id is None and not ErasureExecution.objects.exists()
        assert Favorite.objects.filter(pk=favorite.pk).exists()
    else:
        assert ErasureExecution.objects.count() == 1 and review.consumed_action_id
        assert not Favorite.objects.filter(pk=favorite.pk).exists()
        if scenario == "replay":
            assert results[0] == results[1]
        else:
            assert results.count("denied") == 1
    assert PurposeRestriction.objects.get().active
