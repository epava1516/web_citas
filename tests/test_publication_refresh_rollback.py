"""A discarded commit callback must not suppress a later refresh."""

import pytest
from django.db import connection, transaction

from apps.listings import tasks
from apps.listings.models import Listing
from apps.listings.publication_signals import schedule_refresh

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def independent_legacy_flag(monkeypatch):
    # Reproduce each rollback independently, even when the previous negative
    # case left the old implementation's flag set on the reused connection.
    monkeypatch.setattr(connection, "_publication_refresh_scheduled", False, raising=False)


@pytest.mark.parametrize("savepoint", [False, True])
def test_rollback_does_not_suppress_later_committed_refresh(monkeypatch, savepoint):
    queued = []
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda: queued.append(1))

    def rolled_back():
        with transaction.atomic():
            schedule_refresh(Listing)
            transaction.set_rollback(True)

    if savepoint:
        with transaction.atomic():
            rolled_back()
            assert queued == []
            schedule_refresh(Listing)
    else:
        rolled_back()
        assert queued == []
        with transaction.atomic():
            schedule_refresh(Listing)

    assert queued == [1]


def test_nested_committed_writes_schedule_one_refresh(monkeypatch):
    queued = []
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda: queued.append(1))
    with transaction.atomic():
        schedule_refresh(Listing)
        with transaction.atomic():
            schedule_refresh(Listing)
        schedule_refresh(Listing)
        assert queued == []
    assert queued == [1]


def test_rolled_back_savepoint_preserves_outer_refresh(monkeypatch):
    queued = []
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda: queued.append(1))
    with transaction.atomic():
        schedule_refresh(Listing)
        with transaction.atomic():
            schedule_refresh(Listing)
            transaction.set_rollback(True)
        assert queued == []
    assert queued == [1]
