from pathlib import Path
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
    request,
    settings,
    monkeypatch,
    account_only,
    live_server,
    reference_page,
    tmp_path,
    finish=False,
    finish_mode="http",
    finish_language="en",
    retained_expired_session=False,
    retained_console_mail=False,
):
    case, author, staff, public, receipt, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    console_output = ""
    if retained_console_mail:
        import io
        from contextlib import redirect_stdout

        from apps.core.accounts import send_token

        # Real local console backend; no external mail transport.
        settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        console_stream = io.StringIO()
        with redirect_stdout(console_stream):
            send_token(
                User.objects.get(pk=case.account_subject_id or case.person.subject_id),
                "verify",
                "en",
            )
        console_output = console_stream.getvalue()
    retained_session = None
    if retained_expired_session:
        from datetime import timedelta

        from django.contrib.sessions.backends.db import SessionStore
        from django.utils import timezone

        retained_session = SessionStore()
        retained_session["_auth_user_id"] = str(case.account_subject_id or case.person.subject_id)
        retained_session["_auth_user_hash"] = "synthetic-expired-capability-not-for-delivery"
        retained_session["django_language"] = "en"
        retained_session.set_expiry(timezone.now() - timedelta(days=1))
        retained_session.save()
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
    if not reference_page:
        from apps.safety.rights_access_close import close
        from apps.safety.rights_access_delivery import snapshot
        from apps.safety.rights_access_response_review import inspect as inspect_response
        from apps.safety.rights_access_response_review import record as review_response
        from apps.safety.rights_access_scope_store import inspect as inspect_scope

        inventory, _ = inspect_scope(
            author, case.pk, case.version, case.response_version, uuid4(), reason
        )
        import json

        from django.utils import timezone
        from test_rights_access_recipient_payload import synthetic_log_bundle

        from scripts.collect_access_resource_logs import (
            scoped_origin_name,
            signed_subject_log_event,
            subject_log_signature,
            write_bundle,
        )

        event = signed_subject_log_event(
            "account" if account_only else "person",
            case.account_subject_id if account_only else case.person_id,
            "profile_updated",
            "succeeded",
            inventory.created_at,
        )
        log_content = "".join(
            f"{inventory.created_at.isoformat()} {line}\n" for line in console_output.splitlines()
        )
        log_content += f"{inventory.created_at.isoformat()} {json.dumps(event)}\n"
        log_content += f"{inventory.created_at.isoformat()} {json.dumps(event | {'subject_id': str(uuid4())})}\n"
        archive_directory = tmp_path / "operational-fixture"
        archive_directory.mkdir(mode=0o700)
        archive_path = write_bundle(
            archive_directory,
            synthetic_log_bundle(timezone.now(), log_content),
            case_id=case.pk,
            inventory_id=inventory.pk,
        )
        settings.ACCESS_LOG_ORIGIN_BUNDLE = str(archive_directory)
        with transaction.atomic():
            original_scope = snapshot(
                case,
                None if account_only else case.person,
                inventory,
                cutoff=inventory.created_at,
                projected=evidence_body["delivered"],
            )
        assert not original_scope["blocked"], original_scope["blocked"]
        assert len(original_scope["groups"]["operations.LogEvent"]) == 1
        assert not original_scope["log_origins"]["unprojected_candidates"]
        if retained_console_mail:
            assert len(original_scope["log_origins"]["projected_mail"]) == 1
            assert any(
                row["data"]["body"].endswith("[redacted]")
                for row in original_scope["groups"]["operations.Mail"]
            )
        original_operation = inventory.action.operation
        inventory.action.operation = "access_draft"
        inventory.action.save(update_fields=["operation"])
        with transaction.atomic(), pytest.raises(ValidationError, match="inspection evidence"):
            snapshot(
                case,
                None if account_only else case.person,
                inventory,
                cutoff=inventory.created_at,
                projected=evidence_body["delivered"],
            )
        inventory.action.operation = original_operation
        inventory.action.save(update_fields=["operation"])
        from apps.safety.models import RightsAccessResponseDraft

        drafts_before = RightsAccessResponseDraft.objects.count()
        preview_key = uuid4()
        preview_values = {
            "operation": "inspect_package",
            "key": preview_key,
            "version": case.version,
            "response_version": case.response_version,
            "export": export.pk,
            "coverage_review": approved.pk,
            "scope_inventory": inventory.pk,
            "reason": reason,
            "response": response_text,
            "redaction_confirmed": True,
        }
        package_page = staff.post(response_path, preview_values)
        assert package_page.status_code == 200, package_page.content.decode()
        assert package_page.context["package_preview"] == original_scope
        assert "Original access package" in package_page.content.decode()
        from django.utils import translation

        with translation.override("es"):
            spanish_path = reverse("rights_access_response_prepare", args=[case.pk])
        spanish_page = staff.post(spanish_path, preview_values)
        assert spanish_page.status_code == 200
        assert "Paquete original de acceso" in spanish_page.content.decode()
        assert spanish_page.context["package_preview"] == original_scope
        assert RightsAccessResponseDraft.objects.count() == drafts_before
        assert not RightsAction.objects.filter(key=preview_key, operation="access_draft").exists()
        assert staff.post(response_path, preview_values).status_code == 200
        assert other.post(response_path, preview_values).status_code == 403
        action_count = RightsAction.objects.count()
        page_reload = staff.get(response_path)
        assert page_reload.status_code == 200
        assert page_reload.context["package_preview"] is None
        assert RightsAction.objects.count() == action_count
        decisions = {
            "models": {
                label: {"status": "included", "reason": reason}
                for label in original_scope["groups"]
            },
            "resources": {"status": "reviewed", "reason": reason},
        }
        candidates = [
            (label, row, field, value)
            for label, rows in original_scope["groups"].items()
            for row in rows
            for field, value in row["data"].items()
        ]
        redacted_model, redacted_row, redacted_field, original_value = next(
            (item for item in candidates if isinstance(item[3], str) and len(item[3]) > 3),
            candidates[0],
        )
        redacted_value = (
            original_value[:1] + "[redacted]"
            if isinstance(original_value, str) and len(original_value) > 3
            else None
        )
        field_change = (
            {"status": "omitted", "reason": reason}
            if redacted_value is None
            else {"status": "redacted", "reason": reason, "value": redacted_value}
        )
        decisions["models"][redacted_model] = {
            "status": "redacted",
            "reason": reason,
            "changes": {redacted_row["reference"]: {redacted_field: field_change}},
        }
        package_draft = prepare_response(
            author,
            case.pk,
            case.version,
            case.response_version,
            export.pk,
            uuid4(),
            reason,
            response_text,
            True,
            coverage_review_id=approved.pk,
            scope_inventory_id=inventory.pk,
            delivery_decisions=decisions,
        )
        with transaction.atomic():
            package_body = validate_draft(
                package_draft, case, None if account_only else case.person
            )
        assert package_body["access_package"]["pending"] == ["infrastructure_content_accounting"]
        delivered_group = next(
            group
            for group in package_body["access_package"]["copy"]["additional_records"]
            if group["model"] == redacted_model
        )
        delivered_row = next(
            row
            for row in delivered_group["records"]
            if row["reference"] == redacted_row["reference"]
        )
        if redacted_value is None:
            assert redacted_field not in delivered_row["data"]
        else:
            assert delivered_row["data"][redacted_field] == redacted_value
        assert redacted_row["data"][redacted_field] == original_value
        package_read_key = uuid4()
        _, inspected_package = inspect_response(
            verifier, case.pk, case.version, package_draft.pk, package_read_key, reason
        )
        assert inspected_package["access_package"] == package_body["access_package"]
        package_review = review_response(
            verifier,
            case.pk,
            case.version,
            package_draft.pk,
            RightsAction.objects.get(key=package_read_key).pk,
            uuid4(),
            reason,
            "approved",
        )
        import hashlib

        original_archive = archive_path.read_text()
        changed_archive = unseal(original_archive)
        changed_lines = []
        for line in changed_archive["records"][0]["stdout"].splitlines():
            timestamp, content = line.split(" ", 1)
            try:
                changed_event = json.loads(content)
            except ValueError:
                # Preserve captured MIME lines when testing signed-event drift.
                changed_lines.append(line + "\n")
                continue
            changed_event["outcome"] = "failed"
            changed_event["signature"] = subject_log_signature(changed_event)
            changed_lines.append(f"{timestamp} {json.dumps(changed_event)}\n")
        changed_archive["records"][0]["stdout"] = "".join(changed_lines)
        changed_archive["records"][0]["stdout_sha256"] = hashlib.sha256(
            changed_archive["records"][0]["stdout"].encode()
        ).hexdigest()
        archive_path.write_text(module.seal(changed_archive))
        with (
            transaction.atomic(),
            pytest.raises(ValidationError, match="package contents|original records"),
        ):
            validate_draft(package_draft, case, None if account_only else case.person)
        archive_path.write_text(original_archive)
        with pytest.raises(ValidationError, match="Complete reviewed access delivery"):
            close(
                author,
                case.pk,
                case.version,
                case.response_version,
                package_review.pk,
                uuid4(),
                reason,
            )
        source_cipher = package_draft.encrypted_response
        altered = package_body | {
            "access_package": package_body["access_package"] | {"pending": [], "partial": False}
        }
        package_draft.encrypted_response = module.seal(altered)
        package_draft.save(update_fields=["encrypted_response"])
        with transaction.atomic(), pytest.raises(ValidationError, match="package contents"):
            validate_draft(package_draft, case, None if account_only else case.person)
        package_draft.encrypted_response = source_cipher
        package_draft.save(update_fields=["encrypted_response"])
    if finish:
        from test_rights_access_recipient_payload import synthetic_resource_census
        from test_rights_exports import url

        from apps.safety.models import RightsAccessClosure, RightsNotice, RightsResponse
        from apps.safety.rights_access_delivery import recipient_payload

        census_body = synthetic_resource_census(case, inventory, original_scope)
        census_path = tmp_path / scoped_origin_name("resources", case.pk, inventory.pk)
        census_path.write_text(module.seal(census_body))
        census_path.chmod(0o600)
        settings.ACCESS_RESOURCE_ORIGIN_BUNDLE = str(tmp_path)
        with transaction.atomic():
            completed_scope = snapshot(
                case,
                None if account_only else case.person,
                inventory,
                cutoff=inventory.created_at,
                projected=evidence_body["delivered"],
            )
        assert completed_scope["resource_scope"]["pending"] == []
        completed_decisions = decisions | {
            "resources": {
                "status": "reviewed",
                "reason": reason,
                "origin_digest": completed_scope["resource_scope"]["digest"],
            },
        }
        completed_draft = prepare_response(
            author,
            case.pk,
            case.version,
            case.response_version,
            export.pk,
            uuid4(),
            reason,
            response_text,
            True,
            coverage_review_id=approved.pk,
            scope_inventory_id=inventory.pk,
            delivery_decisions=completed_decisions,
        )
        completed_read_key = uuid4()
        _, completed_body = inspect_response(
            verifier, case.pk, case.version, completed_draft.pk, completed_read_key, reason
        )
        assert completed_body["access_package"]["pending"] == []
        assert completed_body["access_package"]["partial"] is False
        completed_review = review_response(
            verifier,
            case.pk,
            case.version,
            completed_draft.pk,
            RightsAction.objects.get(key=completed_read_key).pk,
            uuid4(),
            reason,
            "approved",
        )
        close_path = reverse("rights_access_close", args=[case.pk, completed_review.pk])
        before = RightsResponse.objects.count(), RightsNotice.objects.count()
        assert other.get(close_path).status_code == 403
        action_count = RightsAction.objects.count()
        assert staff.get(close_path).status_code == 200
        assert RightsAction.objects.count() == action_count
        close_values = {
            "key": uuid4(),
            "version": case.version,
            "response_version": case.response_version,
            "reason": reason,
        }
        if finish_mode == "concurrent":
            from concurrent.futures import ThreadPoolExecutor
            from copy import deepcopy
            from threading import Barrier

            from django.db import connections

            barrier = Barrier(2)
            cookies = deepcopy(staff.cookies)

            def competing_close():
                client = Client()
                client.cookies = deepcopy(cookies)
                try:
                    barrier.wait(timeout=10)
                    result = client.post(close_path, close_values)
                    return result.status_code, result.content.decode()
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: competing_close(), range(2)))
            assert all(status == 200 for status, _ in results), results
        elif finish_mode == "browser":
            with translation.override(finish_language):
                browser_close_path = reverse(
                    "rights_access_close", args=[case.pk, completed_review.pk]
                )
                browser_receipt = receipt.replace("/en/", f"/{finish_language}/", 1)
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
                                "value": staff.cookies[django_settings.SESSION_COOKIE_NAME].value,
                                "url": live_server.url,
                            }
                        ]
                    )
                    page = context.new_page()
                    page.goto(live_server.url + browser_close_path)
                    page.locator("#id_key").evaluate(
                        "(element, value) => element.value = value", str(close_values["key"])
                    )
                    page.locator("#id_reason").fill(reason)
                    page.get_by_role(
                        "button",
                        name=(
                            "Emitir respuesta y cerrar"
                            if finish_language == "es"
                            else "Issue response and close"
                        ),
                        exact=True,
                    ).click()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Respuesta final emitida"
                        if finish_language == "es"
                        else "Final response issued"
                    )
                    public_page = browser.new_page(viewport={"width": 390, "height": 844})
                    public_page.goto(live_server.url + browser_receipt)
                    expect(public_page.locator("body")).to_contain_text(
                        "Paquete de acceso aprobado"
                        if finish_language == "es"
                        else "Reviewed access package"
                    )
                    expect(public_page.locator("body")).to_contain_text(response_text)
                    assert not public_page.evaluate(
                        "() => document.documentElement.scrollWidth > window.innerWidth"
                    )
                    with public_page.expect_download() as downloaded_file:
                        public_page.get_by_role(
                            "button",
                            name=(
                                "Descargar copia privada"
                                if finish_language == "es"
                                else "Download private copy"
                            ),
                            exact=True,
                        ).click()
                    assert json.loads(
                        Path(downloaded_file.value.path()).read_text()
                    ) == recipient_payload(completed_body)
                finally:
                    browser.close()
        else:
            closing = staff.post(close_path, close_values)
            assert closing.status_code == 200, closing.content.decode()
        assert staff.post(close_path, close_values).status_code == 200
        assert staff.post(close_path, close_values | {"key": uuid4()}).status_code == 409
        case.refresh_from_db()
        assert (case.version, case.response_version, case.status) == (
            original[0] + 1,
            original[1] + 1,
            "resolved",
        )
        assert RightsAccessClosure.objects.count() == 1
        assert (RightsResponse.objects.count(), RightsNotice.objects.count()) == (
            before[0] + 1,
            before[1] + 1,
        )
        downloaded = public.post(url(receipt, export), {"key": uuid4()})
        assert downloaded.status_code == 200, downloaded.content.decode()
        assert downloaded.json() == recipient_payload(completed_body)
        assert downloaded.json()["simulation"] is True
        if retained_session is not None:
            session_copy = downloaded.json()["copy"]["sessions"]
            assert any(
                row["expired_at_cutoff"] and row.get("language") == "en" for row in session_copy
            )
            assert retained_session.session_key not in downloaded.content.decode()
            assert (
                "synthetic-expired-capability-not-for-delivery" not in downloaded.content.decode()
            )
        if retained_console_mail:
            assert "Single-use link" in downloaded.content.decode()
            assert "/account/token/" not in downloaded.content.decode()
        assert "review_material" not in downloaded.content.decode()
        assert "origin_digest" not in downloaded.content.decode()
        assert public.post(url(receipt, export), {"key": uuid4()}).json() == downloaded.json()
        from apps.safety.rights import case_export_forms

        assert [item["id"] for item in case_export_forms(case)] == [export.pk]
        for user in (author, verifier):
            for field in ("session_version", "mfa_version"):
                original_epoch = getattr(user, field)
                User.objects.filter(pk=user.pk).update(**{field: original_epoch + 1})
                assert public.post(url(receipt, export), {"key": uuid4()}).status_code == 404
                User.objects.filter(pk=user.pk).update(**{field: original_epoch})
        source_ciphertext = census_path.read_text()
        changed_census = unseal(source_ciphertext)
        changed_census["categories"]["backups"]["reason"] += " altered"
        census_path.write_text(module.seal(changed_census))
        assert public.post(url(receipt, export), {"key": uuid4()}).status_code == 404
        census_path.write_text(source_ciphertext)
        assert public.post(url(receipt, export), {"key": uuid4()}).json() == downloaded.json()
        return
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


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("language", ["es", "en"])
def test_integrated_access_closes_and_downloads_a_reviewed_scoped_resource_fixture(
    request, settings, monkeypatch, account_only, live_server, tmp_path, language
):
    test_audited_coverage_preserves_open_request_and_rejects_stale_replay(
        request,
        settings,
        monkeypatch,
        account_only,
        live_server,
        False,
        tmp_path,
        finish=True,
        finish_mode="browser",
        finish_language=language,
    )


@pytest.mark.parametrize("account_only", [False, True])
def test_integrated_access_concurrent_closure_has_one_response_and_notice(
    request, settings, monkeypatch, account_only, live_server, tmp_path
):
    test_audited_coverage_preserves_open_request_and_rejects_stale_replay(
        request,
        settings,
        monkeypatch,
        account_only,
        live_server,
        False,
        tmp_path,
        finish=True,
        finish_mode="concurrent",
    )


@pytest.mark.parametrize("account_only", [False, True])
def test_integrated_access_includes_retained_expired_session_without_capabilities(
    request, settings, monkeypatch, account_only, live_server, tmp_path
):
    test_audited_coverage_preserves_open_request_and_rejects_stale_replay(
        request,
        settings,
        monkeypatch,
        account_only,
        live_server,
        False,
        tmp_path,
        finish=True,
        retained_expired_session=True,
    )


@pytest.mark.parametrize("account_only", [False, True])
def test_integrated_access_includes_console_mail_without_authentication_link(
    request, settings, monkeypatch, account_only, live_server, tmp_path
):
    test_audited_coverage_preserves_open_request_and_rejects_stale_replay(
        request,
        settings,
        monkeypatch,
        account_only,
        live_server,
        False,
        tmp_path,
        finish=True,
        retained_console_mail=True,
    )
