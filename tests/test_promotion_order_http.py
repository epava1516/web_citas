import uuid

import pytest
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup

from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder
from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_private_order_form_simulation_reload_and_ownership(request, settings, language):
    user, listing, product, credentials = setup(request, settings)
    client = Client()
    client.force_login(user)
    session = client.session
    session.update(credentials)
    session.save()
    path = f"/{language}/account/test-promotions/"
    before = PromotionOrder.objects.count()
    response = client.get(path)
    assert response.status_code == 200 and response["Cache-Control"] == "no-store"
    assert "noindex" in response["X-Robots-Tag"]
    assert PromotionOrder.objects.count() == before
    payload = {
        "key": str(uuid.uuid4()),
        "listing": str(listing.pk),
        "product": product.pk,
        "confirm": "on",
    }
    response = client.post(path, payload)
    assert response.status_code == 302
    order = PromotionOrder.objects.get(buyer=user)
    target = response["Location"]
    assert client.post(path, payload)["Location"] == target
    assert client.get(target).status_code == 200
    event = {"key": str(uuid.uuid4()), "outcome": "succeeded", "confirm": "on"}
    assert client.post(target, event).status_code == 302
    assert client.post(target, event).status_code == 302
    assert PromotionEntitlement.objects.filter(order=order).count() == 1
    assert client.get(target).status_code == 200
    foreign = User.objects.get(username="fixture-v1-visitor")
    foreign.mfa_enabled = True
    foreign.save(update_fields=["mfa_enabled"])
    outsider = Client()
    outsider.force_login(foreign)
    session = outsider.session
    session.update({"mfa_version": foreign.mfa_version, "account_version": foreign.session_version})
    session.save()
    assert (
        outsider.get(target).status_code == 404 and outsider.post(target, event).status_code == 404
    )
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(user)
    session = csrf.session
    session.update(credentials)
    session.save()
    assert csrf.post(target, event).status_code == 403
    settings.PROMOTION_TEST_MODE = False
    assert client.get(path).status_code == 403
