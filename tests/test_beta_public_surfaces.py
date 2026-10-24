"""Romantic profile authority remains exact across surfaces without a timely worker."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.test import Client
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_exposure import purchased
from test_sitemaps import NS, urls

from apps.catalog.promotion_order_models import PromotionOrder
from apps.core.models import Person, User
from apps.listings import tasks
from apps.listings.lifecycle import act
from apps.listings.models import Favorite, Listing, PublicationState, Rate, Revision
from apps.listings.profile_contract import LEGACY_CONTRACT
from apps.listings.publication_state import refresh_all

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("change", [
    "paused", "withdrawn", "expired", "consent", "manager", "age", "legacy",
    "unknown_contract", "professional_rate", "photo_removed", "phone_unverified",
    "missing_category",
])
def test_ineligible_profile_disappears_from_every_surface_before_worker_refresh(
    request, settings, monkeypatch, language, change
):
    _, listing, entitlement = purchased(request, settings)
    public = Client()
    person, revision = listing.person, listing.approved_revision
    photo = revision.photos.get(removed_at__isnull=True)
    peer = Person.objects.get(subject__username="fixture-v1-model-a").listing
    peer_before = (Listing.objects.filter(pk=peer.pk).values().get(),
                   Revision.objects.filter(pk=peer.approved_revision_id).values().get())
    visitor = User.objects.get(username="fixture-v1-visitor")
    private = Client()
    private.force_login(visitor)
    detail = f"/{language}/listing/{listing.pk}/"
    image = detail + f"photo/{photo.pk}/"
    assert private.post(detail + "favorite/").status_code == 302
    assert Favorite.objects.filter(user=visitor, listing=listing).count() == 1
    assert public.get(detail).status_code == 200
    response = public.get(image)
    assert response.status_code == 200
    response.close()
    assert any(card["listing"].pk == listing.pk and card["sponsorship"]
               for card in public.get(f"/{language}/").context["cards"])
    assert revision.title.encode() in private.get(f"/{language}/favorites/").content
    assert any(str(listing.pk) in row.find("s:loc", NS).text for row in urls(public))

    # Pause only the refresh dispatch, never PostgreSQL or the authority itself.
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda *a, **k: None)
    refresh_all()
    assert PublicationState.objects.get(listing=listing).eligible
    if change in {"paused", "withdrawn"}:
        Listing.objects.filter(pk=listing.pk).update(status=change)
    elif change == "expired":
        Listing.objects.filter(pk=listing.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    elif change == "consent":
        Person.objects.filter(pk=person.pk).update(consent_revoked_at=timezone.now())
    elif change == "manager":
        Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version + 1)
    elif change == "age":
        Person.objects.filter(pk=person.pk).update(age_status="failed")
    elif change in {"legacy", "unknown_contract"}:
        Revision.objects.filter(pk=revision.pk).update(
            content_contract=LEGACY_CONTRACT if change == "legacy" else "unknown-contract"
        )
    elif change == "professional_rate":
        Rate.objects.create(revision=revision, concept="Synthetic historical rate", mode="consult")
    elif change == "photo_removed":
        revision.photos.update(removed_at=timezone.now())
    elif change == "phone_unverified":
        person.phone_claim.verified_at = None
        person.phone_claim.save(update_fields=["verified_at"])
    else:
        assert change == "missing_category"
        revision.categories.clear()
    assert PublicationState.objects.get(listing=listing).eligible  # Deliberately stale.

    for refreshed in [False, True]:
        if refreshed:
            refresh_all()
        for promotional in [False, True]:
            settings.PROMOTION_TEST_MODE = promotional
            result = public.get(f"/{language}/")
            ids = [row.pk for row in result.context["page"].object_list]
            assert listing.pk not in ids and peer.pk in ids
            assert public.get(detail).status_code == public.get(image).status_code == 404
            favorites = private.get(f"/{language}/favorites/")
            assert favorites.status_code == 200 and favorites["Cache-Control"] == "private, no-store"
            assert all(not entry["visible"] for entry in favorites.context["entries"])
            assert revision.title.encode() not in favorites.content
            assert revision.phone.encode() not in favorites.content
            assert str(listing.pk).encode() not in favorites.content
            assert private.post(detail + "favorite/").status_code == 404
            locations = [row.find("s:loc", NS).text for row in urls(public)]
            assert all(str(listing.pk) not in row for row in locations)
            assert any(str(peer.pk) in row for row in locations)
    entitlement.refresh_from_db()
    assert entitlement.order.status == "paid" and entitlement.suspended_at is None
    assert Favorite.objects.filter(user=visitor, listing=listing).count() == 1
    assert (Listing.objects.filter(pk=peer.pk).values().get(),
            Revision.objects.filter(pk=peer.approved_revision_id).values().get()) == peer_before


@pytest.mark.parametrize("language", ["es", "en"])
def test_free_renewal_changes_organic_order_without_creating_a_promotion(
    request, settings, language
):
    public = request.getfixturevalue("directory")
    settings.PROMOTION_TEST_MODE = False
    person = Person.objects.get(individual__username="fixture-v1-individual")
    listing = person.listing
    peer = Person.objects.get(subject__username="fixture-v1-model-a").listing
    now = timezone.now()
    Listing.objects.filter(pk=listing.pk).update(
        published_at=now - timedelta(days=20), expires_at=now + timedelta(days=3)
    )
    Listing.objects.filter(pk=peer.pk).update(published_at=now - timedelta(days=1))
    refresh_all()
    before = public.get(f"/{language}/").context["page"].object_list
    assert [row.pk for row in before] == [peer.pk, listing.pk]
    revision_id, count = listing.approved_revision_id, listing.revisions.count()
    key, version = uuid4(), listing.lifecycle_version
    renewed = act(person.individual, listing.pk, key, version, "renew", True)
    assert act(person.individual, listing.pk, key, version, "renew", True).pk == renewed.pk
    result = public.get(f"/{language}/")
    assert [row.pk for row in result.context["page"].object_list] == [listing.pk, peer.pk]
    assert not any(card["sponsorship"] for card in result.context["cards"])
    renewed.refresh_from_db()
    assert renewed.published_at >= now and renewed.expires_at >= now + timedelta(days=30)
    assert renewed.approved_revision_id == revision_id and renewed.revisions.count() == count
    assert renewed.lifecycle_actions.filter(operation="renew").count() == 1
    assert not PromotionOrder.objects.filter(listing=renewed).exists()


@pytest.mark.parametrize("language", ["es", "en"])
def test_publication_panel_explains_renewal_and_separate_bump(request, language):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    client.force_login(person.individual)
    response = client.get(f"/{language}/listing/{person.listing.pk}/manage/")
    assert response.status_code == 200
    expected = (
        "Renewal sets a new thirty-day validity period"
        if language == "en" else "Renovar fija una nueva vigencia de treinta días"
    )
    assert expected.encode() in response.content
    assert ("Auto bump changes promotional ordering" if language == "en"
            else "La autosubida cambia el orden promocional").encode() in response.content
