"""Public sponsorship remains complete and unique across pages and UTC days."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.test import Client
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup
from test_publication_state_matrix import prepare_population

from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.listings.models import Listing

pytestmark = pytest.mark.django_db(transaction=True)


def test_sponsored_rotation_preserves_filtered_public_pagination(request, settings, monkeypatch):
    _, _, top, _ = setup(request, settings)
    prepare_population(40, "repeated")
    listings = list(
        Listing.objects.filter(status="published").select_related("person__agency__owner")
        .order_by("pk")
    )
    expected = {row.pk for row in listings}
    assert len(expected) == 40
    editorial = list(
        Listing.objects.order_by("pk").values_list(
            "pk", "published_at", "lifecycle_version", "approved_revision_id"
        )
    )
    premium = PromotionProductVersion.objects.create(
        product=PromotionProduct.objects.create(slug="synthetic_premium_pages", kind="premium"),
        version=1, name_es="Premium prueba", name_en="Premium test",
        duration_days=top.duration_days, amount=top.amount, currency=top.currency,
        tax_rate=top.tax_rate, published_at=timezone.now(), is_current=True,
    )
    candidates = [row for row in listings if row.person.agency_id][:28]
    assert len(candidates) == 28
    premium_ids, top_ids = set(), set()
    for index, listing in enumerate(candidates):
        buyer = listing.person.agency.owner
        buyer.mfa_enabled = True
        buyer.save(update_fields=["mfa_enabled"])
        credentials = {"mfa_version": buyer.mfa_version, "account_version": buyer.session_version}
        version = premium if index < 10 else top
        order = create_order(buyer, listing.pk, version.pk, uuid4(), **credentials)
        payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid4())
        receive_event(buyer, payload, signature, **credentials)
        (premium_ids if index < 10 else top_ids).add(listing.pk)

    visitor = Client()

    def pages(language, query=None):
        ids, labels = [], {}
        number, total = 1, None
        while total is None or number <= total:
            response = visitor.get(f"/{language}/", {**(query or {}), "page": number})
            assert response.status_code == 200
            page = response.context["page"]
            total = page.paginator.num_pages
            page_ids = [row.pk for row in page.object_list]
            ids.extend(page_ids)
            sponsored = [card for card in response.context["cards"] if card["sponsorship"]]
            assert response.content.count(b'class="sponsored"') == len(sponsored)
            for card in sponsored:
                labels[card["listing"].pk] = card["sponsorship"]
            number += 1
        assert len(ids) == len(set(ids)), "A listing must not appear on multiple pages"
        return ids, labels

    settings.PROMOTION_TEST_MODE = False
    filtered = {}
    for language in ("es", "en"):
        ids, labels = pages(language)
        assert set(ids) == expected and not labels
        ids, labels = pages(language, {"q": "photography"})
        filtered[language] = set(ids)
        assert ids and not labels

    settings.PROMOTION_TEST_MODE = True
    now = timezone.now()
    monkeypatch.setattr("apps.catalog.promotion_exposure.timezone.now", lambda: now)
    for language in ("es", "en"):
        ids, labels = pages(language)
        assert set(ids) == expected
        assert set(ids[:10]) == premium_ids and set(ids[10:28]) == top_ids
        assert labels == {**dict.fromkeys(premium_ids, "premium"), **dict.fromkeys(top_ids, "top")}
        assert pages(language) == (ids, labels), "Pagination must be stable within the same UTC day"
        matching, selected_labels = pages(language, {"q": "photography"})
        assert set(matching) == filtered[language]
        assert set(selected_labels) == filtered[language] & (premium_ids | top_ids)
        assert pages(language, {"q": "synthetic-no-match-8293"}) == ([], {})
        monkeypatch.setattr(
            "apps.catalog.promotion_exposure.timezone.now", lambda: now + timedelta(days=1)
        )
        tomorrow, tomorrow_labels = pages(language)
        assert set(tomorrow) == expected and tomorrow_labels == labels
        assert tomorrow[:10] != ids[:10] or tomorrow[10:28] != ids[10:28]
        assert set(tomorrow[:10]) == premium_ids and set(tomorrow[10:28]) == top_ids
        monkeypatch.setattr("apps.catalog.promotion_exposure.timezone.now", lambda: now)

    assert list(
        Listing.objects.order_by("pk").values_list(
            "pk", "published_at", "lifecycle_version", "approved_revision_id"
        )
    ) == editorial
