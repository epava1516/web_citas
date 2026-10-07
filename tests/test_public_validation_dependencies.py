"""Counterexamples to treating an approved revision/version as eligibility.

These are dependency/consistency probes, not a new public implementation or a
load measurement. Native validation remains the oracle after committed changes.
"""

from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Category, PostalCode, Service
from apps.core.models import Person
from apps.listings.discovery import candidates
from apps.listings.models import Rate, Revision
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext
from apps.mediafiles.models import Blob, Photo

pytestmark = pytest.mark.django_db(transaction=True)


def subject_revision():
    person = Person.objects.get(individual__username="fixture-v1-individual")
    return person.listing.approved_revision


def revision_key(revision):
    current = Revision.objects.get(pk=revision.pk)
    return (current.pk, current.edit_version, current.updated_at, current.status)


def fresh_visibility(listing_id):
    native_rows = list(candidates({}))
    native = [row.pk for row in native_rows if publicly_visible(row)]
    context = PublicationContext(candidates({}))
    batched = [row.pk for row in context.rows if publicly_visible(row, context=context)]
    assert batched == native  # Ordered population, not just count or set.
    return listing_id in native


def test_revision_version_does_not_cover_related_content_dependencies(
    request, record_property
):
    request.getfixturevalue("directory")
    revision = subject_revision()
    baseline_key = revision_key(revision)
    assert fresh_visibility(revision.listing_id)
    observed = []

    def reversible_change(label, change, restore):
        change()
        assert revision_key(revision) == baseline_key
        assert not fresh_visibility(revision.listing_id), label
        restore()
        assert revision_key(revision) == baseline_key
        assert fresh_visibility(revision.listing_id), label
        observed.append(label)

    category = revision.categories.first()
    service = revision.services.first()
    assert category and service
    reversible_change(
        "category.active",
        lambda: Category.objects.filter(pk=category.pk).update(active=False),
        lambda: Category.objects.filter(pk=category.pk).update(active=category.active),
    )
    reversible_change(
        "service.active",
        lambda: Service.objects.filter(pk=service.pk).update(active=False),
        lambda: Service.objects.filter(pk=service.pk).update(active=service.active),
    )
    other = Category.objects.create(
        slug="dependency-proof-other", name_es="Otra", name_en="Other"
    )
    reversible_change(
        "service.category_id",
        lambda: Service.objects.filter(pk=service.pk).update(category=other),
        lambda: Service.objects.filter(pk=service.pk).update(category_id=service.category_id),
    )
    selected_categories = list(revision.categories.all())
    reversible_change(
        "revision.categories membership",
        revision.categories.clear,
        lambda: revision.categories.set(selected_categories),
    )
    city = revision.municipality
    reversible_change(
        "municipality.active",
        lambda: type(city).objects.filter(pk=city.pk).update(active=False),
        lambda: type(city).objects.filter(pk=city.pk).update(active=city.active),
    )
    # Optional postal validation has additional privacy and membership inputs.
    postal = PostalCode.objects.get(code="29001")
    assert postal.public_safe and postal.municipalities.filter(pk=city.pk).exists()
    Revision.objects.filter(pk=revision.pk).update(postal_code=postal)
    assert revision_key(revision) == baseline_key
    assert fresh_visibility(revision.listing_id)
    reversible_change(
        "postal.public_safe",
        lambda: PostalCode.objects.filter(pk=postal.pk).update(public_safe=False),
        lambda: PostalCode.objects.filter(pk=postal.pk).update(public_safe=True),
    )
    reversible_change(
        "postal.municipalities membership",
        lambda: postal.municipalities.remove(city),
        lambda: postal.municipalities.add(city),
    )
    rate = Rate.objects.create(revision=revision, concept="Session", mode="consult")
    reversible_change(
        "rate.concept",
        lambda: Rate.objects.filter(pk=rate.pk).update(concept="www.example.invalid"),
        lambda: Rate.objects.filter(pk=rate.pk).update(concept=rate.concept),
    )
    reversible_change(
        "rate.duration_minutes",
        lambda: Rate.objects.filter(pk=rate.pk).update(duration_minutes=10081),
        lambda: Rate.objects.filter(pk=rate.pk).update(duration_minutes=None),
    )
    photo = revision.photos.filter(removed_at__isnull=True).first()
    assert photo and photo.comparison_complete and photo.blob.status == "ready"
    reversible_change(
        "photo.comparison_complete",
        lambda: Photo.objects.filter(pk=photo.pk).update(comparison_complete=False),
        lambda: Photo.objects.filter(pk=photo.pk).update(comparison_complete=True),
    )
    reversible_change(
        "blob.status",
        lambda: Blob.objects.filter(pk=photo.blob_id).update(status="queued"),
        lambda: Blob.objects.filter(pk=photo.blob_id).update(status="ready"),
    )
    reversible_change(
        "photo.removed_at",
        lambda: Photo.objects.filter(pk=photo.pk).update(removed_at=timezone.now()),
        lambda: Photo.objects.filter(pk=photo.pk).update(removed_at=None),
    )
    record_property("dependency_counterexamples", observed)
    record_property("revision_key_unchanged", True)
    record_property("limits", "Committed synthetic PG mutations; fresh native/batched ordered "
                    "visibility agrees after every change and restore. This rejects the "
                    "revision/version/timestamp key; it does not validate a persistent cache.")


def test_fresh_context_observes_concurrent_committed_catalog_change(
    request, record_property
):
    assert connection.vendor == "postgresql"
    request.getfixturevalue("directory")
    revision = subject_revision()
    before_key = revision_key(revision)
    category = revision.categories.first()
    old_context = PublicationContext(candidates({}))
    old_row = next(row for row in old_context.rows if row.pk == revision.listing_id)
    assert publicly_visible(old_row, context=old_context)

    def deactivate_on_other_connection():
        close_old_connections()
        try:
            with transaction.atomic():
                assert Category.objects.filter(pk=category.pk).update(active=False) == 1
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(deactivate_on_other_connection).result(timeout=30)
    assert revision_key(revision) == before_key
    assert not fresh_visibility(revision.listing_id)
    # Do not reuse the earlier request's catalog/prototypes. This old snapshot
    # is deliberately shown to stay positive; no current linearizability claim.
    assert publicly_visible(old_row, context=old_context)
    Category.objects.filter(pk=category.pk).update(active=True)
    assert fresh_visibility(revision.listing_id)
    record_property("concurrent_commit_observed_by_new_context", True)
    record_property("old_request_snapshot_is_not_invalidation", True)


def test_native_model_rule_change_is_not_covered_by_data_version(
    request, monkeypatch, record_property
):
    request.getfixturevalue("directory")
    revision = subject_revision()
    key = revision_key(revision)
    assert fresh_visibility(revision.listing_id)

    def new_rule(instance):
        if instance.pk == revision.pk:
            raise ValidationError("Synthetic instance-specific rule")

    with monkeypatch.context() as patched:
        patched.setattr(Revision, "clean", new_rule)
        assert not fresh_visibility(revision.listing_id)
        assert revision_key(revision) == key
    assert fresh_visibility(revision.listing_id)
    record_property("native_rule_change_observed", True)
    record_property("limits", "Synthetic runtime model rule; no deployment/performance claim.")
