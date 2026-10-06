from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccessCoverage, RightsAction
from apps.safety.rights import fingerprint
from apps.safety.rights_access_coverage import UNPROJECTED
from apps.safety.rights_access_coverage_store import required_references, save
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import canonical, generate, preview
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("reference_page", [False, True])
def test_audited_coverage_preserves_open_request_and_rejects_stale_replay(
    request, settings, monkeypatch, account_only, live_server, reference_page
):
    case, author, staff, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    reason = "Synthetic coverage preparation with exact evidence references"
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    source = preview(author, case.pk, case.version, reason)
    if reference_page:
        from test_rights_copy_compilation import review_all

        review_all(case, author)
    export = generate(
        author, case.pk, uuid4(), case.version, reason, source, information_review_id=decision.pk
    )
    delivered = unseal(export.encrypted_payload)
    verifier = User.objects.get(username="fixture-v1-visitor")
    verifier.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    verifier = User.objects.get(pk=verifier.pk)
    fresh(case, author, staff, verifier, operator(verifier))
    declarations = {
        "sections": {
            section: [
                {
                    "row": row_reference(section, index, row),
                    "delivered_index": index,
                    "decisions": {},
                }
                for index, row in enumerate(project(source))
            ]
            for section, project in SECTIONS.items()
        },
        "boundaries": {
            name: {
                "status": "excluded",
                "reason": "Synthetic declaration awaiting independent evidence validation",
                "evidence": "Synthetic referenced information review, not final approval",
            }
            for name in set(source["pending_review"])
            | set(delivered["pending_review"])
            | UNPROJECTED
        },
    }
    action = decision.action
    page_evidence = None
    if reference_page:
        from apps.safety.models import RightsCopyPageReview

        page_evidence = (
            RightsCopyPageReview.objects.filter(request=case, actor=author).order_by("pk").first()
        )
        action = page_evidence.action
    snapshot = {
        "action": action.pk,
        "request": str(action.request_id),
        "actor": action.actor_id,
        "version": action.expected_version,
        "operation": action.operation,
        "payload": action.payload_digest,
        "reason_ciphertext": fingerprint(action.encrypted_reason),
    }
    refs = {
        label: {"action": action.pk, "digest": fingerprint(canonical(snapshot))}
        for label in required_references(declarations)
    }
    key = uuid4()

    def invoke():
        return save(
            author,
            case.pk,
            case.version,
            case.response_version,
            export.pk,
            key,
            reason,
            delivered,
            declarations,
            refs,
            fingerprint(canonical(source)),
            fingerprint(canonical(delivered)),
        )

    import apps.safety.rights_access_coverage_store as module

    real_validate = module.validate_transport

    def audited(*args):
        assert RightsAction.objects.filter(key=key, operation="access_coverage").exists()
        return real_validate(*args)

    monkeypatch.setattr(module, "validate_transport", audited)
    original = case.version, case.response_version, case.status
    row = invoke()
    assert invoke().pk == row.pk
    assert reason not in row.encrypted_coverage
    assert unseal(row.encrypted_coverage)["bound_references"]
    from django.core.exceptions import PermissionDenied
    from test_rights_verification import read

    from apps.safety.rights_access_coverage_review import inspect, record

    verifier.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    verifier = User.objects.get(pk=verifier.pk)
    read(operator(verifier), case)
    with pytest.raises(PermissionDenied):
        inspect(author, case.pk, case.version, row.pk, uuid4(), reason)
    with pytest.raises(ValidationError, match="Inspect exact"):
        record(verifier, case.pk, case.version, row.pk, 0, uuid4(), reason, "approved")
    read_key = uuid4()
    inspected, body, audited_read = inspect(
        verifier, case.pk, case.version, row.pk, read_key, reason
    )
    assert inspected.pk == row.pk and body["accounting"]
    decision_key = uuid4()
    approved = record(
        verifier, case.pk, case.version, row.pk, audited_read.pk, decision_key, reason, "approved"
    )
    assert (
        record(
            verifier,
            case.pk,
            case.version,
            row.pk,
            audited_read.pk,
            decision_key,
            reason,
            "approved",
        ).pk
        == approved.pk
    )
    with pytest.raises(ValidationError, match="already reviewed"):
        record(
            verifier, case.pk, case.version, row.pk, audited_read.pk, uuid4(), reason, "rejected"
        )
    from django.test import Client
    from django.urls import reverse

    path = reverse("rights_access_coverage_review", args=[case.pk, row.pk])
    other = operator(verifier)
    inspection_path = reverse("rights_inspect", args=[case.pk])
    assert path in other.get(inspection_path).content.decode()
    assert path not in staff.get(inspection_path).content.decode()
    before = RightsAction.objects.count()
    assert other.get(path).status_code == 200
    assert "Synthetic declaration awaiting" not in other.get(path).content.decode()
    assert RightsAction.objects.count() == before
    assert staff.get(path).status_code == 403
    assert Client().get(path).status_code == 302
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(verifier)
    assert csrf.post(path, {}).status_code == 403
    response = other.post(
        path, {"operation": "inspect", "key": read_key, "version": case.version, "reason": reason}
    )
    assert (
        response.status_code == 200
        and "Synthetic declaration awaiting" in response.content.decode()
    )
    response = other.post(
        path,
        {
            "operation": "review",
            "key": decision_key,
            "version": case.version,
            "read_id": audited_read.pk,
            "reason": reason,
            "outcome": "approved",
        },
    )
    assert (
        response.status_code == 200
        and "Synthetic declaration awaiting" not in response.content.decode()
    )
    import shutil

    from django.conf import settings as django_settings
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": other.cookies[django_settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            from django.utils import translation

            with translation.override("es"):
                browser_path = reverse("rights_access_coverage_review", args=[case.pk, row.pk])
            page.goto(live_server.url + browser_path)
            assert "Synthetic declaration awaiting" not in page.locator("body").inner_text()
            page.locator("#id_reason").fill(reason)
            page.get_by_role("button", name="Consultar cobertura", exact=True).click()
            expect(page.locator("body")).to_contain_text("Registros originales del alcance")
            expect(page.locator("body")).to_contain_text("Copia exacta entregada")
            assert "Synthetic declaration awaiting" in page.locator("body").inner_text()
            overflow = page.evaluate(
                """() => Array.from(document.querySelectorAll('*')).filter(el => el.getBoundingClientRect().right > innerWidth + 1 || el.scrollWidth > el.clientWidth + 1).map(el => ({tag: el.tagName, id: el.id, class: el.className, right: el.getBoundingClientRect().right, width: el.getBoundingClientRect().width, whiteSpace: getComputedStyle(el).whiteSpace, overflowWrap: getComputedStyle(el).overflowWrap}))"""
            )
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), overflow
            page.goto(page.url)
            assert "Synthetic declaration awaiting" not in page.locator("body").inner_text()
        finally:
            browser.close()
    from apps.safety.rights_access_coverage_use import consume

    use_key = uuid4()
    import apps.safety.rights_access_reference_bodies as evidence_module

    real_body = evidence_module.checked_body

    def audited_evidence(ciphertext):
        assert RightsAction.objects.filter(key=use_key, operation="access_cover_use").exists()
        return real_body(ciphertext)

    monkeypatch.setattr(evidence_module, "checked_body", audited_evidence)
    used, evidence_body = consume(
        author, case.pk, case.version, case.response_version, approved.pk, use_key, reason
    )
    assert used.pk == approved.pk and evidence_body["evidence_bodies"]
    assert (
        consume(author, case.pk, case.version, case.response_version, approved.pk, use_key, reason)[
            0
        ].pk
        == approved.pk
    )
    from django.db import transaction

    from apps.safety.rights_access_response_draft import prepare as prepare_response
    from apps.safety.rights_access_response_evidence import validate_draft

    response_text = "Synthetic reviewed access explanation linked to this private copy and its explicit accounting decisions. Further scope validation remains required."
    response_key = uuid4()
    response_draft = prepare_response(
        author,
        case.pk,
        case.version,
        case.response_version,
        export.pk,
        response_key,
        reason,
        response_text,
        True,
        coverage_review_id=approved.pk,
    )
    assert response_draft.coverage_review_id == approved.pk
    response_path = reverse("rights_access_response_prepare", args=[case.pk])
    response_page = staff.post(
        response_path,
        {
            "key": response_key,
            "version": case.version,
            "response_version": case.response_version,
            "export": export.pk,
            "coverage_review": approved.pk,
            "reason": reason,
            "response": response_text,
            "redaction_confirmed": True,
        },
    )
    assert response_page.status_code == 200
    assert response_text not in response_page.content.decode()
    with transaction.atomic():
        assert (
            validate_draft(response_draft, case, None if account_only else case.person)["text"]
            == response_text
        )
    original_session = verifier.session_version
    User.objects.filter(pk=verifier.pk).update(session_version=original_session + 1)
    with pytest.raises(PermissionDenied):
        consume(author, case.pk, case.version, case.response_version, approved.pk, use_key, reason)
    User.objects.filter(pk=verifier.pk).update(session_version=original_session)
    if page_evidence:
        original_entries = page_evidence.encrypted_entries
        page_evidence.encrypted_entries = module.seal([{"injected": "Synthetic altered page body"}])
        page_evidence.save(update_fields=["encrypted_entries"])
        with pytest.raises(ValidationError):
            consume(
                author, case.pk, case.version, case.response_version, approved.pk, use_key, reason
            )
        page_evidence.encrypted_entries = original_entries
        page_evidence.save(update_fields=["encrypted_entries"])
    monkeypatch.setattr(evidence_module, "checked_body", real_body)
    approved.accounting_digest = "0" * 64
    approved.save(update_fields=["accounting_digest"])
    with pytest.raises(ValidationError, match="signatures changed"):
        consume(author, case.pk, case.version, case.response_version, approved.pk, use_key, reason)
    with pytest.raises(ValidationError, match="evidence changed"):
        record(
            verifier,
            case.pk,
            case.version,
            row.pk,
            audited_read.pk,
            decision_key,
            reason,
            "approved",
        )
    row.binding_digest = "0" * 64
    row.save(update_fields=["binding_digest"])
    with pytest.raises(ValidationError, match="references changed"):
        invoke()
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status) == original
    assert RightsAccessCoverage.objects.count() == 1
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.tasks import purge_expired_access_coverage

    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save(update_fields=["expires_at"])
    assert purge_expired_access_coverage() == 1
    assert purge_expired_access_coverage() == 0
    row.refresh_from_db()
    assert row.purged_at and not row.encrypted_coverage
