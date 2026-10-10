from copy import deepcopy
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client
from django.urls import reverse
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability import assessment
from test_rights_verification import read

from apps.core.models import User
from apps.safety.crypto import seal, unseal
from apps.safety.models import RightsAction, RightsExport, RightsPortabilitySelection
from apps.safety.rights_exports import source_copy
from apps.safety.rights_portability import save_assessment
from apps.safety.rights_portability_review import record
from apps.safety.rights_portability_selected_use import consume_selected
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_review import record as selection_record
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = pytest.mark.django_db(transaction=True)


def test_general_copy_cannot_bypass_portability_selection(request, settings, monkeypatch):
    from apps.safety.models import RightsExportPreview
    from apps.safety.rights_exports import generate, preview

    case, author, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    source = preview(
        author, case.pk, case.version, "Inspect synthetic general copy before rejection"
    )
    assert RightsExportPreview.objects.filter(request=case, actor=author).exists()
    version, status, scope = case.version, case.status, case.scope_status
    count = RightsAction.objects.filter(request=case).count()
    key = uuid4()
    for _ in range(2):
        with pytest.raises(ValidationError, match="approved field selection"):
            generate(
                author, case.pk, key, version, "Attempt unapproved synthetic portability", source
            )
    case.refresh_from_db()
    assert (case.version, case.status, case.scope_status) == (version, status, scope)
    assert RightsAction.objects.filter(request=case).count() == count
    assert not RightsExport.objects.filter(action__request=case).exists()


@pytest.mark.parametrize("packaged", [False, True])
def test_mixed_field_evidence_persists_is_reviewed_and_is_not_delivered(
    request, settings, monkeypatch, packaged
):
    if packaged:
        import test_account_copy_races

        account_factory = test_account_copy_races.account

        def long_account():
            subject = account_factory()
            subject.email = "synthetic" + "x" * 180 + "@example.invalid"
            subject.save(update_fields=["email"])
            return subject

        monkeypatch.setattr(test_account_copy_races, "account", long_account)
    case, author, _, subject, public, receipt = prepared_account(
        request, settings, monkeypatch, "portability"
    )
    if packaged:
        from apps.safety import rights_data_parts

        monkeypatch.setattr(rights_data_parts, "DATA_PART_LIMIT", 256)
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
    eligible_facts = dict(decisions["subject_account"])
    decisions["subject_account"].update(
        status="granular",
        origin="mixed",
        basis="unknown",
        subject_related=None,
        third_party_reviewed=None,
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
    with transaction.atomic():
        source = source_copy(None, None, case)
    selectors = {name: [] for name in decisions}
    ref = row_reference("subject_account", 0, source["subject_account"])
    selectors["subject_account"] = [{"row": ref, "fields": ["/email"]}]
    eligible_facts["evidence"] = "PRIVATE_MIXED_FIELD_EVIDENCE"
    evidence = {"subject_account": {ref: {"/email": eligible_facts}}}
    before = RightsAction.objects.count()
    invalid = deepcopy(evidence)
    invalid["subject_account"][ref]["/email"]["origin"] = "third_party"
    with pytest.raises(ValidationError):
        save_selection(
            author,
            case.pk,
            case.version,
            approval.pk,
            uuid4(),
            0,
            purpose,
            selectors,
            field_evidence=invalid,
        )
    assert (
        RightsAction.objects.count() == before and not RightsPortabilitySelection.objects.exists()
    )
    key = uuid4()
    selected = save_selection(
        author,
        case.pk,
        case.version,
        approval.pk,
        key,
        0,
        purpose,
        selectors,
        field_evidence=evidence,
    )
    assert unseal(selected.encrypted_selection)["field_evidence"] == evidence
    assert (
        save_selection(
            author,
            case.pk,
            case.version,
            approval.pk,
            key,
            0,
            purpose,
            selectors,
            field_evidence=evidence,
        ).pk
        == selected.pk
    )
    modified = deepcopy(evidence)
    modified["subject_account"][ref]["/email"]["reason"] += " changed evidence"
    with pytest.raises(ValidationError, match="Conflicting portability use"):
        save_selection(
            author,
            case.pk,
            case.version,
            approval.pk,
            key,
            0,
            purpose,
            selectors,
            field_evidence=modified,
        )
    from apps.safety.rights_portability_page_selection import prepare_page, save_page

    monkeypatch.setattr("apps.safety.rights_portability_catalog.FIELD_PAGE_SIZE", 1)
    first_page = prepare_page(
        author, case.pk, case.version, approval.pk, uuid4(), purpose, "subject_account"
    )
    assert first_page["granular"] and first_page["fields"][0]["path"] == "/username"
    with pytest.raises(ValidationError, match="exact decisions"):
        save_page(author, case.pk, first_page["token"], uuid4(), purpose, ["/username"])
    username_facts = deepcopy(eligible_facts)
    selected = save_page(
        author,
        case.pk,
        first_page["token"],
        uuid4(),
        purpose,
        ["/username"],
        field_decisions={"/username": username_facts},
    )
    stored = unseal(selected.encrypted_selection)
    assert set(stored["field_evidence"]["subject_account"][ref]) == {"/email", "/username"}
    assert stored["field_evidence"]["subject_account"][ref]["/email"] == eligible_facts
    email_page = prepare_page(
        author,
        case.pk,
        case.version,
        approval.pk,
        uuid4(),
        purpose,
        "subject_account",
        field_page=2,
    )
    assert email_page["field_decisions"] == {"/email": eligible_facts}
    observed = deepcopy(eligible_facts)
    observed["origin"] = "observed"
    selected = save_page(
        author,
        case.pk,
        email_page["token"],
        uuid4(),
        purpose,
        ["/email"],
        field_decisions={"/email": observed},
    )
    first_page = prepare_page(
        author, case.pk, case.version, approval.pk, uuid4(), purpose, "subject_account"
    )
    selected = save_page(author, case.pk, first_page["token"], uuid4(), purpose, [])
    evidence = {"subject_account": {ref: {"/email": observed}}}
    assert unseal(selected.encrypted_selection)["field_evidence"] == evidence
    author_client = Client()
    author_client.force_login(author)
    session = author_client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    prepare_url = reverse("rights_portability_select", args=[case.pk])
    response = author_client.post(
        prepare_url,
        {
            "operation": "catalog",
            "key": uuid4(),
            "version": case.version,
            "review": approval.pk,
            "dataset": "subject_account",
            "row_number": 1,
            "field_page": 2,
            "purpose": purpose,
        },
    )
    assert response.status_code == 200
    fields = response.context["field_forms"]
    assert len(fields.forms) == 1 and fields.forms[0]["origin"].value() == "observed"
    form = response.context["save_form"]
    payload = {
        "operation": "save",
        "key": form.initial["key"],
        "token": form.initial["token"],
        "reason": purpose,
        "paths": ["/email"],
        "fields-TOTAL_FORMS": 1,
        "fields-INITIAL_FORMS": 1,
        "fields-MIN_NUM_FORMS": 0,
        "fields-MAX_NUM_FORMS": 50,
    }
    for name in fields.forms[0].fields:
        payload["fields-0-" + name] = fields.forms[0][name].value()
    before_invalid_form = RightsAction.objects.count()
    assert (
        author_client.post(prepare_url, {**payload, "fields-0-origin": "third_party"}).status_code
        == 400
    )
    assert (
        author_client.post(prepare_url, {**payload, "fields-0-path": "/username"}).status_code
        == 400
    )
    assert RightsAction.objects.count() == before_invalid_form
    payload["fields-0-basis"] = "consent"
    response = author_client.post(prepare_url, payload)
    assert response.status_code == 200 and b"PRIVATE_MIXED_FIELD_EVIDENCE" not in response.content
    assert author_client.post(prepare_url, payload).status_code == 200
    assert b"PRIVATE_MIXED_FIELD_EVIDENCE" not in author_client.get(prepare_url).content
    selected = RightsPortabilitySelection.objects.filter(request=case).order_by("-version").first()
    evidence["subject_account"][ref]["/email"]["basis"] = "consent"
    assert unseal(selected.encrypted_selection)["field_evidence"] == evidence
    read_key = uuid4()
    inspected, projected = selection_record(
        reviewer, case.pk, case.version, selected.pk, read_key, purpose
    )
    assert projected["field_evidence"] == evidence
    path = reverse("rights_portability_selection_review", args=[case.pk, selected.pk])
    assert b"PRIVATE_MIXED_FIELD_EVIDENCE" not in client.get(path).content
    # The HTTP inspection is paginated and uses its own key; the service read key stays bound
    # to the unpaginated inspection recorded above.
    page_inspection = {
        "key": uuid4(),
        "version": case.version,
        "operation": "inspect",
        "reason": purpose,
        "outcome": "",
    }
    response = client.post(path, page_inspection)
    assert response.status_code == 200 and b"PRIVATE_MIXED_FIELD_EVIDENCE" in response.content
    replay = client.post(path, page_inspection)
    assert replay.status_code == 200 and b"PRIVATE_MIXED_FIELD_EVIDENCE" in replay.content
    assert client.post(path, {**page_inspection, "key": read_key}).status_code == 409
    decision, _ = selection_record(
        reviewer, case.pk, case.version, selected.pk, uuid4(), purpose, "review", "approved"
    )
    _, output = consume_selected(
        author, case.pk, case.version, selected.pk, decision.pk, uuid4(), purpose
    )
    assert output["datasets"]["subject_account"] == [
        {"fields": {"/email": source["subject_account"]["email"]}}
    ]
    assert "field_evidence" not in output and "PRIVATE_MIXED_FIELD_EVIDENCE" not in str(output)
    assert not RightsExport.objects.exists()
    case.refresh_from_db()
    assert case.status == "reviewing"

    from apps.safety.rights_portability_export import generate, validate_export_binding

    version = case.version
    key = uuid4()
    export_url = reverse("rights_portability_export", args=[case.pk])
    before_exports = RightsExport.objects.count()
    response = author_client.get(export_url)
    assert response.status_code == 200 and b"PRIVATE_MIXED_FIELD_EVIDENCE" not in response.content
    assert RightsExport.objects.count() == before_exports
    export_form = {"key": key, "version": version, "review": decision.pk, "reason": purpose}
    protected = Client(enforce_csrf_checks=True)
    protected.cookies = author_client.cookies.copy()
    assert protected.get(export_url).status_code == 200
    assert protected.post(export_url, export_form).status_code == 403
    assert RightsExport.objects.count() == before_exports
    from apps.safety import rights_portability_jobs as jobs
    from apps.safety.models import RightsPortabilityExportJob

    monkeypatch.setattr(jobs, "dispatch", lambda job_id: True)
    response = author_client.post(export_url, export_form)
    assert response.status_code == 302 and b"PRIVATE_MIXED_FIELD_EVIDENCE" not in response.content
    assert RightsExport.objects.count() == before_exports
    job = RightsPortabilityExportJob.objects.get(key=key)
    jobs.run(job.pk)
    job.refresh_from_db()
    assert job.state == "succeeded"
    exported = RightsExport.objects.get(action__key=key)
    assert author_client.post(export_url, export_form).status_code == 302
    if packaged:
        assert exported.parts.exists()
        assert unseal(exported.encrypted_payload)["schema"] == "rights-data-manifest-v1"
    else:
        assert unseal(exported.encrypted_payload)["datasets"] == output["datasets"]
    assert "PRIVATE_MIXED_FIELD_EVIDENCE" not in str(unseal(exported.encrypted_payload))
    assert (
        generate(author, case.pk, version, selected.pk, decision.pk, key, purpose).pk == exported.pk
    )
    case.refresh_from_db()
    assert case.version == version + 1 and case.status == "reviewing"
    with transaction.atomic():
        validate_export_binding(case, None, exported)
    from test_rights_exports import url

    from apps.safety.models import RightsExportDownload

    download_key = uuid4()
    response = public.post(url(receipt, exported), {"key": download_key})
    assert response.status_code == 200
    assert b"PRIVATE_MIXED_FIELD_EVIDENCE" not in response.content
    before_downloads = RightsExportDownload.objects.count()
    original_reason = exported.action.encrypted_reason
    exported.action.encrypted_reason = seal({})
    exported.action.save(update_fields=["encrypted_reason"])
    assert public.post(url(receipt, exported), {"key": uuid4()}).status_code == 404
    assert RightsExportDownload.objects.count() == before_downloads
    with pytest.raises(ValidationError, match="reason unavailable"):
        generate(author, case.pk, version, selected.pk, decision.pk, key, purpose)
    exported.action.encrypted_reason = original_reason
    exported.action.save(update_fields=["encrypted_reason"])
    if packaged:
        part = exported.parts.order_by("position").first()
        original_content = part.encrypted_content
        part.encrypted_content = exported.encrypted_payload
        part.save(update_fields=["encrypted_content"])
        assert public.post(url(receipt, exported), {"key": uuid4()}).status_code == 404
        assert RightsExportDownload.objects.count() == before_downloads
        part.encrypted_content = original_content
        part.save(update_fields=["encrypted_content"])
    exported.encrypted_payload = selected.encrypted_selection
    exported.save(update_fields=["encrypted_payload"])
    with transaction.atomic(), pytest.raises(ValidationError, match="binding changed"):
        validate_export_binding(case, None, exported)
    assert public.post(url(receipt, exported), {"key": uuid4()}).status_code == 404
    assert RightsExportDownload.objects.count() == before_downloads
