"""Private HTTP preparation with real PostgreSQL and synthetic fixtures."""

from uuid import uuid4

import pytest
from django.test import Client
from django.urls import reverse
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsPortabilityCoverage

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only,images", [(False, False), (True, False), (False, True)])
def test_private_guided_coverage_http_get_clean_save_replay_csrf(
    request, settings, monkeypatch, account_only, images
):
    case, author, _, decision, _, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    url = reverse(
        "rights_portability_image_coverage" if images else "rights_portability_coverage",
        args=[case.pk],
    )
    client = Client()
    client.force_login(author)
    session = client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    before = RightsAction.objects.filter(request=case).count()
    response = client.get(url)
    assert response.status_code == 200
    assert RightsAction.objects.filter(request=case).count() == before
    assert response.context["catalog"] is None
    assert "no-store" in response["Cache-Control"]
    reason = "Synthetic HTTP omission preparation for independent review"
    catalog_data = {
        "operation": "catalog",
        "key": str(uuid4()),
        "version": case.version,
        "review": decision.pk,
        "dataset": "subject_account" if account_only else "profile",
        "row_number": 1,
        "field_page": 1,
        "purpose": reason,
    }
    response = client.post(url, catalog_data)
    assert response.status_code == 200
    catalog = response.context["catalog"]
    assert catalog["fields"]
    form = response.context["save_form"]
    forms = response.context["field_forms"]
    selected = catalog["fields"][0]["path"]
    data = {
        "operation": "save",
        "key": str(form.initial["key"]),
        "token": form.initial["token"],
        "reason": reason,
        "paths": [selected],
        "fields-TOTAL_FORMS": len(forms.forms),
        "fields-INITIAL_FORMS": len(forms.forms),
        "fields-MIN_NUM_FORMS": 0,
        "fields-MAX_NUM_FORMS": 50,
    }
    for index, item in enumerate(catalog["fields"]):
        facts = {
            "path": item["path"],
            "basis": "other",
            "origin": "inferred",
            "automated": "yes",
            "subject_related": "yes",
            "third_party_reviewed": "yes",
            "reason": "Synthetic fixture exclusion without production factual claim",
            "evidence": "PRIVATE_HTTP_COVERAGE_EVIDENCE",
        }
        data.update({f"fields-{index}-{name}": value for name, value in facts.items()})
    response = client.post(url, data)
    assert response.status_code == 200
    row = response.context["saved"]
    assert unseal(row.encrypted_coverage)["allow_partial"] is True
    if images:
        assert selected in unseal(row.encrypted_coverage)["image_omissions"]
    assert client.post(url, data).context["saved"].pk == row.pk
    assert RightsPortabilityCoverage.objects.filter(request=case).count() == 1
    response = client.get(url)
    assert b"PRIVATE_HTTP_COVERAGE_EVIDENCE" not in response.content
    assert response.context["catalog"] is None
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(author)
    session = strict.session
    session["mfa_version"] = author.mfa_version
    session.save()
    assert strict.post(url, catalog_data).status_code == 403
    anonymous = Client()
    assert anonymous.get(url).status_code == 302
