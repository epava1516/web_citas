"""Functional oracle and fresh-authority coverage for the value projection."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings import projected_publication as projection_module
from apps.listings import submissions
from apps.listings.discovery import candidates
from apps.listings.forms import DetailsForm
from apps.listings.models import Revision
from apps.listings.moderation import publicly_visible
from apps.listings.projected_publication import ProjectedPublication, projected_page, supported
from apps.listings.public_validation import PublicationContext
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def native_ids(query):
    context = PublicationContext(query)
    return [row.pk for row in context.rows if publicly_visible(row, context=context)]


def test_projection_proves_full_population_before_page_and_keeps_native_body(
    request, monkeypatch, record_property
):
    client = request.getfixturevalue("directory")
    populate(50)
    assert supported()
    query = candidates({})
    projection = ProjectedPublication(query)
    assert projection.visible_ids(query) == native_ids(query)
    assert projection.stats["candidates"] == projection.stats["positive"] == 50
    assert projection.stats["native_fallback"] == 0
    assert projection.stats["details_native"] < 50
    assert projection.stats["contacts_native"] < 50
    second = projected_page(query, 2)
    assert second is not None and second.paginator.count == 50
    assert [row.pk for row in second.object_list] == native_ids(query)[24:48]
    for language in ["es", "en"]:
        for params in [{}, {"page": "2"}, {"q": "photography"}]:
            fast = client.get(f"/{language}/", params)
            assert fast.status_code == 200 and fast["Cache-Control"] == "no-store"
            with monkeypatch.context() as patched:
                patched.setattr(projection_module, "supported", lambda **kwargs: False)
                native = client.get(f"/{language}/", params)
            assert fast.status_code == native.status_code
            assert fast.content == native.content
            assert fast.context["page"].paginator.count == native.context["page"].paginator.count
            assert [row.pk for row in fast.context["page"].object_list] == [
                row.pk for row in native.context["page"].object_list]
    record_property("projection_stats", projection.stats)
    record_property("oracle", "Ordered population, page2/24, exact native ES/EN bodies, search")


def test_projection_preserves_normalization_and_unknown_data_fallback(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    Revision.objects.filter(pk=revision.pk).update(
        title="  Whitespace title  ", telegram=" @Valid_name ",
        description="  Description of a synthetic professional.  ",
    )
    assert supported()
    fast = client.get("/es/")
    row = next(item for item in fast.context["page"].object_list if item.pk == person.listing.pk)
    assert row.approved_revision.title == "Whitespace title"
    assert row.approved_revision.telegram == "Valid_name"
    assert row.approved_revision.description == "Description of a synthetic professional."
    # A non-list JSON shape is outside the exact typed memo domain; native
    # validation determines eligibility instead of a new blanket rejection.
    Revision.objects.filter(pk=revision.pk).update(spoken_languages={"es": True})
    query = candidates({})
    projection = ProjectedPublication(query)
    assert projection.visible_ids(query) == native_ids(query)
    assert projection.stats["native_fallback"] >= 1
    Revision.objects.filter(pk=revision.pk).update(spoken_languages=["es"], title="www.invalid.example")
    projection = ProjectedPublication(candidates({}))
    assert projection.visible_ids(candidates({})) == native_ids(candidates({}))
    assert person.listing.pk not in projection.visible_ids(candidates({}))


def test_unknown_instance_rule_or_form_metadata_uses_full_native_path(request, monkeypatch):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    assert supported()

    def changed_clean(instance):
        if instance.listing_id == person.listing.pk:
            raise ValidationError("Synthetic new instance rule")

    with monkeypatch.context() as patched:
        patched.setattr(Revision, "clean", changed_clean)
        assert not supported()
        assert projected_page(candidates({}), 1) is None
        response = client.get("/es/")
        assert person.listing.pk not in [row.pk for row in response.context["page"].object_list]
    with monkeypatch.context() as patched:
        patched.setattr(DetailsForm.base_fields["title"], "disabled", True)
        assert not supported()
        assert projected_page(candidates({}), 1) is None
    assert supported()


def test_unsupported_modes_do_not_bypass_checked_production_or_promotions(request, settings):
    request.getfixturevalue("directory")
    assert supported()
    assert not supported(checked=True)
    settings.PRODUCTION = True
    assert not supported()
    settings.PRODUCTION = False
    settings.PROMOTION_TEST_MODE = True
    assert not supported()


def test_revocation_committed_between_projection_and_hydration_recomputes_native_population(
    request, monkeypatch, record_property
):
    client = request.getfixturevalue("directory")
    populate(50)
    assert supported()
    target_id = candidates({}).first().person_id
    listing_id = Person.objects.get(pk=target_id).listing.pk
    original = ProjectedPublication.visible_ids
    committed = []

    def revoke_on_other_connection():
        close_old_connections()
        try:
            with transaction.atomic():
                assert Person.objects.filter(pk=target_id).update(consent_revoked_at=timezone.now()) == 1
            committed.append(True)
        finally:
            connection.close()

    def after_projection(self, query):
        result = original(self, query)
        assert listing_id in result
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(revoke_on_other_connection).result(timeout=30)
        return result

    monkeypatch.setattr(ProjectedPublication, "visible_ids", after_projection)
    response = client.get("/es/")
    assert committed == [True]
    assert response.context["page"].paginator.count == 49
    actual = [row.pk for row in response.context["page"].object_list]
    assert actual == native_ids(candidates({}))[:24]
    assert listing_id not in actual
    record_property("concurrent_revocation_observed", True)
    record_property("native_population_recomputed", True)


def test_changed_authority_alias_outside_page_preserves_complete_count(request, monkeypatch):
    client = request.getfixturevalue("directory")
    populate(50)
    last = candidates({}).last()
    first_page_ids = native_ids(candidates({}))[:24]
    assert last.pk not in first_page_ids
    original = submissions.publication_ready

    def changed(person):
        return person.pk != last.person_id and original(person)

    monkeypatch.setattr(submissions, "publication_ready", changed)
    assert not supported()
    response = client.get("/es/")
    assert response.context["page"].paginator.count == 49
    assert [row.pk for row in response.context["page"].object_list] == first_page_ids


def test_distinct_content_and_full_unknown_fallback_preserve_native_population(request, record_property):
    request.getfixturevalue("directory")
    populate(25)
    for index, row in enumerate(candidates({})):
        Revision.objects.filter(pk=row.approved_revision_id).update(
            description=f"Unique synthetic professional description number {index}."
        )
    query = candidates({})
    projection = ProjectedPublication(query)
    assert projection.visible_ids(query) == native_ids(query)
    assert projection.stats["positive"] == projection.stats["details_native"] == 25
    record_property("distinct_content_stats", dict(projection.stats))
    Revision.objects.filter(approved_for__status="published").update(spoken_languages={"es": True})
    query = candidates({})
    unknown = ProjectedPublication(query)
    assert unknown.visible_ids(query) == native_ids(query)
    assert unknown.stats["positive"] == 0 and unknown.stats["native_fallback"] == 25
    record_property("full_unknown_fallback_stats", dict(unknown.stats))
    record_property("limits", "Small functional diversity/fallback cases; no latency or capacity claim")
