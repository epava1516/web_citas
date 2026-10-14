import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_promotion_catalog import manager
from test_reports import directory, photo_environment  # noqa: F401

from apps.catalog.promotion_models import PromotionProductVersion

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_mobile_catalogue_navigation_save_release_reload(
    request, live_server, settings, language
):
    settings.DEBUG = True
    actor, staff = manager(request)
    cookie = staff.cookies[settings.SESSION_COOKIE_NAME].value
    english = language == "en"
    catalogue = "Promotion catalogue" if english else "Catálogo de promociones"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": cookie,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(live_server.url + f"/{language}/account/")
            page.get_by_role("link", name=catalogue, exact=True).click()
            expect(page.get_by_role("heading", name=catalogue, exact=True)).to_be_visible()
            expect(page.locator("label[for=id_slug]")).to_have_text(
                ("Identifier" if english else "Identificador") + ":"
            )
            expect(page.locator("label[for=id_kind]")).to_have_text(
                ("Type" if english else "Tipo") + ":"
            )
            assert page.locator("[name=kind] option[value=autobump]").inner_text() == (
                "Auto bump" if english else "Autosubida"
            )
            assert page.locator("[name=kind] option").evaluate_all(
                "xs => xs.map(x => x.value)"
            ) == ["", "premium", "top", "autobump"]
            page.locator("[name=slug]").fill("synthetic_mobile_top")
            page.locator("[name=kind]").select_option("top")
            page.get_by_role(
                "button", name="Create product" if english else "Crear producto"
            ).click()
            labels = {
                "name_es": ("Nombre español", "Spanish name"),
                "name_en": ("Nombre inglés", "English name"),
                "duration_days": ("Duración en días", "Duration in days"),
                "amount": ("Importe sin impuestos", "Amount before tax"),
                "currency": ("Moneda", "Currency"),
                "tax_rate": ("Impuesto porcentual", "Tax percent"),
                "bump_interval_minutes": (
                    "Intervalo de subida en minutos",
                    "Bump interval in minutes",
                ),
                "daily_bump_limit": ("Cupo diario", "Daily bump limit"),
            }
            for name, pair in labels.items():
                expect(page.locator(f"label[for=id_{name}]")).to_have_text(pair[english] + ":")
            page.locator("[name=name_es]").fill("Promoción móvil sintética")
            page.locator("[name=name_en]").fill("Synthetic mobile promotion")
            page.get_by_role("button", name="Save draft" if english else "Guardar borrador").click()
            expect(
                page.get_by_role(
                    "heading",
                    name=("Synthetic mobile promotion" if english else "Promoción móvil sintética"),
                    exact=True,
                )
            ).to_be_visible()
            expect(
                page.get_by_text(
                    "Configuration pending. Sales inactive."
                    if english
                    else "Pendiente de configurar. Ventas inactivas.",
                    exact=True,
                )
            ).to_be_visible()
            page.get_by_role(
                "button", name=("Release configuration" if english else "Publicar configuración")
            ).click()
            expect(
                page.get_by_role(
                    "button",
                    name=("Release configuration" if english else "Publicar configuración"),
                )
            ).to_have_count(0)
            page.reload()
            expect(
                page.get_by_role(
                    "button",
                    name=("Release configuration" if english else "Publicar configuración"),
                )
            ).to_have_count(0)
            assert "0.00" not in page.content()
        finally:
            browser.close()
    row = PromotionProductVersion.objects.get(product__slug="synthetic_mobile_top")
    assert row.published_at and row.is_current and not row.sellable
    assert row.amount is None and row.name_en == "Synthetic mobile promotion"
