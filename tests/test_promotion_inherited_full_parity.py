"""Exercise the frozen commercial oracle through inherited READ COMMITTED SQL."""

import pytest
from django.db import connection, transaction
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_paged_equivalence import (
    test_all_pages_match_frozen_native_with_overlapping_rights as assert_frozen_parity,
)

pytestmark = pytest.mark.django_db(transaction=True)


def test_inherited_read_committed_full_frozen_parity(
    request, settings, monkeypatch, record_property,
):
    get = Client.get
    requests = []

    def inherited_get(client, *args, **kwargs):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SHOW transaction_isolation")
                assert cursor.fetchone()[0] == "read committed"
            response = get(client, *args, **kwargs)
            with connection.cursor() as cursor:
                cursor.execute("SHOW transaction_isolation")
                assert cursor.fetchone()[0] == "read committed"
            requests.append(response.status_code)
            return response

    # Fixture preparation/refresh retains its ordinary commit boundaries.
    monkeypatch.setattr(Client, "get", inherited_get)
    assert_frozen_parity(request, settings, monkeypatch, record_property)
    assert len(requests) == 32 and set(requests) == {200}
    record_property("inherited_read_committed_requests", len(requests))
