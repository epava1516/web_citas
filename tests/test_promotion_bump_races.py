import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event

import pytest
from django.db import close_old_connections, connection, connections, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_exposure import purchased

from apps.catalog.promotion_exposure import bump_one
from apps.catalog.promotion_order_models import PromotionBumpExecution
from apps.core.models import Person, User
from apps.listings.models import Listing

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("replay", [False, True])
@pytest.mark.parametrize("change", ["management", "withdrawal", "inactive_buyer"])
def test_observed_person_wait_prevents_bump_after_eligibility_revocation(
    request, settings, replay, change
):
    user, listing, entitlement = purchased(request, settings, "autobump")
    now = entitlement.starts_at + timedelta(minutes=11)
    if replay:
        assert bump_one(entitlement.pk, now=now)
    count = PromotionBumpExecution.objects.count()
    entitlement.refresh_from_db()
    before = entitlement.last_bumped_at
    ready = Event()
    backend = {}

    def execute():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend["pid"] = cursor.fetchone()[0]
            ready.set()
            return bump_one(entitlement.pk, now=now)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Person.objects.select_for_update().get(pk=listing.person_id)
            future = pool.submit(execute)
            assert ready.wait(5)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                own = cursor.fetchone()[0]
                deadline = time.monotonic() + 5
                blocked = False
                while time.monotonic() < deadline:
                    cursor.execute("SELECT pg_blocking_pids(%s)", [backend["pid"]])
                    blocked = own in cursor.fetchone()[0]
                    if blocked:
                        break
                    time.sleep(0.02)
            assert blocked and not future.done()
            if change == "management":
                Person.objects.filter(pk=listing.person_id).update(
                    manager_version=listing.person.manager_version + 1
                )
            elif change == "withdrawal":
                Listing.objects.filter(pk=listing.pk).update(status="withdrawn")
            else:
                User.objects.filter(pk=user.pk).update(is_active=False)
        assert future.result(10) is False
    entitlement.refresh_from_db()
    assert PromotionBumpExecution.objects.count() == count and entitlement.last_bumped_at == before


def test_two_concurrent_bumps_grant_one_window_only(request, settings):
    _, _, entitlement = purchased(request, settings, "autobump")
    now = entitlement.starts_at + timedelta(minutes=11)
    barrier = Barrier(2)

    def execute():
        close_old_connections()
        try:
            barrier.wait(5)
            return bump_one(entitlement.pk, now=now)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: execute(), range(2)))
    assert sorted(outcomes) == [False, True]
    assert PromotionBumpExecution.objects.filter(entitlement=entitlement).count() == 1
