"""Audited image popup's static denial copy preserves exact WebP and private scope."""

import hashlib
import shutil

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import translation
from playwright.sync_api import sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_exports import prepared

from apps.core.models import Person
from apps.safety.models import RightsExport, RightsImageAccess, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)
PURPOSE = "Synthetic / literal own image inspection purpose"


@pytest.mark.parametrize("language", ["es", "en"])
def test_native_image_popup_and_private_denials(request, settings, live_server, language):
    settings.DEBUG = True
    case, actor, staff, _, _, person = prepared(request, settings)
    before = (case.status, case.version, case.initial_due_at)
    photo = person.listing.revisions.first().photos.first()
    with photo.blob.derivative.open("rb") as stream:
        content = stream.read()
    foreign = (
        Person.objects.get(individual__username="fixture-v1-individual")
        .listing.revisions.first()
        .photos.first()
    )
    with translation.override(language):
        prepare_path = reverse("rights_export_prepare", args=[case.pk])
        image_path = reverse("rights_image_inspect", args=[case.pk, photo.pk])
        foreign_path = reverse("rights_image_inspect", args=[case.pk, foreign.pk])
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": staff.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            assert page.goto(live_server.url + prepare_path).status == 200
            page.locator("#id_operation").select_option("preview")
            page.locator("#id_purpose").fill(PURPOSE)
            with page.expect_response(lambda r: r.request.method == "POST") as preview:
                page.get_by_role(
                    "button",
                    name="Record copy action" if language == "en" else "Registrar acción de copia",
                    exact=True,
                ).click()
            assert preview.value.status == 200
            image_form = page.locator(f'form[action="{image_path}"]')
            assert image_form.count() == 1
            csrf = image_form.locator('[name="csrfmiddlewaretoken"]').input_value()
            assert context.request.get(live_server.url + image_path).status == 405
            image_form.evaluate("f=>f.noValidate=true")
            image_form.locator('[name="purpose"]').fill("bad")
            with page.expect_popup() as popup:
                image_form.get_by_role("button").click()
            invalid = popup.value
            invalid.wait_for_load_state()
            assert invalid.locator("body").inner_text() == (
                "Purpose required" if language == "en" else "Motivo obligatorio"
            )
            invalid.close()
            assert db_sync(lambda: RightsImageAccess.objects.filter(request=case).count()) == 0
            result = context.request.post(
                live_server.url + foreign_path,
                form={"csrfmiddlewaretoken": csrf, "purpose": PURPOSE},
            )
            assert result.status == 404
            result = context.request.post(
                live_server.url + image_path, form={"csrfmiddlewaretoken": csrf, "purpose": PURPOSE}
            )
            assert (
                result.status == 200
                and result.body() == content
                and result.headers["content-type"] == "image/webp"
            )
            assert "no-store" in result.headers["cache-control"]
            assert db_sync(lambda: RightsImageAccess.objects.filter(request=case).count()) == 1
            page.goto(live_server.url + prepare_path)
            page.reload()
            assert page.locator(f'form[action="{image_path}"]').count() == 0
            csrf = page.locator('[name="csrfmiddlewaretoken"]').first.input_value()
            db_sync(
                lambda: RightsRequest.objects.filter(pk=case.pk).update(scope_status="unverified")
            )
            result = context.request.post(
                live_server.url + image_path, form={"csrfmiddlewaretoken": csrf, "purpose": PURPOSE}
            )
            assert result.status == 409 and result.text() == (
                "Review current scope and image first"
                if language == "en"
                else "Revisa el ámbito y la imagen actual"
            )
            db_sync(
                lambda: actor.user_permissions.remove(
                    Permission.objects.get(codename="review_rights_request")
                )
            )
            result = context.request.post(
                live_server.url + image_path, form={"csrfmiddlewaretoken": csrf, "purpose": PURPOSE}
            )
            assert result.status == 403 and result.text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
            assert "no-store" in result.headers["cache-control"]
        finally:
            browser.close()
    row = RightsImageAccess.objects.get(request=case)
    assert (
        row.photo_id == photo.pk
        and row.content_digest == hashlib.sha256(content).hexdigest()
        and row.purpose == PURPOSE
    )
    assert RightsExport.objects.filter(action__request=case).count() == 0
    case.refresh_from_db()
    assert (case.status, case.version, case.initial_due_at) == before
