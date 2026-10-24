"""Installed promotional fallback, real thresholds and complete native pagination."""

import hashlib
import math
import runpy
from contextlib import nullcontext
from uuid import uuid4

import pytest
from django.db import connection, transaction
from django.test import Client
from django.utils import timezone, translation
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup
from test_promotion_paged_equivalence import grant
from test_publication_state_matrix import prepare_population

from apps.listings import discovery, publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("boundary", ["dirty_1001", "unknown_49", "stale_guard"])
def test_promotional_fallback_preserves_all_native_pages(
    request, settings, monkeypatch, record_property, language, boundary,
):
    assert connection.vendor == "postgresql"
    assert publication_state.DIRTY_LIMIT == 1000
    assert publication_state.NATIVE_UNKNOWN_LIMIT == 48
    assert not publication_state.READ_REPAIR
    _, _, top, _ = setup(request, settings)
    prepare_population(60, "diverse")
    sponsored = list(
        Listing.objects.filter(status="published", person__agency__isnull=False)
        .select_related("person__agency__owner").order_by("pk")[:7]
    )
    assert len(sponsored) == 7
    for row in sponsored:
        grant(row.person, top)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    instant = timezone.now()
    monkeypatch.setattr(timezone, "now", lambda: instant)
    victim = sponsored[0]
    if boundary == "dirty_1001":
        # Explicit synthetic orphan backlog: exercise the actual global ceiling
        # without claiming that 1001 domain writes or triggers were exercised.
        PublicationDirty.objects.bulk_create([
            PublicationDirty(listing_id=uuid4(), generation=i + 1, marked_at=instant)
            for i in range(1001)
        ])
        assert PublicationDirty.objects.count() == 1001
        reason = "state_dirty_over_limit"
    elif boundary == "unknown_49":
        ids = list(Listing.objects.filter(status="published").order_by("pk")
                   .values_list("pk", flat=True)[:49])
        assert len(ids) == 49
        publication_state.mark(ids)
        assert PublicationDirty.objects.count() == 49
        reason = "state_unknown_over_limit"
    else:
        assert Revision.objects.filter(pk=victim.approved_revision_id).update(phone="invalid") == 1
        assert PublicationDirty.objects.filter(pk=victim.pk).exists()
        # Deliberate derived-state divergence, not proof of missing invalidation.
        PublicationDirty.objects.filter(pk=victim.pk).delete()
        reason = "state_page_guard_changed"

    frozen = settings.BASE_DIR / "docs/evidencias/b08-promociones-referencia-20261020.py"
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == "9f700b72394edbc8aac1a671081885b66c1754ed97f6c012a9f802bc45337c29"
    native_ranked = runpy.run_path(str(frozen), run_name="apps.catalog._beta_frozen_reference")["ranked"]
    reports = []
    for params in [{}, {"q": "photography"}]:
        if boundary == "stale_guard":
            PublicationDirty.objects.filter(pk=victim.pk).delete()
        marks = list(PublicationDirty.objects.order_by("pk").values_list("pk", "generation"))
        form = discovery.SearchForm(params, english=language == "en")
        assert form.is_valid()
        with translation.override(language):
            context = PublicationContext(discovery.candidates(form.cleaned_data), page_read=True)
            visible = [row for row in context.rows if publicly_visible(row, context=context)]
            expected, labels = native_ranked(visible, text_search=bool(params.get("q")))
        expected_ids = [row.pk for row in expected]
        assert len(expected_ids) == (59 if boundary == "stale_guard" else 60)
        assert labels and (victim.pk not in expected_ids if boundary == "stale_guard" else True)
        seen, observed = [], []
        for number in range(1, math.ceil(len(expected_ids) / 24) + 1):
            with transaction.atomic() if boundary == "unknown_49" else nullcontext():
                if boundary == "unknown_49":
                    with connection.cursor() as cursor:
                        cursor.execute("SHOW transaction_isolation")
                        assert cursor.fetchone()[0] == "read committed"
                response = Client().get(f"/{language}/", {**params, "page": number})
            assert response.status_code == 200
            page = response.context["page"]
            ids = [row.pk for row in page.object_list]
            route = response.wsgi_request._publication_route
            if number == 1 or boundary != "stale_guard":
                assert route["route"] == "fallback" and route["reason"] == reason
            assert page.paginator.count == len(expected_ids)
            assert ids == expected_ids[(number - 1) * 24:number * 24]
            actual_labels = {card["listing"].pk: card["sponsorship"]
                             for card in response.context["cards"] if card["sponsorship"]}
            assert actual_labels == {pk: labels[pk] for pk in ids if pk in labels}
            seen.extend(ids)
            observed.append(dict(page=number, route=dict(route)))
        assert seen == expected_ids and len(seen) == len(set(seen))
        if boundary == "stale_guard":
            assert PublicationDirty.objects.filter(pk=victim.pk).exists()
        else:
            assert list(PublicationDirty.objects.order_by("pk").values_list("pk", "generation")) == marks
        reports.append(dict(params=params, count=len(expected_ids), pages=observed))
    record_property("natural_fallback_native_comparisons", dict(
        boundary=boundary, language=language, dirty_limit=1000, unknown_limit=48,
        synthetic_orphan_backlog=boundary == "dirty_1001",
        deliberately_missing_invalidation=boundary == "stale_guard", variants=reports,
    ))
