"""Account-purpose decisions revalidate state after an observed PostgreSQL wait."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_erasure_plans import BASIS, REASON, SCOPE
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import Favorite, Listing
from apps.safety.crypto import unseal
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record
from apps.safety.models import ErasureInventory, ErasurePlan, RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("operation", ["inventory", "plan"])
def test_account_erasure_revalidates_after_observed_subject_lock(
    request, settings, monkeypatch, operation
):
    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch, "erase")
    inventory = None
    decisions = None
    if operation == "plan":
        inventory = prepare(actor, case.pk, uuid4(), case.version, REASON)
        manifest = unseal(inventory.encrypted_manifest)
        decisions = [
            {
                "purpose": purpose,
                "operation": "review",
                "basis": BASIS,
                "reason": REASON,
                "scope": SCOPE,
                "review_on": (timezone.localdate() + timedelta(days=30)).isoformat(),
            }
            for purpose in sorted({row["purpose"] for row in manifest["entries"]})
        ]
    before = (
        RightsAction.objects.count(),
        ErasureInventory.objects.count(),
        ErasurePlan.objects.count(),
    )
    profiles = list(Person.objects.order_by("pk").values())
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            user = User.objects.get(pk=actor.pk)
            try:
                if operation == "inventory":
                    prepare(user, case.pk, uuid4(), case.version, REASON)
                else:
                    record(user, case.pk, inventory.pk, uuid4(), case.version, decisions)
            except ValidationError:
                return "denied"
            return "admitted"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=subject.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if operation == "inventory":
                locked.mfa_version += 1
                locked.save(update_fields=["mfa_version"])
            else:
                Favorite.objects.create(user=locked, listing=Listing.objects.first())
        assert future.result(timeout=15) == "denied"
    assert (
        RightsAction.objects.count(),
        ErasureInventory.objects.count(),
        ErasurePlan.objects.count(),
    ) == before
    assert list(Person.objects.order_by("pk").values()) == profiles
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_account_execution_same_key_after_observed_wait_has_one_effect(
    request, settings, monkeypatch
):
    from test_account_erasure_execution import prepared_erasure

    from apps.safety.erasure_execution import execute
    from apps.safety.models import ErasureExecution

    case, actor, _, subject, _, _, plan, purposes, _, _ = prepared_erasure(
        request, settings, monkeypatch
    )
    key = uuid4()
    pids = Queue()
    before = subject.session_version, subject.mfa_version, case.version

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
                purposes,
                REASON,
                True,
            ).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            User.objects.select_for_update().get(pk=subject.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            second = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not first.done() and not second.done()
        assert first.result(timeout=20) == second.result(timeout=20)
    subject.refresh_from_db()
    case.refresh_from_db()
    assert (subject.session_version, subject.mfa_version, case.version) == tuple(
        value + 1 for value in before
    )
    assert subject.account_erased_at and not subject.is_active
    assert ErasureExecution.objects.filter(plan=plan).count() == 1
    assert RightsAction.objects.filter(request=case, operation="erasure_execute").count() == 1


def test_account_execution_wait_rechecks_proof_without_deletion(request, settings, monkeypatch):
    from test_account_erasure_execution import prepared_erasure

    from apps.core.models import AccountToken, RecoveryCode
    from apps.safety.erasure_execution import execute
    from apps.safety.models import ErasureExecution

    case, actor, _, subject, _, _, plan, purposes, stored, _ = prepared_erasure(
        request, settings, monkeypatch
    )
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
                    case.version,
                    purposes,
                    REASON,
                    True,
                )
            except ValidationError:
                return "denied"
            return "admitted"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=subject.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            locked.mfa_version += 1
            locked.save(update_fields=["mfa_version"])
        assert future.result(timeout=15) == "denied"
    subject.refresh_from_db()
    stored.refresh_from_db()
    assert not subject.account_erased_at and subject.is_active
    assert stored.encrypted_payload and not stored.purged_at
    assert (
        AccountToken.objects.filter(user=subject).count()
        == RecoveryCode.objects.filter(user=subject).count()
        == Favorite.objects.filter(user=subject).count()
        == 1
    )
    assert not ErasureExecution.objects.exists()


def test_waiting_favorite_writer_cannot_recreate_erased_account_preferences(
    request, settings, monkeypatch
):
    import test_account_copy_races
    from django.test import Client
    from test_account_erasure_execution import prepared_erasure

    from apps.core.accounts import docs
    from apps.core.models import LegalAcceptance
    from apps.safety.erasure_execution import execute

    original_account = test_account_copy_races.account

    def active_account():
        user = original_account()
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at"])
        for document in docs("en"):
            LegalAcceptance.objects.create(user=user, document=document, action="register")
        return user

    monkeypatch.setattr(test_account_copy_races, "account", active_account)
    case, actor, _, subject, _, _, plan, purposes, _, _ = prepared_erasure(
        request, settings, monkeypatch
    )
    client = Client()
    client.force_login(subject)
    assert client.get("/en/favorites/").status_code == 200
    target = Listing.objects.get(person__individual__username="fixture-v1-individual")
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            return client.post(f"/en/listing/{target.pk}/favorite/").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            User.objects.select_for_update().get(pk=subject.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
        assert future.result(timeout=15) == 409
    assert not Favorite.objects.filter(user=subject).exists()
