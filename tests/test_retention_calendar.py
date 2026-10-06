"""Synthetic calendar metadata exercises real PostgreSQL and scoped HTTP navigation."""

from datetime import timedelta

import pytest
from django.db.models.signals import post_init
from django.urls import reverse
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_retention_reviews import prepared

from apps.safety.models import RetentionReview

pytestmark = pytest.mark.django_db(transaction=True)


def test_calendar_bounds_loading_and_preserves_navigation_and_scope(request, settings, monkeypatch):
    case, _, reviewer, client, _, _, plan, _ = prepared(request, settings, monkeypatch)
    today = timezone.localdate()
    # Metadata fixtures do not authorize new retention purposes or legal decisions.
    RetentionReview.objects.bulk_create(
        [
            RetentionReview(
                plan=plan,
                purpose=f"calendar_fixture_{i}",
                operation="review",
                initial_review_on=today,
                next_review_on=today,
                responsible=reviewer,
            )
            for i in range(1100)
        ]
    )
    expected = list(
        RetentionReview.objects.filter(next_review_on__lte=today)
        .order_by("next_review_on", "pk")
        .values_list("pk", flat=True)
    )
    loaded = []

    def observed(sender, instance, **kwargs):
        loaded.append(instance.pk)

    path = reverse("retention_queue")
    post_init.connect(observed, sender=RetentionReview)
    try:
        first = client.get(path)
    finally:
        post_init.disconnect(observed, sender=RetentionReview)
    assert first.status_code == 200
    assert 50 <= len(loaded) <= 100
    page = first.context["page"]
    first_ids = [row.pk for row in page]
    assert first_ids == expected[:50]
    assert not page.has_previous() and page.has_next()
    token = page.next_cursor
    second = client.get(path, {"cursor": token})
    second_page = second.context["page"]
    assert [row.pk for row in second_page] == expected[50:100]
    back = client.get(path, {"cursor": second_page.previous_cursor})
    assert [row.pk for row in back.context["page"]] == first_ids
    collected = first_ids
    while token:
        response = client.get(path, {"cursor": token})
        assert response.status_code == 200
        page = response.context["page"]
        collected.extend(row.pk for row in page)
        token = page.next_cursor
    assert collected == expected
    assert client.get(path, {"cursor": second_page.previous_cursor + "x"}).status_code == 400
    assert (
        client.get(path, {"cursor": second_page.previous_cursor, "attention": "all"}).status_code
        == 400
    )
    assert client.get(path, {"page": "2"}).status_code == 400
    case.actor = reviewer
    case.save(update_fields=["actor"])
    hidden = client.get(path)
    assert hidden.status_code == 200 and len(hidden.context["page"]) == 0
    assert b"calendar_fixture_" not in hidden.content


def test_calendar_date_filters_and_cursor_expiry(request, settings, monkeypatch):
    _, _, reviewer, client, _, _, plan, _ = prepared(request, settings, monkeypatch)
    today = timezone.localdate()
    RetentionReview.objects.filter(plan=plan).update(next_review_on=today + timedelta(days=30))
    RetentionReview.objects.bulk_create(
        [
            RetentionReview(
                plan=plan,
                purpose=f"filter_fixture_{i}",
                operation="review",
                initial_review_on=today,
                next_review_on=today + timedelta(days=i % 3 * 7),
                responsible=reviewer,
            )
            for i in range(160)
        ]
    )
    path = reverse("retention_queue")
    due = client.get(path).context["page"]
    assert all(row.next_review_on <= today for row in due)
    soon = client.get(path, {"attention": "soon"}).context["page"]
    assert all(row.next_review_on <= today + timedelta(days=7) for row in soon)
    all_page = client.get(path, {"attention": "all"}).context["page"]
    from django.core import signing

    payload = signing.loads(all_page.next_cursor, salt="safety.retention-calendar.v1")
    payload[1] = str(reviewer.pk + 1)
    foreign = signing.dumps(payload, salt="safety.retention-calendar.v1")
    assert client.get(path, {"attention": "all", "cursor": foreign}).status_code == 400
    import time

    now = time.time()
    monkeypatch.setattr(signing.time, "time", lambda: now + 1801)
    assert client.get(path, {"attention": "all", "cursor": all_page.next_cursor}).status_code == 400
