from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.urls import reverse
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability import assessment
from test_rights_verification import read

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsExport, RightsPortabilitySelection
from apps.safety.rights_portability import save_assessment
from apps.safety.rights_portability_page_selection import prepare_page, save_page
from apps.safety.rights_portability_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def test_page_selection_preserves_other_pages_and_rejects_stale_or_foreign_forms(
    request, settings, monkeypatch
):
    case, author, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    decisions = assessment()
    for item in decisions.values():
        item.update(
            status="eligible",
            basis="contract",
            origin="provided",
            automated=True,
            subject_related=True,
            third_party_reviewed=True,
            reason="Synthetic reviewed provenance for page-selection test",
            evidence="Synthetic documented origin and processing conditions",
        )
    draft = save_assessment(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Prepare synthetic assessment for page-selection test",
        decisions,
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_portability",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    purpose = "Inspect synthetic provenance before guided selection"
    record(reviewer, case.pk, draft.pk, uuid4(), case.version, "inspect", purpose)
    approval, _ = record(
        reviewer, case.pk, draft.pk, uuid4(), case.version, "review", purpose, "approved"
    )
    monkeypatch.setattr("apps.safety.rights_portability_catalog.FIELD_PAGE_SIZE", 1)
    page1 = prepare_page(
        author, case.pk, case.version, approval.pk, uuid4(), purpose, "subject_account"
    )
    page1_path = page1["fields"][0]["path"]
    actions = RightsAction.objects.count()
    with pytest.raises(ValidationError, match="only from inspected page"):
        save_page(author, case.pk, page1["token"], uuid4(), purpose, ["/not-inspected"])
    with pytest.raises(PermissionDenied):
        save_page(reviewer, case.pk, page1["token"], uuid4(), purpose, [page1_path])
    with pytest.raises(ValidationError, match="expired or invalid"):
        save_page(author, case.pk, page1["token"] + "tamper", uuid4(), purpose, [page1_path])
    assert RightsAction.objects.count() == actions
    key = uuid4()
    first = save_page(author, case.pk, page1["token"], key, purpose, [page1_path])
    assert save_page(author, case.pk, page1["token"], key, purpose, [page1_path]).pk == first.pk
    page2 = prepare_page(
        author,
        case.pk,
        case.version,
        approval.pk,
        uuid4(),
        purpose,
        "subject_account",
        field_page=2,
    )
    page2_path = page2["fields"][0]["path"]
    assert page2_path != page1_path
    second = save_page(author, case.pk, page2["token"], uuid4(), purpose, [page2_path])
    selected = unseal(second.encrypted_selection)["selection"]["subject_account"]
    assert selected == [{"row": page1["row"], "fields": [page1_path, page2_path]}]
    assert second.version == first.version + 1
    with pytest.raises(ValidationError, match="version changed"):
        save_page(author, case.pk, page1["token"], uuid4(), purpose, [])
    # A confirmed retry reproduces its original version, without changing latest draft.
    assert save_page(author, case.pk, page1["token"], key, purpose, [page1_path]).pk == first.pk
    refreshed_page1 = prepare_page(
        author, case.pk, case.version, approval.pk, uuid4(), purpose, "subject_account"
    )
    assert page1_path in refreshed_page1["chosen"]
    third = save_page(author, case.pk, refreshed_page1["token"], uuid4(), purpose, [])
    selected = unseal(third.encrypted_selection)["selection"]["subject_account"]
    assert selected == [{"row": page1["row"], "fields": [page2_path]}]
    author_client = Client()
    author_client.force_login(author)
    session = author_client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    url = reverse("rights_portability_select", args=[case.pk])
    private_marker = str(page1["fields"][0]["value"]).encode()
    response = author_client.get(url)
    assert response.status_code == 200 and private_marker not in response.content
    assert "no-store" in response["Cache-Control"]
    response = author_client.post(
        url,
        {
            "operation": "catalog",
            "key": uuid4(),
            "version": case.version,
            "review": approval.pk,
            "dataset": "subject_account",
            "row_number": 1,
            "field_page": 1,
            "purpose": purpose,
        },
    )
    assert response.status_code == 200 and private_marker in response.content
    form = response.context["save_form"]
    save_payload = {
        "operation": "save",
        "key": form.initial["key"],
        "token": form.initial["token"],
        "reason": purpose,
        "paths": [page1_path],
    }
    response = author_client.post(url, save_payload)
    assert response.status_code == 200 and private_marker not in response.content
    assert author_client.post(url, save_payload).status_code == 200
    assert private_marker not in author_client.get(url).content
    bad = {**save_payload, "key": uuid4(), "paths": ["/not-on-page"]}
    assert author_client.post(url, bad).status_code == 400
    assert author_client.post(url, {**save_payload, "token": "tampered"}).status_code == 409
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(author)
    session = csrf_client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    assert csrf_client.get(url).status_code == 200
    assert csrf_client.post(url, save_payload).status_code == 403
    assert client.get(url).status_code == 403
    assert RightsPortabilitySelection.objects.count() == 4 and not RightsExport.objects.exists()
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.rights_portability_reset_selection import reset_selection
    from apps.safety.tasks import purge_expired_portability_selections

    latest = RightsPortabilitySelection.objects.filter(request=case).order_by("-version").first()
    RightsPortabilitySelection.objects.filter(pk=latest.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert purge_expired_portability_selections() == 1
    latest.refresh_from_db()
    assert latest.encrypted_selection == "" and latest.purged_at
    actions_before_unconfirmed = RightsAction.objects.count()
    with pytest.raises(ValidationError, match="Explicit confirmation"):
        reset_selection(
            author,
            case.pk,
            case.version,
            approval.pk,
            uuid4(),
            purpose,
            latest.pk,
            latest.version,
            latest.selection_digest,
            False,
        )
    assert RightsAction.objects.count() == actions_before_unconfirmed
    reset_key = uuid4()
    restarted = reset_selection(
        author,
        case.pk,
        case.version,
        approval.pk,
        reset_key,
        purpose,
        latest.pk,
        latest.version,
        latest.selection_digest,
        True,
    )
    assert restarted.version == latest.version + 1
    assert all(rows == [] for rows in unseal(restarted.encrypted_selection)["selection"].values())
    assert (
        reset_selection(
            author,
            case.pk,
            case.version,
            approval.pk,
            reset_key,
            purpose,
            latest.pk,
            latest.version,
            latest.selection_digest,
            True,
        ).pk
        == restarted.pk
    )
    assert RightsAction.objects.filter(operation="selection_reset").count() == 1
    with pytest.raises(ValidationError, match="reset version changed"):
        reset_selection(
            author,
            case.pk,
            case.version,
            approval.pk,
            uuid4(),
            purpose,
            latest.pk,
            latest.version,
            latest.selection_digest,
            True,
        )
    resumed = prepare_page(
        author, case.pk, case.version, approval.pk, uuid4(), purpose, "subject_account"
    )
    assert resumed["chosen"] == []
    assert RightsPortabilitySelection.objects.filter(pk=latest.pk).exists()
    new_assessment = save_assessment(
        author,
        case.pk,
        case.version,
        uuid4(),
        draft.version,
        "Replace synthetic assessment before explicit reset",
        decisions,
    )
    record(reviewer, case.pk, new_assessment.pk, uuid4(), case.version, "inspect", purpose)
    new_approval, _ = record(
        reviewer, case.pk, new_assessment.pk, uuid4(), case.version, "review", purpose, "approved"
    )
    with pytest.raises(ValidationError, match="selection unavailable"):
        prepare_page(
            author, case.pk, case.version, new_approval.pk, uuid4(), purpose, "subject_account"
        )
    response = author_client.get(url)
    reset_form = response.context["reset_form"]
    reset_payload = {
        **reset_form.initial,
        "operation": "reset",
        "review": new_approval.pk,
        "reason": "Explicitly restart synthetic choices under new approved assessment",
    }
    assert author_client.post(url, reset_payload).status_code == 400
    assert (
        RightsPortabilitySelection.objects.filter(request=case).order_by("-version").first().pk
        == restarted.pk
    )
    reset_payload["confirmed"] = "on"
    response = author_client.post(url, reset_payload)
    assert response.status_code == 200 and private_marker not in response.content
    assert author_client.post(url, reset_payload).status_code == 200
    new_empty = RightsPortabilitySelection.objects.filter(request=case).order_by("-version").first()
    assert new_empty.assessment_review_id == new_approval.pk
    assert all(rows == [] for rows in unseal(new_empty.encrypted_selection)["selection"].values())
    prepared_again = prepare_page(
        author, case.pk, case.version, new_approval.pk, uuid4(), purpose, "subject_account"
    )
    assert prepared_again["chosen"] == []
    assert not RightsExport.objects.exists()
    case.refresh_from_db()
    assert case.status == "reviewing"
