"""PostgreSQL scope locks make restriction enforcement atomic with ordinary routes."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection, connections, transaction
from django.test import Client
from django.urls import reverse
from test_photo_reuse_races import observe_blocked
from test_processing_execution import prepared
from test_processing_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.listings.models import Favorite
from apps.safety.models import ProcessingExecution, ProcessingPurposePlan, PurposeRestriction
from apps.safety.processing_execution import execute

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("operation", ["index", "add", "remove"])
def test_favorite_route_waiting_on_account_observes_new_restriction(
    request, settings, monkeypatch, operation
):
    case, actor, subject, plan, favorite, _ = prepared(request, settings, monkeypatch)
    own = Client()
    own.force_login(subject)
    own.get(reverse("favorites"))
    paths = {
        "index": reverse("favorites"),
        "add": reverse("favorite_add", kwargs={"listing_id": favorite.listing_id}),
        "remove": reverse("favorite_remove", kwargs={"favorite_id": favorite.pk}),
    }
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            client = Client()
            client.cookies = own.cookies.copy()
            response = (
                client.get(paths[operation])
                if operation == "index"
                else client.post(paths[operation])
            )
            return response.status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            User.objects.select_for_update(no_key=True).get(pk=subject.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            execute(
                actor,
                case.pk,
                plan.pk,
                uuid4(),
                case.version,
                ["account_preferences"],
                REASON,
                True,
            )
        assert future.result(timeout=20) == 409
    assert (
        Favorite.objects.filter(pk=favorite.pk).exists() and PurposeRestriction.objects.count() == 1
    )


def test_execution_replay_after_wait_is_unique(request, settings, monkeypatch):
    case, actor, _, plan, _, _ = prepared(request, settings, monkeypatch)
    key = uuid4()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            return execute(
                User.objects.get(pk=actor.pk),
                case.pk,
                plan.pk,
                key,
                case.version,
                ["account_preferences"],
                REASON,
                True,
            ).pk
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
        assert first.result(timeout=20) == second.result(timeout=20)
    assert ProcessingExecution.objects.count() == PurposeRestriction.objects.count() == 1


def test_permission_revoked_during_execution_wait_rolls_back(request, settings, monkeypatch):
    case, actor, _, plan, _, _ = prepared(request, settings, monkeypatch)
    pids = Queue()
    version = case.version

    def attempt():
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            assert user.has_perm("safety.execute_rights_request")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                execute(
                    user, case.pk, plan.pk, uuid4(), version, ["account_preferences"], REASON, True
                )
            except PermissionDenied:
                return "denied"
            return "executed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            ProcessingPurposePlan.objects.select_for_update().get(pk=plan.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            actor.user_permissions.remove(Permission.objects.get(codename="execute_rights_request"))
        assert future.result(timeout=20) == "denied"
    case.refresh_from_db()
    assert (
        case.version == version
        and not ProcessingExecution.objects.exists()
        and not PurposeRestriction.objects.exists()
    )


def test_proof_revoked_while_waiting_for_approval_row_prevents_execution(
    request, settings, monkeypatch
):
    from django.core.exceptions import ValidationError

    from apps.safety.models import ProcessingPlanReview

    case, actor, _, plan, _, _ = prepared(request, settings, monkeypatch)
    version = case.version
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                execute(
                    User.objects.get(pk=actor.pk),
                    case.pk,
                    plan.pk,
                    uuid4(),
                    version,
                    ["account_preferences"],
                    REASON,
                    True,
                )
            except ValidationError:
                return "denied"
            return "executed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            ProcessingPlanReview.objects.select_for_update().get(plan=plan)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            plan.proof.status = "failed"
            plan.proof.save(update_fields=["status"])
        assert future.result(timeout=20) == "denied"
    case.refresh_from_db()
    assert (
        case.version == version
        and not ProcessingExecution.objects.exists()
        and not PurposeRestriction.objects.exists()
    )
