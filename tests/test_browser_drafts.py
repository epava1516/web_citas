import os
import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401

from apps.catalog.models import Municipality, PostalCode
from apps.listings.models import Revision


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("language,width", [("es", 390), ("en", 390), ("es", 1280), ("en", 1280)])
def test_browser_profile_steps_reload_and_no_professional_fields(
    live_server, request, settings, language, width
):
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
    postal_id = str(PostalCode.objects.get(code="29001").pk)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": width, "height": 844})
        try:
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(user.email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/{language}/person/{person.pk}/verification/")
            page.get_by_role("button", name="Create or resume listing" if language == "en" else "Crear o retomar anuncio").click()
            page.get_by_role(
                "button", name="Save and continue" if language == "en" else "Guardar y continuar"
            ).focus()
            page.keyboard.press("Enter")
            expect(page.locator("[name=title]")).to_be_focused()
            assert page.locator("[name=title]").evaluate("field => field.validationMessage")
            page.locator("[name=title]").fill("Busco compartir fotografía y paseos")
            page.keyboard.press("Tab")
            expect(page.locator("textarea[name=description]")).to_be_focused()
            page.locator("textarea[name=description]").fill(
                "Busco citas románticas y compartir mis aficiones por la fotografía y la cultura."
            )
            expect(page.locator("[name=categories], [name=services], [name=travel]")).to_have_count(0)
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
            page.get_by_role("button", name="Save and continue" if language == "en" else "Guardar y continuar").click()
            page.locator("[name=contact_exposure_accepted]").check()
            page.locator("[name=accept_publishing]").check()
            expect(page.locator("[name^=rates-]")).to_have_count(0)
            page.get_by_role("button", name="Save and continue" if language == "en" else "Guardar y continuar").click()
            page.get_by_role("link", name="Review draft" if language == "en" else "Revisar borrador").click()
            page.reload()
            expect(
                page.get_by_role("heading", name="Busco compartir fotografía y paseos")
            ).to_be_visible()
            expect(page.get_by_text("Busco citas románticas y compartir mis aficiones por la fotografía y la cultura.")).to_be_visible()
        finally:
            browser.close()
    revision = Revision.objects.get()
    assert revision.municipality_id == int(city_id)
    assert not revision.rates.exists()
    assert revision.categories.get().slug == "romantic-dating"
