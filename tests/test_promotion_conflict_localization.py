"""Native conflicts rendered in browser; controlled catalogue interleaving is not a race proof."""

import shutil
import uuid

import pytest
from django.db import connection
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_promotion_catalog import manager
from test_promotion_orders import setup
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.catalog import promotion_views
from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_order_models import (
    PromotionEntitlement,
    PromotionOrder,
    PromotionPaymentEvent,
)
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_three_native_conflicts_localized(request, settings, live_server, monkeypatch, language):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    user, listing, version, credentials = setup(request, settings)
    key = uuid.uuid4()
    order = create_order(user, listing.pk, version.pk, key, **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid.uuid4())
    receive_event(user, payload, signature, **credentials)
    version.pk = None
    version.product = PromotionProduct.objects.create(slug="synthetic_second", kind="top")
    version.save()
    client = Client()
    client.force_login(user)
    session = client.session
    session.update(credentials)
    session.save()
    _, staff = manager(request)
    original = promotion_views.create_product

    def insert_between_validation_and_create(*args, **kwargs):
        original(*args, **kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(promotion_views, "create_product", insert_between_validation_and_create)
    english = language == "en"
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
                        "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(live_server.url + f"/{language}/account/test-promotions/")
            page.locator("[name=listing]").select_option(str(listing.pk))
            page.locator("[name=product]").select_option(str(version.pk))
            page.locator("[name=key]").evaluate("(e, key) => e.value=key", str(key))
            page.locator("[name=confirm]").check()
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Create test order" if english else "Crear pedido de prueba",
                    exact=True,
                ).click()
            assert response.value.status == 409
            expect(
                page.get_by_text(
                    "Configuration or publication changed"
                    if english
                    else "Configuración o publicación cambiada",
                    exact=True,
                )
            ).to_be_visible()
            page.goto(live_server.url + f"/{language}/account/test-promotions/{order.pk}/")
            page.locator("[name=outcome]").select_option("failed")
            page.locator("[name=confirm]").check()
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Simulate outcome" if english else "Simular resultado",
                    exact=True,
                ).click()
            assert response.value.status == 409
            expect(
                page.get_by_text(
                    "Simulation rejected: publication, session or state changed"
                    if english
                    else "Simulación rechazada: publicación, sesión o estado cambiados",
                    exact=True,
                )
            ).to_be_visible()
            assert db_sync(
                lambda: (
                    PromotionOrder.objects.count(),
                    PromotionPaymentEvent.objects.count(),
                    PromotionEntitlement.objects.count(),
                )
            ) == (1, 1, 1)
            context.clear_cookies()
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": staff.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page.goto(live_server.url + f"/{language}/operations/promotion-products/")
            page.locator("[name=slug]").fill("synthetic_conflicting_create")
            page.locator("[name=kind]").select_option("top")
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button", name="Create product" if english else "Crear producto", exact=True
                ).click()
            assert response.value.status == 409
            expect(
                page.get_by_text(
                    "Product changed or invalid" if english else "Producto cambiado o inválido",
                    exact=True,
                )
            ).to_be_visible()
            assert (
                db_sync(
                    lambda: PromotionProductVersion.objects.filter(
                        product__slug="synthetic_conflicting_create"
                    ).count()
                )
                == 1
            )
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
