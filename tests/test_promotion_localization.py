"""Localized prepared test-mode orders, never actual purchase/capacity acceptance."""

import re
import shutil

import pytest
from django.db import connection
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup
from test_reset_localization import db_sync

from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_synthetic_order_preserves_price_and_gates(
    request, settings, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    user, listing, version, credentials = setup(request, settings)
    client = Client()
    client.force_login(user)
    session = client.session
    session.update(credentials)
    session.save()
    cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
    english = language == "en"
    link = "Test promotion orders" if english else "Pedidos de promociones de prueba"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [{"name": settings.SESSION_COOKIE_NAME, "value": cookie, "url": live_server.url}]
            )
            page = context.new_page()
            page.goto(live_server.url + f"/{language}/account/")
            page.get_by_role("link", name=link, exact=True).click()
            expect(page.get_by_role("heading", name=link, exact=True)).to_be_visible()
            for label in [
                ("Listing" if english else "Anuncio"),
                ("Test product" if english else "Producto de prueba"),
                (
                    "I understand this is a simulation with no charge"
                    if english
                    else "Entiendo que es una simulación sin cobro"
                ),
            ]:
                expect(
                    page.get_by_label(re.compile("^" + re.escape(label) + ":?$"))
                ).to_be_visible()
            expect(
                page.locator(
                    "[name=product] option",
                    has_text=("Test" if english else "Prueba") + " · 12.00 EUR",
                )
            ).to_have_count(1)
            page.locator("[name=listing]").select_option(str(listing.pk))
            page.locator("[name=product]").select_option(str(version.pk))
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            assert page.request.post(page.url, form=data).status == 400
            assert db_sync(lambda: PromotionOrder.objects.count()) == 0
            page.locator("[name=confirm]").check()
            page.get_by_role(
                "button",
                name="Create test order" if english else "Crear pedido de prueba",
                exact=True,
            ).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Synthetic promotion order"
                    if english
                    else "Pedido sintético de promoción",
                    exact=True,
                )
            ).to_be_visible()
            for label in [
                ("Outcome" if english else "Resultado"),
                (
                    "Simulation only, no real payment"
                    if english
                    else "Solo simulación, sin pago real"
                ),
            ]:
                expect(
                    page.get_by_label(re.compile("^" + re.escape(label) + ":?$"))
                ).to_be_visible()
            expected = [
                ["pending", "Pending" if english else "Pendiente"],
                ["failed", "Failure" if english else "Fallo"],
                ["succeeded", "Simulated success" if english else "Éxito simulado"],
            ]
            assert (
                page.locator("[name=outcome] option").evaluate_all(
                    "es=>es.map(e=>[e.value,e.textContent])"
                )
                == expected
            )
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            assert (
                page.request.post(
                    page.url, form=data | {"outcome": "unknown", "confirm": "on"}
                ).status
                == 400
            )
            assert db_sync(lambda: PromotionEntitlement.objects.count()) == 0
            page.locator("[name=outcome]").select_option("succeeded")
            page.locator("[name=confirm]").check()
            page.get_by_role(
                "button", name="Simulate outcome" if english else "Simular resultado", exact=True
            ).click()
            page.reload()
            expect(
                page.get_by_text(
                    "Confirmed simulated payment" if english else "Pago simulado confirmado",
                    exact=True,
                )
            ).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert PromotionOrder.objects.filter(buyer=user, status="paid").count() == 1
    assert PromotionEntitlement.objects.count() == 1
