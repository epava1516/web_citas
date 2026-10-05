"""Observed PostgreSQL waits cannot retain old reviewer permissions or duplicate follow-up."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_retention_reviews import prepared, values

from apps.core.models import User
from apps.safety.models import RetentionReview, RetentionReviewEvent
from apps.safety.retention_reviews import record

pytestmark = pytest.mark.django_db(transaction=True)


def test_permission_revoked_during_observed_wait_prevents_disclosure(
    request, settings, monkeypatch
):
    case, _, reviewer, _, _, _, plan, _ = prepared(request, settings, monkeypatch)
    review = RetentionReview.objects.filter(plan=plan).first()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=reviewer.pk)
            assert actor.has_perm("safety.review_retention")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                record(actor, review.pk, **values(case, review))
            except PermissionDenied:
                return "denied"
            return "disclosed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RetentionReview.objects.select_for_update().get(pk=review.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            reviewer.user_permissions.remove(Permission.objects.get(codename="review_retention"))
        assert future.result(timeout=15) == "denied"
    assert not RetentionReviewEvent.objects.exists()
    review.refresh_from_db()
    assert review.version == 1 and review.last_reviewed_at is None


def test_followup_same_key_waits_and_updates_once(request, settings, monkeypatch):
    case, _, reviewer, _, _, _, plan, _ = prepared(request, settings, monkeypatch)
    review = RetentionReview.objects.filter(plan=plan).first()
    record(reviewer, review.pk, **values(case, review))
    payload = values(case, review, "follow_up", key=uuid4())
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            return record(User.objects.get(pk=reviewer.pk), review.pk, **payload)[0].pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            RetentionReview.objects.select_for_update().get(pk=review.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            second = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not first.done() and not second.done()
        assert first.result(timeout=20) == second.result(timeout=20)
    review.refresh_from_db()
    assert review.version == 2 and review.next_review_on == payload["next_review_on"]
    assert RetentionReviewEvent.objects.filter(review=review, operation="follow_up").count() == 1
