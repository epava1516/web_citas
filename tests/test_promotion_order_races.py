import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, connection, connections, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup

from apps.catalog.promotion_order_models import (
    PromotionEntitlement,
    PromotionOrder,
    PromotionOrderAudit,
    PromotionPaymentEvent,
)
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.core.models import Person, User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("operation", ["create", "event", "replay"])
@pytest.mark.parametrize("change", ["session", "mfa", "management"])
def test_observed_person_lock_revocation_denies_new_operation_or_replay(
    request, settings, operation, change
):
    user, listing, version, credentials = setup(request, settings)
    key = uuid.uuid4()
    payload = signature = None
    if operation != "create":
        order = create_order(user, listing.pk, version.pk, key, **credentials)
        payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid.uuid4())
        if operation == "replay":
            receive_event(user, payload, signature, **credentials)
    models = [PromotionOrder, PromotionPaymentEvent, PromotionEntitlement, PromotionOrderAudit]
    counts = [model.objects.count() for model in models]
    ready = Event()
    backend = {}

    def execute():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend["pid"] = cursor.fetchone()[0]
            current = User.objects.get(pk=user.pk)
            ready.set()
            try:
                if operation == "create":
                    create_order(current, listing.pk, version.pk, key, **credentials)
                else:
                    receive_event(current, payload, signature, **credentials)
            except PermissionDenied:
                return "denied"
            return "allowed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Person.objects.select_for_update().get(pk=listing.person_id)
            future = pool.submit(execute)
            assert ready.wait(5)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                own_pid = cursor.fetchone()[0]
                deadline = time.monotonic() + 5
                blocked = False
                while time.monotonic() < deadline:
                    cursor.execute("SELECT pg_blocking_pids(%s)", [backend["pid"]])
                    blocked = own_pid in cursor.fetchone()[0]
                    if blocked:
                        break
                    time.sleep(0.02)
            assert blocked and not future.done()
            if change == "management":
                Person.objects.filter(pk=listing.person_id).update(
                    manager_version=listing.person.manager_version + 1
                )
            else:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=user.pk).update(**{field: getattr(user, field) + 1})
        assert future.result(10) == "denied"
    assert [model.objects.count() for model in models] == counts


def test_concurrent_identical_payment_event_has_one_entitlement_and_one_event(request, settings):
    user, listing, version, credentials = setup(request, settings)
    order = create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid.uuid4())
    barrier = Barrier(2)

    def execute():
        close_old_connections()
        try:
            current = User.objects.get(pk=user.pk)
            barrier.wait(5)
            return receive_event(current, payload, signature, **credentials).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: execute(), range(2)))
    assert results == [order.pk, order.pk]
    assert PromotionPaymentEvent.objects.count() == 1 and PromotionEntitlement.objects.count() == 1
    assert PromotionOrderAudit.objects.filter(operation="synthetic_succeeded").count() == 1


def test_audit_failure_rolls_back_order_and_payment_grant(request, settings, monkeypatch):
    user, listing, version, credentials = setup(request, settings)
    order = create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid.uuid4())

    def fail(*args):
        raise RuntimeError("Synthetic audit unavailable")

    monkeypatch.setattr("apps.catalog.promotion_orders.audit", fail)
    with pytest.raises(RuntimeError):
        receive_event(user, payload, signature, **credentials)
    assert not PromotionPaymentEvent.objects.exists() and not PromotionEntitlement.objects.exists()
    order.refresh_from_db()
    order.payment_attempt.refresh_from_db()
    assert order.status == "pending" and order.payment_attempt.status == "pending"
    with pytest.raises(RuntimeError):
        create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    assert PromotionOrder.objects.count() == 1
