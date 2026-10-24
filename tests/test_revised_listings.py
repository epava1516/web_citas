import pytest
from django.test import Client
from test_drafts import contacts, details, scenario  # noqa: F401
from test_listing_moderation import decision, pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import payload, prepared  # noqa: F401

from apps.listings.models import Rate, Revision
from apps.listings.profile_contract import LEGACY_CONTRACT
from apps.mediafiles.models import Blob, Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def published(request):
    person, owner, revision, moderator, reviewer = request.getfixturevalue("pending")
    assert (
        reviewer.post(f"/es/moderation/listings/{revision.pk}/", decision(revision)).status_code
        == 302
    )
    revision.refresh_from_db()
    return person, owner, revision, moderator, reviewer


def revised_draft(person, owner, title):
    response = owner.post(f"/es/person/{person.pk}/listing/start/")
    assert response.status_code == 302
    revision = Revision.objects.get(pk=response.url.split("/")[3])
    assert owner.post(response.url, details(revision, title=title)).status_code == 302
    revision.refresh_from_db()
    data = contacts(revision)
    assert owner.post(f"/es/draft/{revision.pk}/2/", data).status_code == 302
    revision.refresh_from_db()
    return revision


def test_revised_version_keeps_approved_snapshot_and_reuses_bytes(published):
    person, owner, original, _, reviewer = published
    revision = revised_draft(person, owner, "Nueva versión pendiente")
    assert revision.pk != original.pk and revision.source_revision_id == original.pk
    assert not revision.rates.exists() and not original.rates.exists()
    assert not revision.services.exists() and not original.services.exists()
    photos = list(Photo.objects.order_by("created_at"))
    assert len(photos) == 2 and Blob.objects.count() == 1
    assert (
        photos[0].blob_id == photos[1].blob_id
        and not photos[1].approved
        and photos[1].comparison_complete
    )
    path = f"/es/listing/{original.listing_id}/"
    assert original.title.encode() in Client().get(path).content
    assert revision.title.encode() not in Client().get(path).content
    assert Client().get(path + f"photo/{photos[1].pk}/").status_code == 404
    assert owner.post(f"/es/draft/{revision.pk}/submit/", payload(revision)).status_code == 302
    assert original.title.encode() in Client().get(path).content
    assert (
        reviewer.post(f"/es/moderation/listings/{revision.pk}/", decision(revision)).status_code
        == 302
    )
    assert revision.title.encode() in Client().get(path).content
    assert Client().get(path + f"photo/{photos[0].pk}/").status_code == 404
    original.refresh_from_db()
    assert original.title != revision.title and original.status == "approved"


def test_rejection_preserves_public_version_and_rate_ids_are_isolated(published):
    person, owner, original, _, reviewer = published
    response = owner.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get(pk=response.url.split("/")[3])
    assert (
        not revision.publisher_acceptance_id
        and not revision.contact_exposure_accepted
        and not revision.phone
    )
    assert (
        owner.post(
            response.url, details(revision, title="Versión rechazada por corregir")
        ).status_code
        == 302
    )
    revision.refresh_from_db()
    # A forged public form cannot overwrite a tariff retained in private history.
    history = Revision.objects.create(
        listing=person.listing,
        manager_version=person.manager_version,
        content_contract=LEGACY_CONTRACT,
        status="archived",
    )
    historical_rate = Rate.objects.create(
        revision=history, concept="Private historical tariff", mode="consult"
    )
    data = contacts(
        revision,
        **{
            "rates-INITIAL_FORMS": "1",
            "rates-0-id": str(historical_rate.pk),
            "rates-0-concept": "Unauthorized overwrite",
            "rates-0-mode": "fixed",
            "rates-0-amount": "9999.00",
        },
    )
    assert owner.post(f"/es/draft/{revision.pk}/2/", data).status_code == 400
    historical_rate.refresh_from_db()
    assert historical_rate.concept == "Private historical tariff"
    assert historical_rate.mode == "consult" and historical_rate.amount is None
    assert historical_rate.revision_id == history.pk
    assert not original.rates.exists() and not revision.rates.exists()
    data = contacts(revision)
    assert owner.post(f"/es/draft/{revision.pk}/2/", data).status_code == 302
    revision.refresh_from_db()
    assert owner.post(f"/es/draft/{revision.pk}/submit/", payload(revision)).status_code == 302
    assert (
        reviewer.post(
            f"/es/moderation/listings/{revision.pk}/",
            decision(revision, outcome="rejected", reason="Corrige el contenido"),
        ).status_code
        == 302
    )
    path = f"/es/listing/{original.listing_id}/"
    assert original.title.encode() in Client().get(path).content
    original.listing.refresh_from_db()
    assert original.listing.approved_revision_id == original.pk
    response = owner.post(f"/es/person/{person.pk}/listing/start/")
    correction = Revision.objects.get(pk=response.url.split("/")[3])
    assert correction.source_revision_id == revision.pk and correction.title == revision.title


def test_older_pending_revision_cannot_replace_later_approval(published):
    person, owner, original, _, reviewer = published
    first = revised_draft(person, owner, "Primera revisión nueva")
    assert owner.post(f"/es/draft/{first.pk}/submit/", payload(first)).status_code == 302
    second = revised_draft(person, owner, "Segunda revisión nueva")
    assert owner.post(f"/es/draft/{second.pk}/submit/", payload(second)).status_code == 302
    assert (
        reviewer.post(f"/es/moderation/listings/{second.pk}/", decision(second)).status_code == 302
    )
    assert reviewer.post(f"/es/moderation/listings/{first.pk}/", decision(first)).status_code == 400
    first.refresh_from_db()
    assert first.status == "obsolete" and first.decisions.get().outcome == "obsolete"
    assert second.title.encode() in Client().get(f"/es/listing/{original.listing_id}/").content
