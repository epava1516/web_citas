"""Commercial SQL ordering against the frozen native implementation, not itself."""

import hashlib
import math
import runpy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.test import Client
from django.utils import timezone, translation
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup
from test_publication_state_matrix import prepare_population

from apps.catalog.promotion_exposure import ranked
from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.core.models import Agency, AgencyMember, Person, User
from apps.listings import discovery, publication_state
from apps.listings.models import Listing, Revision
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext

pytestmark = pytest.mark.django_db(transaction=True)


def grant(person, version):
    buyer = person.agency.owner if person.agency_id else person.individual
    buyer.mfa_enabled = True
    buyer.save(update_fields=["mfa_enabled"])
    credentials = {"mfa_version": buyer.mfa_version, "account_version": buyer.session_version}
    order = create_order(buyer, person.listing.pk, version.pk, uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid4())
    receive_event(buyer, payload, signature, **credentials)
    return order.entitlement


def test_all_pages_match_frozen_native_with_overlapping_rights(request, settings, monkeypatch, record_property):
    _, _, top, _ = setup(request, settings)
    prepare_population(49, "diverse")
    rows = list(
        Listing.objects.filter(status="published", person__agency__isnull=False)
        .select_related("person__agency__owner").order_by("pk")
    )
    bump_instant = timezone.now()
    for kind in ["premium", "autobump"]:
        version = PromotionProductVersion.objects.create(
            product=PromotionProduct.objects.create(slug="parity_" + kind, kind=kind),
            version=1, name_es="Prueba", name_en="Test", duration_days=top.duration_days,
            amount=top.amount, currency=top.currency, tax_rate=top.tax_rate,
            bump_interval_minutes=60 if kind == "autobump" else None,
            daily_bump_limit=3 if kind == "autobump" else None,
            published_at=timezone.now(), is_current=True,
        )
        selected = rows[:5] if kind == "premium" else rows[:12]
        for index, row in enumerate(selected):
            entitlement = grant(row.person, version)
            if kind == "autobump":
                PromotionEntitlement.objects.filter(pk=entitlement.pk).update(
                    last_bumped_at=bump_instant - timedelta(minutes=index // 2 + 1),
                )
    for row in rows[3:18]:
        grant(row.person, top)
    assert PromotionEntitlement.objects.filter(order__listing_id=rows[3].pk).count() == 3
    # Include optional type filtering while retaining the original candidate semantics.
    Revision.objects.filter(listing_id__in=[row.pk for row in rows]).update(profile_type="man")
    Revision.objects.filter(listing_id__in=[row.pk for row in rows[::2]]).update(profile_type="woman")
    publication_state.refresh_all()
    reference = settings.BASE_DIR / "docs/evidencias/b08-promociones-referencia-20261020.py"
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == "9f700b72394edbc8aac1a671081885b66c1754ed97f6c012a9f802bc45337c29"
    native_ranked = runpy.run_path(str(reference), run_name="apps.catalog._beta_frozen_reference")["ranked"]
    editorial = list(Listing.objects.order_by("pk").values_list(
        "pk", "published_at", "expires_at", "lifecycle_version", "approved_revision_id",
    ))
    client = Client()
    now = timezone.now()
    checked = []
    for day in [0, 1]:
        instant = now + timedelta(days=day)
        monkeypatch.setattr("apps.catalog.promotion_exposure.timezone.now", lambda: instant)
        for language in ["es", "en"]:
            for params in [{}, {"q": "photography"}, {"profile": ["woman"], "language": ["en"]}]:
                form = discovery.SearchForm(params, english=language == "en")
                assert form.is_valid()
                with translation.override(language):
                    context = PublicationContext(discovery.candidates(form.cleaned_data), page_read=True)
                    visible = [row for row in context.rows if publicly_visible(row, context=context)]
                    expected, labels = native_ranked(visible, text_search=bool(params.get("q")))
                    fresh_ranked, fresh_labels = ranked(visible, text_search=bool(params.get("q")))
                if params.get("profile"):
                    assert 0 < len(expected) < 49
                expected_ids = [row.pk for row in expected]
                assert [row.pk for row in fresh_ranked] == expected_ids and fresh_labels == labels
                all_ids = []
                for number in range(1, max(1, math.ceil(len(expected) / 24)) + 1):
                    response = client.get(f"/{language}/", {**params, "page": number})
                    assert response.status_code == 200
                    page = response.context["page"]
                    ids = [row.pk for row in page.object_list]
                    assert response.wsgi_request._publication_route["route"] == "state"
                    assert page.paginator.count == len(expected)
                    assert ids == expected_ids[(number - 1) * 24:number * 24]
                    assert {card["listing"].pk: card["sponsorship"] for card in response.context["cards"] if card["sponsorship"]} == {pk: labels[pk] for pk in ids if pk in labels}
                    all_ids.extend(ids)
                assert all_ids == expected_ids and len(all_ids) == len(set(all_ids))
                checked.append({"day": day, "language": language, "params": params, "count": len(expected)})
    assert len(checked) == 12
    assert editorial == list(Listing.objects.order_by("pk").values_list(
        "pk", "published_at", "expires_at", "lifecycle_version", "approved_revision_id",
    ))
    record_property("frozen_native_comparisons", checked)


@pytest.mark.parametrize("role", ["individual", "owner", "editor"])
def test_commercial_revocation_is_fresh_in_sql_and_batch(request, settings, role):
    _, own_listing, version, _ = setup(request, settings)
    person = own_listing.person if role == "individual" else Person.objects.get(subject__username="fixture-v1-model-a")
    buyer = (person.individual if role == "individual" else
             person.agency.owner if role == "owner" else person.assigned_editor)
    buyer.mfa_enabled = True
    buyer.save(update_fields=["mfa_enabled"])
    credentials = {"mfa_version": buyer.mfa_version, "account_version": buyer.session_version}
    order = create_order(buyer, person.listing.pk, version.pk, uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid4())
    receive_event(buyer, payload, signature, **credentials)
    publication_state.refresh_all()
    stale = person.listing
    assert ranked([stale])[1] == {stale.pk: "top"}
    assert any(card["listing"].pk == stale.pk and card["sponsorship"] == "top" for card in Client().get("/es/").context["cards"])
    if role == "individual":
        User.objects.filter(pk=buyer.pk).update(is_active=False)
    elif role == "owner":
        Agency.objects.filter(pk=person.agency_id).update(owner=User.objects.get(username="fixture-v1-visitor"))
    else:
        AgencyMember.objects.filter(agency_id=person.agency_id, user=buyer).update(active=False)
    assert not ranked([stale])[1]
    assert not any(card["listing"].pk == stale.pk and card["sponsorship"] for card in Client().get("/es/").context["cards"])
    assert PromotionEntitlement.objects.filter(order=order).count() == 1
