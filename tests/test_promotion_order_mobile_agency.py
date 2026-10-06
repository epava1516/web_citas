import shutil
import uuid

import pytest
from django.core.exceptions import PermissionDenied
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup

from apps.catalog.promotion_exposure import ranked
from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.core.models import Agency, AgencyMember, Person, User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_dashboard_order_simulation_reload_and_layout(
    request, settings, live_server, language
):
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
            page.locator("[name=listing]").select_option(str(listing.pk))
            page.locator("[name=product]").select_option(str(version.pk))
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


@pytest.mark.parametrize("role", ["owner", "editor"])
def test_agency_buyer_authority_and_revocation_remove_sponsorship(request, settings, role):
    _, _, version, _ = setup(request, settings)
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    user = person.agency.owner if role == "owner" else person.assigned_editor
    user.mfa_enabled = True
    user.save(update_fields=["mfa_enabled"])
    credentials = {"mfa_version": user.mfa_version, "account_version": user.session_version}
    order = create_order(user, person.listing.pk, version.pk, uuid.uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid.uuid4())
    receive_event(user, payload, signature, **credentials)
    assert ranked([person.listing])[1] == {person.listing.pk: "top"}
    if role == "editor":
        AgencyMember.objects.filter(agency=person.agency, user=user).update(active=False)
    else:
        foreign = User.objects.get(username="fixture-v1-visitor")
        Agency.objects.filter(pk=person.agency_id).update(owner=foreign)
    with pytest.raises(PermissionDenied):
        receive_event(user, payload, signature, **credentials)
    assert not ranked([person.listing])[1]
    order.refresh_from_db()
    assert order.buyer_id == user.pk and order.manager_version == person.manager_version
    assert PromotionEntitlement.objects.filter(order=order).count() == 1
