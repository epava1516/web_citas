import os
import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401

from apps.catalog.models import Category, Municipality, PostalCode, Service
from apps.listings.models import Revision


@pytest.mark.django_db(transaction=True)
def test_browser_draft_steps_reload_and_consult(live_server, request, settings):
    settings.DEBUG = True
    user, person, _ = request.getfixturevalue("scenario")
    city = Municipality.objects.get(code="demo-south")
    north = Municipality.objects.get(code="demo-north")
    region_id, province_id, city_id = (
        str(city.province.region_id),
        str(city.province_id),
        str(city.pk),
    )
    north_region, north_province = str(north.province.region_id), str(north.province_id)
    category_id = str(Category.objects.get(slug="modeling").pk)
    service_id = str(Service.objects.get(slug="photography").pk)
    postal_id = str(PostalCode.objects.get(code="29001").pk)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.goto(live_server.url + "/es/account/login/")
            page.locator("[name=email]").fill(user.email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/es/person/{person.pk}/verification/")
            page.get_by_role("button", name="Crear o retomar anuncio").click()
            page.locator("[name=title]").fill("Fotografía para eventos culturales")
            page.locator("textarea[name=description]").fill(
                "Trabajo de modelaje profesional en eventos y fotografía."
            )
            page.locator('[name=categories][value="' + category_id + '"]').check()
            page.locator('[name=services][value="' + service_id + '"]').check()
            page.locator("[name=region]").select_option(region_id)
            page.locator("[name=province]").select_option(province_id)
            page.locator("[name=municipality]").select_option(city_id)
            page.locator("[name=postal_code]").select_option(postal_id)
            page.locator("[name=region]").select_option(north_region)
            expect(page.locator("[name=municipality]")).to_have_value("")
            expect(page.locator("[name=postal_code]")).to_have_value("")
            page.locator("[name=province]").select_option(north_province)
            page.locator("[name=region]").select_option(region_id)
            page.locator("[name=province]").select_option(province_id)
            page.locator("[name=municipality]").select_option(city_id)
            page.locator("[name=postal_code]").select_option(postal_id)
            page.get_by_role("button", name="Guardar y continuar").click()
            page.locator("[name=contact_exposure_accepted]").check()
            page.locator("[name=accept_publishing]").check()
            page.locator("[name=rates-0-concept]").fill("Fotografía profesional")
            page.locator("[name=rates-0-mode]").select_option("consult")
            page.get_by_role("button", name="Guardar y continuar").click()
            page.get_by_role("link", name="Revisar borrador").click()
            page.reload()
            expect(
                page.get_by_role("heading", name="Fotografía para eventos culturales")
            ).to_be_visible()
            expect(page.get_by_text("Fotografía profesional · Consultar")).to_be_visible()
        finally:
            browser.close()
    revision = Revision.objects.get()
    assert revision.municipality_id == int(city_id)
    assert revision.rates.get().amount is None
