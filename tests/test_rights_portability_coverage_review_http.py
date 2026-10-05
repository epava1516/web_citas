"""HTTP private independent page review; PostgreSQL synthetic coverage."""

from uuid import uuid4

import pytest
from django.db import transaction
from django.test import Client
from django.urls import reverse
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.safety.models import RightsAction
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_store import save_coverage

pytestmark = pytest.mark.django_db(transaction=True)


def login(user, *, csrf=False):
    client = Client(enforce_csrf_checks=csrf)
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    return client


@pytest.mark.parametrize("account_only", [False, True])
def test_review_http_requires_all_pages_and_never_restores_evidence_on_get(
    request, settings, monkeypatch, account_only
):
    case, author, _, selection_review, _, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    reason = "PRIVATE_HTTP_INDEPENDENT_COVERAGE_REVIEW"
    row = save_coverage(
        author,
        case.pk,
        case.version,
        selection_review.pk,
        uuid4(),
        0,
        reason,
        {name: {} for name in SECTIONS},
        {},
        allow_partial=True,
    )
    reviewer = User.objects.get(pk=selection_review.action.actor_id)
    client = login(reviewer)
    url = reverse("rights_portability_coverage_review", args=[case.pk, row.pk])
    listing_response = client.get(reverse("rights_inspect", args=[case.pk]))
    assert url.encode() in listing_response.content
    assert url.encode() not in login(author).get(reverse("rights_inspect", args=[case.pk])).content
    before = RightsAction.objects.filter(request=case).count()
    response = client.get(url)
    assert response.status_code == 200 and response.context["page"] is None
    assert RightsAction.objects.filter(request=case).count() == before
    assert "no-store" in response["Cache-Control"]
    assert login(author).get(url).status_code == 403
    data = {
        "operation": "review",
        "key": str(uuid4()),
        "version": case.version,
        "reason": reason,
        "outcome": "rejected",
    }
    assert client.post(url, data).status_code == 409
    with transaction.atomic():
        locked, person, listing = reviewer_case(reviewer, case.pk)
        source = source_copy(person, listing, locked)
    for dataset, index, page, binary in required_pages(source):
        response = client.post(
            url,
            {
                "operation": "inspect",
                "key": str(uuid4()),
                "version": case.version,
                "reason": reason,
                "dataset": "binary" if binary else dataset,
                "row_number": index + 1,
                "field_page": page,
            },
        )
        assert response.status_code == 200
        assert response.context["page"]["binary"] == binary
        if any(item["conditions"] for item in response.context["page"]["fields"]):
            assert (
                b"Automated processing" in response.content
                or b"Tratamiento automatizado" in response.content
            )
    response = client.post(url, data)
    assert response.status_code == 200
    decision = response.context["decision"]
    assert decision.outcome == "rejected"
    assert client.post(url, data).context["decision"].pk == decision.pk
    assert reason.encode() not in client.get(url).content
    assert login(reviewer, csrf=True).post(url, data).status_code == 403
    case.refresh_from_db()
    assert case.version == locked.version and case.status == locked.status
