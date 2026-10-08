"""Remaining route and generated-data compatibility on the common candidate."""

import time
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings import discovery
from apps.listings.models import Revision
from apps.listings.presentation_reads import PagePresentation

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("mode", ["normal", "production", "checked", "promotion"])
def test_actual_routes_keep_native_presentation_equivalence(
    request, settings, monkeypatch, record_property, mode
):
    client = request.getfixturevalue("directory")
    if mode == "promotion":
        from test_promotion_exposure import purchased

        purchased(request, settings)
    if mode == "production":
        settings.PRODUCTION = True
    params = {"checked": ["age"]} if mode == "checked" else {}
    reports = []
    for language in ["es", "en"]:
        start = time.perf_counter()
        candidate = client.get("/" + language + "/", params)
        elapsed = time.perf_counter() - start
        with monkeypatch.context() as patch:
            patch.setattr(
                discovery, "PagePresentation", lambda rows: PagePresentation(rows, grouped=False)
            )
            original = client.get("/" + language + "/", params)
        assert candidate.status_code == original.status_code == 200
        assert candidate.content == original.content
        assert candidate.wsgi_request._publication_route == original.wsgi_request._publication_route
        route = candidate.wsgi_request._publication_route
        assert route["route"] == ("projection" if mode == "normal" else "fallback")
        reports.append(
            {
                "language": language,
                "route": route,
                "count": candidate.context["page"].paginator.count,
                "request_seconds": elapsed,
                "presentation": candidate.wsgi_request._presentation_reads,
            }
        )
    record_property("route_checks", reports)
    record_property(
        "scope",
        "Two published synthetic seed profiles; end-to-end DjangoClient single first request per locale, no profiler. Diagnostic route/cost only, not10000capacity; production/age-filter may yield empty because simulated evidence is not accredited. Promotions synthetic only. Broader mode semantics retained in discovery/promotion tests. SQL/models/rules/render not_measured.",
    )


def test_generated_search_is_current_scoped_opaque_in_inventory(request, record_property):
    request.getfixturevalue("directory")
    from test_search_document_sql_proof import original_vector

    from apps.safety.models import RightsRequest
    from apps.safety.rights_access_field_read import read
    from apps.safety.rights_access_scope_inventory import source

    person = Person.objects.get(individual__username="fixture-v1-individual")
    # A source-census test, not an authorization/API delivery test. No persisted
    # fake review: source explicitly accepts its exact case/profile subject.
    case = RightsRequest(kind="access", person=person, manager_version=person.manager_version)

    def snapshot():
        with transaction.atomic():
            return source(case, person)

    initial = snapshot()
    entry = next(e for e in initial["entries"] if e["model"] == "listings.Revision")
    own = Revision.objects.filter(listing__person=person)
    assert entry["count"] == own.count()
    assert (
        entry["fields"]["search_document"]
        == Revision._meta.get_field("search_document").get_internal_type()
    )
    assert all("search_document" in r["fields"] for r in entry["records"])
    other = Revision.objects.exclude(listing__person=person).first()
    Revision.objects.filter(pk=other.pk).update(
        description="Unrelated separate synthetic lexeme zebra"
    )
    assert snapshot()["digest"] == initial["digest"]
    target = own.first()
    Revision.objects.filter(pk=target.pk).update(description="Scoped synthetic lexeme hummingbird")
    changed = snapshot()
    assert changed["digest"] != initial["digest"]
    changed_entry = next(e for e in changed["entries"] if e["model"] == "listings.Revision")
    assert [r["fields"]["search_document"]["digest"] for r in entry["records"]] != [
        r["fields"]["search_document"]["digest"] for r in changed_entry["records"]
    ]
    assert "hummingbird" not in str(changed)
    assert all(
        a == b
        for a, b in own.annotate(expected=original_vector()).values_list(
            "search_document", "expected"
        )
    )
    with pytest.raises(ValidationError, match="Unsupported"):
        read(
            None,
            case.pk,
            0,
            0,
            uuid4(),
            "listings.Revision",
            "0" * 64,
            "search_document",
            uuid4(),
            "Synthetic unsupported raw derived field",
        )
    record_property(
        "generated_inventory",
        {
            "scoped_current_opaque": True,
            "unsupported_field_read_fails_closed": True,
            "limitations": "Internal source census only; does not accept full rights delivery. No derived raw content newly exposed.",
        },
    )


def test_reviewed_rectification_recomputes_generated_document_without_publishing(
    request, settings, monkeypatch, record_property
):
    from test_privacy_release import fresh
    from test_rectification_review import REASON, independent_case
    from test_search_document_sql_proof import original_vector

    from apps.safety.rectification_execution import execute, notify
    from apps.safety.rectification_review import inspect, review
    from apps.safety.rights_rectification import preview

    case, reviewer, other, person, proposal, path, client, receipt = independent_case(
        request,
        settings,
        monkeypatch,
        with_receipt=True,
        subject_username="fixture-v1-individual",
        changes={
            "title": "Synthetic corrected hummingbird",
            "description": "Distinct synthetic draft description.",
        },
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    original = proposal.action.actor
    staff = Client()
    staff.force_login(original)
    session = staff.session
    session["mfa_version"] = original.mfa_version
    session.save()

    def inspect_current():
        preview(reviewer, case.pk, case.version, "Read current correction source before execution")
        inspect(
            reviewer,
            case.pk,
            proposal.pk,
            case.version,
            "Read approved proposed correction independently",
        )

    inspect_current()
    review(reviewer, case.pk, proposal.pk, uuid4(), case.version, "approved", REASON)
    case.refresh_from_db()
    fresh(case, reviewer, other, original, staff)
    inspect_current()
    notice = notify(reviewer, case.pk, proposal.pk, uuid4(), case.version, REASON)
    assert (
        client.post(
            receipt + f"response/{notice.response_id}/acknowledge/", {"received": "yes"}
        ).status_code
        == 302
    )
    case.refresh_from_db()
    fresh(case, reviewer, other, original, staff)
    inspect_current()
    old_id = person.listing.approved_revision_id
    key = uuid4()
    version = case.version
    result = execute(reviewer, case.pk, proposal.pk, key, version, REASON)
    assert execute(reviewer, case.pk, proposal.pk, key, version, REASON).pk == result.pk
    corrected = result.corrected_revision
    corrected.refresh_from_db()
    assert corrected.status == "draft" and corrected.source_revision_id == old_id
    assert corrected.title == "Synthetic corrected hummingbird"
    actual, expected = (
        Revision.objects.filter(pk=corrected.pk)
        .annotate(expected=original_vector())
        .values_list("search_document", "expected")
        .get()
    )
    assert actual == expected and "hummingbird" in actual
    person.listing.refresh_from_db()
    assert person.listing.approved_revision_id == old_id and person.listing.status == "paused"
    public = request.getfixturevalue("directory").get("/es/", {"q": "hummingbird"})
    assert public.status_code == 200 and public.context["page"].paginator.count == 0
    assert connection.vendor == "postgresql"
    record_property(
        "generated_rectification",
        {
            "current_generated_content": True,
            "draft_not_published": True,
            "approved_pointer_preserved": True,
            "execution_replay": True,
            "no_real_provider_claim": True,
        },
    )
