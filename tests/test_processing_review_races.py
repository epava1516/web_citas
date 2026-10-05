"""Observe actual PostgreSQL lock waits before mutating review authority or source."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_processing_plans import REASON
from test_processing_review import prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.listings.models import Favorite, Listing
from apps.safety.models import ProcessingPlanRead, ProcessingPlanReview, ProcessingPurposePlan
from apps.safety.processing_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("change", ["permission", "source", "proof"])
def test_inspection_revalidates_after_observed_plan_wait(request, settings, monkeypatch, change):
    case, _, subject, plan, reviewer, _ = prepared(request, settings, monkeypatch)
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=reviewer.pk)
            assert actor.has_perm("safety.review_processing_plan")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                record(actor, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
            except (PermissionDenied, ValidationError):
                return "denied"
            return "disclosed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            if change == "source":
                User.objects.select_for_update().get(pk=subject.pk)
            else:
                ProcessingPurposePlan.objects.select_for_update().get(pk=plan.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if change == "permission":
                reviewer.user_permissions.remove(
                    Permission.objects.get(codename="review_processing_plan")
                )
            elif change == "source":
                Favorite.objects.create(user=subject, listing=Listing.objects.first())
            else:
                plan.proof.status = "failed"
                plan.proof.save(update_fields=["status"])
        assert future.result(timeout=20) == "denied"
    assert not ProcessingPlanRead.objects.exists() and not ProcessingPlanReview.objects.exists()


def test_same_review_key_waits_and_records_once(request, settings, monkeypatch):
    case, _, _, plan, reviewer, _ = prepared(request, settings, monkeypatch)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
    key = uuid4()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            result, _ = record(
                User.objects.get(pk=reviewer.pk),
                case.pk,
                plan.pk,
                key,
                case.version,
                "review",
                REASON,
                "approved",
            )
            return result.pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            ProcessingPurposePlan.objects.select_for_update().get(pk=plan.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            second = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not first.done() and not second.done()
        assert first.result(timeout=20) == second.result(timeout=20)
    assert ProcessingPlanReview.objects.count() == 1
