"""Independent plan inspection and decision through actual mobile sessions ES/EN."""

import json
import shutil
from uuid import uuid4

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.db import transaction
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_copy_information_localization import review_captions
from test_image_selection_form_localization import image_catalog_captions, image_save_captions
from test_portability_export_localization import export_captions
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability import assessment
from test_rights_responses import ready
from test_rights_verification import read
from test_scalar_selection_form_localization import catalog_captions

from apps.core.mfa import encrypt
from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsExport,
    RightsExportDownload,
    RightsPortabilitySelectionReview,
)
from apps.safety.rights_exports import source_copy
from apps.safety.rights_portability import save_assessment
from apps.safety.rights_portability_review import record

REASON = "PRIVATE_SYNTHETIC_REVIEW_INFORMATION"
FIELD_EVIDENCE = "PRIVATE_SYNTHETIC_FIELD_ELIGIBILITY"

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "account_only,include_images",
    [(False, False), (True, False), (False, True)],
    ids=["profile", "account", "profile-images"],
)
@pytest.mark.parametrize("granular", [False, True])
@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_independent_portability_selection_review(
    live_server,
    request,
    settings,
    monkeypatch,
    tmp_path,
    language,
    granular,
    account_only,
    include_images,
):
    settings.DEBUG = True
    if account_only:
        case, author, _, _, _, receipt = prepared_account(
            request, settings, monkeypatch, "portability"
        )
        person = None
    else:
        case, author, _, _, receipt, person = ready(request, settings, monkeypatch, "portability")
    dataset = "subject_account" if account_only else "profile"
    selected_path = "/email" if account_only else "/alias"
    value = assessment()
    for item in value.values():
        item.update(
            status="eligible",
            basis="contract",
            origin="provided",
            automated=True,
            subject_related=True,
            third_party_reviewed=True,
            reason="Synthetic eligibility review before mobile approval",
            evidence=REASON,
        )
    if granular:
        value[dataset].update(
            status="granular",
            origin="mixed",
            basis="unknown",
            subject_related=None,
            third_party_reviewed=None,
        )
    plan = save_assessment(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Save synthetic assessment before mobile independent review",
        value,
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
    record(
        reviewer,
        case.pk,
        plan.pk,
        uuid4(),
        case.version,
        "inspect",
        "Inspect synthetic assessment before selected field preparation",
    )
    assessment_decision, _ = record(
        reviewer,
        case.pk,
        plan.pk,
        uuid4(),
        case.version,
        "review",
        "Approve synthetic assessment before selected field preparation",
        "approved",
    )
    with transaction.atomic():
        source = source_copy(person, person.listing if person else None, case)
    selected_marker = source[dataset][selected_path[1:]]
    original = (case.version, case.status, case.initial_due_at)
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.mfa_version += 1
    reviewer.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    author_secret = pyotp.random_base32()
    author.mfa_secret_encrypted = encrypt(author_secret)
    author.mfa_version += 1
    author.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            author_page = browser.new_page(viewport={"width": 390, "height": 844})
            author_page.goto(live_server.url + f"/{language}/account/login/")
            author_page.locator("[name=email]").fill(author.email)
            author_page.locator("[name=password]").fill(credentials["password"])
            author_page.locator("button[type=submit]").click()
            author_page.locator("[name=code]").fill(pyotp.TOTP(author_secret).now())
            author_page.locator("button[type=submit]").click()
            expect(
                author_page.get_by_role(
                    "heading", name="Your account" if english else "Tu cuenta", exact=True
                )
            ).to_be_visible()
            author_page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            author_page.locator("[name=purpose]").fill(
                "Inspect current request before guided field selection"
            )
            author_page.locator("button[type=submit]").first.click()
            author_page.locator(
                f'a[href="/{language}/moderation/rights/{case.pk}/portability/select/"]'
            ).click()
            assert selected_marker not in author_page.content()
            catalog_captions(author_page, language)
            inspect_button = "Inspect field page" if english else "Consultar página de campos"
            author_page.locator("[name=purpose]").fill("short")
            author_page.locator("form").first.evaluate("form=>form.noValidate=true")
            with author_page.expect_response(lambda r: r.request.method == "POST") as invalid:
                author_page.get_by_role("button", name=inspect_button, exact=True).click()
            assert invalid.value.status == 400
            catalog_captions(author_page, language)
            assert selected_marker not in author_page.content()
            author_page.locator("[name=review]").select_option(str(assessment_decision.pk))
            author_page.locator("[name=dataset]").select_option(dataset)
            author_page.locator("[name=purpose]").fill(
                "Audit synthetic account fields before portable selection"
            )
            author_page.get_by_role(
                "button",
                name="Inspect field page" if english else "Consultar página de campos",
                exact=True,
            ).click()
            expect(author_page.get_by_text(selected_marker, exact=True).first).to_be_visible()
            catalog_captions(author_page, language)
            expect(author_page.locator('label[for="id_reason"]')).to_have_text(
                ("Private selection reason" if english else "Motivo privado de selección") + ":"
            )
            if granular:
                for row in author_page.locator("fieldset").all():
                    expect(row.locator('label[for$="-evidence"]')).to_have_text(
                        ("Evidence" if english else "Evidencia") + ":"
                    )
                    expect(row.locator('option[value="unknown"]').first).to_have_text(
                        "Unknown" if english else "Desconocido"
                    )
            author_page.locator(f'[name=paths][value="{selected_path}"]').check()
            if granular:
                fieldset = author_page.locator("fieldset").filter(
                    has=author_page.locator(f'[name$="-path"][value="{selected_path}"]')
                )
                fieldset.locator('[name$="-basis"]').select_option("contract")
                fieldset.locator('[name$="-origin"]').select_option("provided")
                for name in ("automated", "subject_related", "third_party_reviewed"):
                    fieldset.locator(f'[name$="-{name}"]').select_option("yes")
                fieldset.locator('[name$="-reason"]').fill(
                    "Synthetic verified provenance for selected email field"
                )
                fieldset.locator('[name$="-evidence"]').fill(FIELD_EVIDENCE)
            author_page.locator("#id_reason").fill(
                "Choose synthetic account email for independent portable review"
            )
            author_page.get_by_role(
                "button",
                name="Save choices on this page"
                if english
                else "Guardar elecciones de esta página",
                exact=True,
            ).click()
            expect(author_page.get_by_role("status")).to_contain_text(
                "Selection draft saved" if english else "Borrador de selección guardado"
            )
            assert selected_marker not in author_page.content()
            author_page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/select/"
            )
            author_page.reload()
            assert selected_marker not in author_page.content()
            catalog_captions(author_page, language)
            expect(author_page.locator('label[for="reset_reason"]')).to_have_text(
                ("Private reset reason" if english else "Motivo privado del reinicio") + ":"
            )
            author_page.locator("#reset_review").select_option(str(assessment_decision.pk))
            author_page.locator("#reset_reason").fill(
                "Unconfirmed synthetic reset must have no effect"
            )
            author_page.locator("section form").evaluate("form=>form.noValidate=true")
            with author_page.expect_response(lambda r: r.request.method == "POST") as unconfirmed:
                author_page.get_by_role(
                    "button",
                    name="Confirm selection restart"
                    if english
                    else "Confirmar reinicio de selección",
                    exact=True,
                ).click()
            assert unconfirmed.value.status == 400
            catalog_captions(author_page, language)
            expect(author_page.locator('label[for="reset_reason"]')).to_have_text(
                ("Private reset reason" if english else "Motivo privado del reinicio") + ":"
            )
            assert author_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            if include_images:
                author_page.goto(
                    live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/images/"
                )
                assert author_page.locator('img[src^="data:image/webp"]').count() == 0
                image_catalog_captions(author_page, language)
                image_button_name = (
                    "Inspect image page" if english else "Consultar página de imagen"
                )
                author_page.locator("[name=purpose]").fill("short")
                author_page.locator("form").first.evaluate("form=>form.noValidate=true")
                with author_page.expect_response(
                    lambda r: r.request.method == "POST"
                ) as invalid_catalog:
                    author_page.get_by_role("button", name=image_button_name, exact=True).click()
                assert invalid_catalog.value.status == 400
                image_catalog_captions(author_page, language)
                assert author_page.locator('img[src^="data:image/webp"]').count() == 0
                author_page.locator("[name=review]").select_option(str(assessment_decision.pk))
                author_page.locator("[name=purpose]").fill(
                    "Inspect synthetic binary content before mobile selection"
                )
                author_page.get_by_role(
                    "button",
                    name="Inspect image page" if english else "Consultar página de imagen",
                    exact=True,
                ).click()
                expect(author_page.locator('img[src^="data:image/webp"]')).to_be_visible()
                image_catalog_captions(author_page, language)
                image_save_captions(author_page, language)
                author_page.locator("#id_reason").fill("short")
                author_page.locator("form").last.evaluate("form=>form.noValidate=true")
                with author_page.expect_response(
                    lambda r: r.request.method == "POST"
                ) as invalid_save:
                    author_page.get_by_role(
                        "button",
                        name="Save image selection" if english else "Guardar selección de imagen",
                        exact=True,
                    ).click()
                assert invalid_save.value.status == 400
                image_catalog_captions(author_page, language)
                image_save_captions(author_page, language, facts=False)
                assert author_page.locator('img[src^="data:image/webp"]').count() == 0
                author_page.locator("[name=review]").select_option(str(assessment_decision.pk))
                author_page.locator("[name=purpose]").fill(
                    "Inspect synthetic image again after invalid unsaved form"
                )
                author_page.get_by_role("button", name=image_button_name, exact=True).click()
                image_catalog_captions(author_page, language)
                image_save_captions(author_page, language)
                author_page.locator("[name=include]").check()
                author_page.locator("[name=image-basis]").select_option("contract")
                author_page.locator("[name=image-origin]").select_option("provided")
                for name in ("automated", "subject_related", "third_party_reviewed"):
                    author_page.locator(f'[name="image-{name}"]').select_option("yes")
                author_page.locator("[name=image-reason]").fill(
                    "Synthetic binary eligibility checked independently"
                )
                author_page.locator("[name=image-evidence]").fill(FIELD_EVIDENCE)
                author_page.locator("#id_reason").fill(
                    "Preserve scalar selections while including reviewed image"
                )
                author_page.get_by_role(
                    "button",
                    name="Save image selection" if english else "Guardar selección de imagen",
                    exact=True,
                ).click()
                expect(author_page.get_by_role("status")).to_contain_text(
                    "Image selection saved" if english else "Selección de imagen guardada"
                )
                author_page.goto(
                    live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/images/"
                )
                author_page.reload()
                image_catalog_captions(author_page, language)
                assert FIELD_EVIDENCE not in author_page.content()
                assert author_page.locator('img[src^="data:image/webp"]').count() == 0
                assert author_page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(reviewer.email)
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_role(
                    "heading", name="Your account" if english else "Tu cuenta", exact=True
                )
            ).to_be_visible()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            page.locator("[name=purpose]").fill(
                "Inspect latest request before independent purpose review"
            )
            page.locator("button[type=submit]").first.click()
            # The inspection UI orders selection drafts newest first.
            page.locator(
                f'a[href^="/{language}/moderation/rights/{case.pk}/portability/selection/"]'
            ).first.click()
            assert selected_marker not in page.content()
            review_url = page.url
            review_captions(page, language)
            button = "Record review action" if english else "Registrar acción de revisión"
            page.locator("#id_reason").fill("short")
            page.locator("form").last.evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                page.get_by_role("button", name=button, exact=True).click()
            assert invalid.value.status == 400
            review_captions(page, language)
            assert selected_marker not in page.content()
            assert (
                db_sync(
                    lambda: RightsPortabilitySelectionReview.objects.filter(
                        selection__request=case
                    ).count()
                )
                == 0
            )
            page.locator("[name=operation]").select_option("inspect")
            page.locator("#id_reason").fill(
                "Audit current plan before independent operational review"
            )
            button = "Record review action" if english else "Registrar acción de revisión"
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(selected_marker, exact=True).first).to_be_visible()
            review_captions(page, language)
            if granular:
                expect(page.get_by_text(FIELD_EVIDENCE, exact=True).first).to_be_visible()
            if include_images:
                image_button = page.get_by_role(
                    "button",
                    name="Inspect selected image" if english else "Consultar imagen seleccionada",
                    exact=True,
                )
                image_form = image_button.locator("..")
                reason_id = image_form.locator("textarea").get_attribute("id")
                expect(image_form.locator(f'label[for="{reason_id}"]')).to_have_text(
                    ("Private inspection purpose" if english else "Motivo privado de consulta")
                    + ":"
                )
                image_endpoint = image_form.get_attribute("action")
                image_form.locator("textarea").fill("short")
                image_form.evaluate("form=>form.noValidate=true")
                with page.expect_popup() as invalid_image:
                    image_button.click()
                popup = invalid_image.value
                popup.wait_for_load_state()
                expect(popup.locator("body")).to_have_text(
                    "Invalid inspection form" if english else "Formulario de consulta inválido"
                )
                popup.close()
                image_button.locator("..").locator("textarea").fill(
                    "Inspect exact synthetic bytes before independent approval"
                )
                with page.expect_popup() as opened:
                    image_button.click()
                popup = opened.value
                popup.wait_for_load_state()
                expect(popup.locator("img")).to_be_visible()
                response = popup.request.get(popup.url)
                assert response.status == 405
                popup.close()
            page.locator("[name=operation]").select_option("review")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("#id_reason").fill(
                "Independent synthetic review confirms the selected decisions"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Decision recorded: Approved" if english else "Decisión registrada: Aprobada"
            )
            page.goto(review_url)
            page.reload()
            review_captions(page, language)
            assert selected_marker not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            author_page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/export/"
            )
            assert selected_marker not in author_page.content()
            assert FIELD_EVIDENCE not in author_page.content()
            export_captions(author_page, language)
            assert author_page.locator("#id_coverage_review").input_value() == ""
            author_page.locator("#id_reason").fill("short")
            author_page.locator("form").evaluate("form=>form.noValidate=true")
            with author_page.expect_response(
                lambda r: r.request.method == "POST"
            ) as invalid_export:
                author_page.get_by_role(
                    "button",
                    name="Create approved private copy"
                    if english
                    else "Crear copia privada aprobada",
                    exact=True,
                ).click()
            assert invalid_export.value.status == 400
            export_captions(author_page, language)
            assert db_sync(lambda: RightsExport.objects.filter(action__request=case).count()) == 0
            choice = author_page.locator("[name=review] option").last.get_attribute("value")
            author_page.locator("[name=review]").select_option(choice)
            author_page.locator("#id_reason").fill(
                "Generate independently approved synthetic mobile copy"
            )
            author_page.get_by_role(
                "button",
                name="Create approved private copy" if english else "Crear copia privada aprobada",
                exact=True,
            ).click()
            expect(author_page.get_by_role("status")).to_contain_text(
                "Private copy created" if english else "Copia privada creada"
            )
            expect(author_page.get_by_role(
                "heading", name="Private copy generation" if english else "Generación de copia privada",
                exact=True,
            )).to_be_visible()
            expect(author_page.get_by_role(
                "link", name="Prepare final response" if english else "Preparar respuesta final",
                exact=True,
            )).to_have_attribute("href", f"/{language}/moderation/rights/{case.pk}/portability/response/")
            expect(author_page.get_by_role(
                "link", name="Return to generation" if english else "Volver a generación", exact=True,
            )).to_have_attribute("href", f"/{language}/moderation/rights/{case.pk}/portability/export/")
            assert db_sync(lambda: RightsExport.objects.filter(action__request=case).count()) == 1
            assert selected_marker not in author_page.content()
            author_page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/export/"
            )
            author_page.reload()
            export_captions(author_page, language)
            assert selected_marker not in author_page.content()
            assert author_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            public_page = browser.new_page(viewport={"width": 390, "height": 844})
            public_page.goto(live_server.url + receipt.replace("/en/", f"/{language}/", 1))
            assert selected_marker not in public_page.content()
            with public_page.expect_download() as downloaded:
                public_page.get_by_role(
                    "button",
                    name="Download private copy" if english else "Descargar copia privada",
                    exact=True,
                ).click()
            downloaded.value.save_as(str(tmp_path / "portable-mobile.json"))
            delivered = json.loads((tmp_path / "portable-mobile.json").read_text())
            assert delivered["datasets"][dataset] == [{"fields": {selected_path: selected_marker}}]
            assert FIELD_EVIDENCE not in str(delivered)
            page.goto(review_url)
            review_csrf = page.locator("[name=csrfmiddlewaretoken]").input_value()
            db_sync(
                lambda: reviewer.user_permissions.remove(
                    Permission.objects.get(codename="review_portability")
                )
            )
            response = page.goto(review_url)
            assert response.status == 403 and page.locator("body").inner_text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = page.request.post(review_url, form={"csrfmiddlewaretoken": review_csrf})
            assert response.status == 403 and response.text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            if include_images:
                response = page.request.post(
                    live_server.url + image_endpoint,
                    form={
                        "csrfmiddlewaretoken": review_csrf,
                        "key": str(uuid4()),
                        "version": case.version,
                        "reason": "Inspect synthetic image after revoked permission",
                    },
                )
                assert response.status == 403 and response.text() == (
                    "Forbidden" if english else "Acceso denegado"
                )
            author_page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/select/"
            )
            csrf = author_page.locator("[name=csrfmiddlewaretoken]").first.input_value()
            db_sync(
                lambda: author.user_permissions.remove(
                    Permission.objects.get(codename="execute_rights_request")
                )
            )
            response = author_page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/select/"
            )
            assert response.status == 403 and author_page.locator("body").inner_text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = author_page.request.post(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/select/",
                form={"csrfmiddlewaretoken": csrf},
            )
            assert response.status == 403 and response.text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            response = author_page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/export/"
            )
            assert response.status == 403 and author_page.locator("body").inner_text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = author_page.request.post(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/export/",
                form={"csrfmiddlewaretoken": csrf},
            )
            assert response.status == 403 and response.text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            if include_images:
                response = author_page.goto(
                    live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/images/"
                )
                assert response.status == 403 and author_page.locator("body").inner_text() == (
                    "Forbidden" if english else "Acceso denegado"
                )
                assert "no-store" in response.headers["cache-control"]
                response = author_page.request.post(
                    live_server.url
                    + f"/{language}/moderation/rights/{case.pk}/portability/images/",
                    form={"csrfmiddlewaretoken": csrf},
                )
                assert response.status == 403 and response.text() == (
                    "Forbidden" if english else "Acceso denegado"
                )
                assert len(delivered["images"]) == 1 and len(delivered["parts"]) == 1

        finally:
            browser.close()
    result = RightsPortabilitySelectionReview.objects.get(selection__request=case)
    assert result.action.actor_id == reviewer.pk and result.outcome == "approved"
    export = RightsExport.objects.get(action__request=case)
    projected = unseal(export.encrypted_payload)
    assert projected["partial"] is True and export.portability_binding.coverage_review_id is None
    assert projected["datasets"][dataset] == [{"fields": {selected_path: selected_marker}}]
    assert "field_evidence" not in projected and FIELD_EVIDENCE not in str(projected)
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == (original[0] + 1, *original[1:])
    assert RightsExportDownload.objects.filter(export=export, actor__isnull=True).count() == 1
