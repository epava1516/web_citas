"""Exact current-state membership across trust boundaries and off-page candidates."""

import pytest
from django.db import connection
from django.utils import timezone
from test_discovery import directory, multipage_directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings import publication_state
from apps.listings.models import PublicationDirty, PublicationState, Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("boundary", ["missing", "old_version", "dirty_eligible", "dirty_revoked"])
def test_membership_preserves_native_population_at_trust_boundary(
    request, monkeypatch, record_property, boundary
):
    client = request.getfixturevalue("multipage_directory")
    while publication_state.refresh(500):
        pass
    second = client.get("/en/", {"q": "pagination", "page": "2"})
    target = second.context["page"].object_list[0]
    assert second.context["page"].paginator.count == 25
    assert not PublicationDirty.objects.exists()
    if boundary == "missing":
        PublicationState.objects.filter(listing_id=target.pk).delete()
    elif boundary == "old_version":
        PublicationState.objects.filter(listing_id=target.pk).update(rules_version="0" * 64)
    elif boundary == "dirty_eligible":
        Revision.objects.bulk_create([
            Revision(listing=target, manager_version=target.person.manager_version)
        ])
    else:
        Person.objects.filter(pk=target.person_id).update(consent_revoked_at=timezone.now())
    if boundary.startswith("dirty"):
        assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) == {target.pk}
    expected_count = 24 if boundary == "dirty_revoked" else 25
    reports = []
    queries = []

    def capture(execute, sql, params, many, context):
        if '"listings_publicationstate"' in sql and '"eligible"' in sql:
            queries.append(sql)
        return execute(sql, params, many, context)

    service_ids = list(target.approved_revision.services.values_list("pk", flat=True))
    filters = [{}, {"checked": ["age"]}, {"checked": ["contact", "agency"]},
               {"service": service_ids, "services_mode": "any"}]
    for language in ["es", "en"]:
        for extra in filters:
            for page in ["1", "2"]:
                params = {"q": "pagination", "page": page, **extra}
                with connection.execute_wrapper(capture):
                    actual = client.get(f"/{language}/", params)
                with monkeypatch.context() as patch:
                    patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
                    native = client.get(f"/{language}/", params)
                assert actual.status_code == native.status_code
                assert actual.content == native.content
                if actual.status_code == 200:
                    assert actual.wsgi_request._publication_route["route"] == "state"
                    assert actual.context["page"].paginator.count == native.context["page"].paginator.count
                    if not extra:
                        assert actual.context["page"].paginator.count == expected_count
                    reports.append({"language": language, "page": page,
                                    "count": actual.context["page"].paginator.count,
                                    "native_unknown": actual.wsgi_request._publication_route["native_unknown"]})
    record_property("membership_sql_shapes", queries)
    # Dirty first pages also preview clean state IDs before native hydration.
    # That direct bounded state read is not the final Listing membership query.
    preview_prefix = ('SELECT "listings_publicationstate"."listing_id" AS "listing_id" '
                      'FROM "listings_publicationstate" WHERE ')
    previews = [sql for sql in queries if sql.startswith(preview_prefix)]
    membership = [sql for sql in queries if not sql.startswith(preview_prefix)]
    assert len(previews) == (2 if boundary.startswith("dirty") else 0)
    assert all('LIMIT 24' in sql and '"search_document" @@' in sql
               and 'NOT ("listings_publicationstate"."listing_id" IN (' in sql
               for sql in previews)
    assert membership and all('IN (SELECT' in sql for sql in membership)
    # An OuterRef in the final eligible-state subquery would reintroduce the mechanism.
    assert all('U0."listing_id" = ("listings_listing"."id")' not in sql for sql in queries)
    record_property("membership_equivalence", {"boundary": boundary, "reports": reports,
                                              "final_state_membership_uncorrelated": True})
