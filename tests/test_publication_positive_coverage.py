"""Positive-result coverage of the stored publication route in PRODUCTION and `checked`.

Synthetic, isolated data only: the verification provider is a named synthetic value (never
the simulator, never a contacted service), so real_checks can pass and PRODUCTION publishes.
Ten of the 25 paginated listings receive a passed age check; phone and agency checks are
shared by the fixture. Every response is compared byte for byte with the native route.
"""

import pytest
from django.utils import timezone
from test_discovery import directory, multipage_directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Agency, Person, PhoneClaim, VerificationCheck
from apps.listings import publication_state

pytestmark = pytest.mark.django_db(transaction=True)

PROVIDER = "synthetic-coverage"
FILTERS = [{}, {"checked": ["age"]}, {"checked": ["contact"]}, {"checked": ["agency"]},
           {"checked": ["contact", "agency"]}]


@pytest.mark.parametrize("production", [False, True])
def test_positive_results_match_native(request, settings, monkeypatch, record_property, production):
    request.getfixturevalue("multipage_directory")
    client = request.getfixturevalue("client")
    people = list(Person.objects.filter(alias__startswith="Pagination subject").order_by("alias"))
    assert len(people) == 25
    template = people[0]
    PhoneClaim.objects.filter(pk=template.phone_claim_id).update(
        verified_at=timezone.now(), verification_procedure="sms-v1")
    Agency.objects.filter(pk=template.agency_id).update(
        verification_status="passed", verification_procedure="organization-v1")
    for person in people[:10]:
        VerificationCheck.objects.create(
            person=person, subject_id=person.subject_id, manager_version=person.manager_version,
            provider=PROVIDER, procedure="age-v1", status="passed")
    settings.VERIFICATION_PROVIDER = PROVIDER
    settings.PRODUCTION = production
    publication_state.rules_version.cache_clear()
    publication_state.mark_all()
    publication_state.refresh_all()
    reports = []
    try:
        for language in ["es", "en"]:
            for extra in FILTERS:
                for page in ["1", "2"]:
                    params = {"q": "pagination", "page": page, **extra}
                    actual = client.get(f"/{language}/", params)
                    with monkeypatch.context() as patch:
                        patch.setattr(publication_state, "state_page", lambda *a, **k: None)
                        native = client.get(f"/{language}/", params)
                    assert actual.status_code == native.status_code, params
                    assert actual.content == native.content, params
                    if actual.status_code != 200:
                        continue
                    route = actual.wsgi_request._publication_route
                    assert route["route"] == "state", (params, route)
                    count = actual.context["page"].paginator.count
                    reports.append({"language": language, "page": page, "filters": sorted(extra.get("checked", [])),
                                    "count": count, "route": route})
    finally:
        publication_state.rules_version.cache_clear()
    counts = {(tuple(r["filters"]), r["page"]): r["count"] for r in reports if r["language"] == "es"}
    # Positive, partial populations in the mode under test.
    assert counts[(("age",), "1")] == 10
    assert counts[(("agency", "contact"), "1")] == (10 if production else 25)
    assert counts[((), "1")] == (10 if production else 25)
    record_property("positive_coverage", {"production": production, "reports": reports})
