"""Stored publication state: native equivalence, trigger invalidation and refresh races."""

import re
import threading
import uuid
from datetime import timedelta

import pytest
from django.db import connection, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Category, Municipality
from apps.core.models import Agency, LegalDocument, Person, PhoneClaim, RepresentationAction
from apps.listings import moderation, publication_state
from apps.listings import projected_publication as projection
from apps.listings.discovery import candidates
from apps.listings.models import Listing, PublicationDirty, Rate, Revision
from apps.listings.public_validation import PublicationContext
from apps.mediafiles.models import Blob, Photo
from apps.safety import models as safety

pytestmark = pytest.mark.django_db(transaction=True)

QUERIES = [{}, {"q": "photography"}, {"q": "synthetic"}, {"page": "2"}, {"checked": ["age"]},
           {"checked": ["contact", "agency"]}, {"reception": "on"}]


def native(client, monkeypatch, path, params):
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
        patch.setattr(projection, "supported", lambda **kwargs: False)
        return client.get(path, params)


def assert_equivalent(client, monkeypatch, *, expect_state=True):
    for language in ["es", "en"]:
        for params in QUERIES:
            candidate = client.get(f"/{language}/", params)
            original = native(client, monkeypatch, f"/{language}/", params)
            assert candidate.status_code == original.status_code, params
            assert candidate.content == original.content, (language, params)
            if expect_state and candidate.status_code == 200:
                assert candidate.wsgi_request._publication_route["route"] == "state", params


def drain():
    while publication_state.refresh(500):
        pass
    assert not PublicationDirty.objects.exists()


def dirty_ids():
    return set(PublicationDirty.objects.values_list("listing_id", flat=True))


def published():
    return Listing.objects.filter(status="published").select_related(
        "person__agency", "approved_revision").order_by("pk").first()


@pytest.mark.parametrize("mode", ["normal", "production"])
def test_state_route_matches_native_before_and_after_refresh(request, settings, monkeypatch, mode):
    client = request.getfixturevalue("directory")
    if mode == "production":
        settings.PRODUCTION = True
        publication_state.rules_version.cache_clear()
    assert dirty_ids()  # Fresh listings are unknown and evaluated natively.
    assert_equivalent(client, monkeypatch)
    drain()
    assert_equivalent(client, monkeypatch)
    publication_state.rules_version.cache_clear()


MUTATIONS = {
    "consent_revoked": lambda listing: Person.objects.filter(pk=listing.person_id).update(
        consent_revoked_at=timezone.now()),
    "age_failed": lambda listing: Person.objects.filter(pk=listing.person_id).update(
        age_status="failed"),
    "phone_unverified": lambda listing: PhoneClaim.objects.filter(
        pk=listing.person.phone_claim_id).update(verified_at=None),
    "agency_pending": lambda listing: Agency.objects.update(verification_status="pending"),
    "grant_removed": lambda listing: RepresentationAction.objects.filter(
        person_id=listing.person_id, action="grant").delete(),
    "check_failed": lambda listing: listing.person.verificationcheck_set.update(status="failed"),
    "listing_paused": lambda listing: Listing.objects.filter(pk=listing.pk).update(status="paused"),
    "expired": lambda listing: Listing.objects.filter(pk=listing.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)),
    "text_with_url": lambda listing: Revision.objects.filter(
        pk=listing.approved_revision_id).update(description="visit www.example.invalid"),
    "invalid_rate": lambda listing: Rate.objects.create(
        revision_id=listing.approved_revision_id, concept="call +34 600 000 000", mode="consult"),
    "photo_removed": lambda listing: Photo.objects.filter(
        revision_id=listing.approved_revision_id).update(removed_at=timezone.now()),
    "blob_failed": lambda listing: Blob.objects.filter(
        photos__revision_id=listing.approved_revision_id).update(status="failed"),
    "category_inactive": lambda listing: Category.objects.filter(
        revision__pk=listing.approved_revision_id).update(active=False),
    "city_inactive": lambda listing: Municipality.objects.filter(
        pk=listing.approved_revision.municipality_id).update(active=False),
    "category_removed": lambda listing: listing.approved_revision.categories.clear(),
    "publishing_terms_replaced": lambda listing: replace_publishing_terms(),
}


def replace_publishing_terms():
    current = LegalDocument.objects.filter(slug="publishing", active=True)
    for document in list(current):
        document.active = False
        document.save(update_fields=["active"])
        LegalDocument.objects.create(slug="publishing", version=document.version + "-next",
                                     language=document.language, title=document.title,
                                     body=document.body, published_at=timezone.now())


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_dependency_change_is_reflected_without_refresh(request, monkeypatch, name):
    client = request.getfixturevalue("directory")
    drain()
    listing = published()
    if name == "agency_pending":
        listing = Listing.objects.filter(status="published", person__agency__isnull=False).select_related(
            "person__agency", "approved_revision").first()
    assert moderation.publicly_visible(listing)
    MUTATIONS[name](listing)
    # No refresh: exactness comes from the trigger-marked native evaluation.
    assert listing.pk in dirty_ids() or name == "expired"
    assert_equivalent(client, monkeypatch, expect_state=False)
    drain()
    assert_equivalent(client, monkeypatch, expect_state=False)


def native_tables():
    tables = set()

    def grab(execute, sql, params, many, context):
        tables.update(re.findall(r'(?:FROM|JOIN)\s+"([a-z_0-9]+)"', sql))
        return execute(sql, params, many, context)

    with connection.execute_wrapper(grab):
        listing = published()
        moderation.publicly_visible(listing)
        context = PublicationContext(candidates({}))
        [moderation.publicly_visible(row, context=context) for row in context.rows]
    return tables


def test_every_table_read_by_the_native_rule_has_an_invalidation_trigger(request):
    request.getfixturevalue("directory")
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT event_object_table FROM information_schema.triggers "
                       "WHERE trigger_name LIKE 'lpd_%%'")
        triggered = {row[0] for row in cursor.fetchall()}
    assert native_tables() <= triggered


class Rollback(Exception):
    pass


def assert_marks(listing, create):
    """Insert under deferred FK checks, observe the trigger, never commit the fake rows."""
    with pytest.raises(Rollback), transaction.atomic():
        PublicationDirty.objects.all().delete()
        create()
        assert listing.pk in dirty_ids()
        raise Rollback


def test_safety_dependency_rows_mark_the_affected_listing(request):
    request.getfixturevalue("directory")
    drain()
    listing = published()
    photo = Photo.objects.filter(revision_id=listing.approved_revision_id).first()
    fake = {"proof_id": uuid.uuid4()}
    now = timezone.now()

    def chain():
        proposal = safety.RightsRectificationProposal.objects.create(
            action_id=9_000_001, person_id=listing.person_id, source_digest="x",
            encrypted_changes="x", **fake)
        review = safety.RightsRectificationReview.objects.create(
            proposal=proposal, action_id=9_000_002, outcome="x", changes_digest="x", **fake)
        notification = safety.RightsRectificationNotification.objects.create(
            review=review, action_id=9_000_003, response_id=9_000_004, source_digest="x", **fake)
        return safety.RightsRectificationExecution.objects.create(
            notification=notification, action_id=9_000_005, encrypted_previous_values="x", **fake)

    def only_last(steps):
        # Every step must mark on its own: clear marks from the earlier steps first.
        def run():
            for step in steps[:-1]:
                step()
                PublicationDirty.objects.all().delete()
            steps[-1]()
        return run

    holder = {}
    assert_marks(listing, lambda: safety.PrivacyPublicationHold.objects.create(
        action_id=9_000_010, person_id=listing.person_id, subject_snapshot="x", manager_version=1,
        ground="x", previous_listing_status="", **fake))
    assert_marks(listing, lambda: safety.Restriction.objects.create(
        report_id=uuid.uuid4(), listing=listing, revision_id=listing.approved_revision_id,
        manager_version=1, action_id=9_000_011))
    assert_marks(listing, lambda: safety.RightsPhotoReintroduction.objects.create(
        photo=photo, uploaded_blob_id=uuid.uuid4(), disposition_id=9_000_012, method="sha256"))
    assert_marks(listing, lambda: safety.RightsRectificationPhotoUpload.objects.create(
        action_id=9_000_013, photo=photo, source_digest="x", person_rights_version=1,
        expires_at=now, **fake))
    assert_marks(listing, lambda: chain())
    for depth in range(1, 4):
        def partial(depth=depth):
            execution = chain()
            rows = [execution.notification.review.proposal, execution.notification.review,
                    execution.notification, execution]
            PublicationDirty.objects.all().delete()
            # Touch only one link of the chain: it alone must identify the listing.
            type(rows[depth]).objects.filter(pk=rows[depth].pk).update(**{
                {1: "outcome", 2: "source_digest", 3: "encrypted_previous_values"}[depth]: "y"})
        assert_marks(listing, partial)

    def disposition():
        execution = chain()
        PublicationDirty.objects.all().delete()
        holder["d"] = safety.RightsRectificationPhotoDisposition.objects.create(
            execution=execution, source_photo_id=uuid.uuid4(), blob_id=uuid.uuid4(), outcome="retained")
    assert_marks(listing, disposition)


def test_concurrent_change_during_refresh_keeps_listing_dirty(request):
    request.getfixturevalue("directory")
    drain()
    listing = published()
    publication_state.mark([listing.pk])
    claimed, release = threading.Event(), threading.Event()
    original = publication_state.PublicationContext

    def slow_context(*args, **kwargs):
        context = original(*args, **kwargs)
        claimed.set()
        release.wait(10)
        return context

    def refresher():
        try:
            publication_state.refresh(10)
        finally:
            connection.close()

    def writer():
        try:
            claimed.wait(10)
            with transaction.atomic():
                Person.objects.filter(pk=listing.person_id).update(age_status="failed")
                release.set()  # The trigger's upsert now waits for the refresher's row lock.
        finally:
            connection.close()

    publication_state.PublicationContext = slow_context
    try:
        threads = [threading.Thread(target=refresher), threading.Thread(target=writer)]
        [thread.start() for thread in threads]
        [thread.join(30) for thread in threads]
    finally:
        publication_state.PublicationContext = original
    # The refresher computed from the old state; the change must remain pending.
    assert listing.pk in dirty_ids()
    page = publication_state.state_page(candidates({}), 1)
    assert listing.pk not in [row.pk for row in page.object_list]
