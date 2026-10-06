import uuid
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_order_models import (
    PromotionEntitlement,
    PromotionOrder,
    PromotionPaymentEvent,
)
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.core.models import Person, User

pytestmark = pytest.mark.django_db(transaction=True)


def setup(request, settings):
    request.getfixturevalue("directory")
    settings.PROMOTION_TEST_MODE = True
    person = Person.objects.get(individual__username="fixture-v1-individual")
    user = person.individual
    user.mfa_enabled = True
    user.save(update_fields=["mfa_enabled"])
    version = PromotionProductVersion.objects.create(
        product=PromotionProduct.objects.create(slug="synthetic_order", kind="top"),
        version=1,
        name_es="Prueba",
        name_en="Test",
        duration_days=10,
        amount=Decimal("12.00"),
        currency="EUR",
        tax_rate=Decimal("20"),
        published_at=timezone.now(),
        is_current=True,
    )
    credentials = {"mfa_version": user.mfa_version, "account_version": user.session_version}
    return user, person.listing, version, credentials


def test_order_snapshot_replay_pending_failed_success_and_event_conflicts(request, settings):
    user, listing, version, credentials = setup(request, settings)
    key = uuid.uuid4()
    order = create_order(user, listing.pk, version.pk, key, **credentials)
    assert create_order(user, listing.pk, version.pk, key, **credentials).pk == order.pk
    assert order.net_amount == Decimal("10.00") and order.tax_amount == Decimal("2.00")
    for outcome in ["pending", "failed", "succeeded"]:
        payload, signature = synthetic_event(order.payment_attempt, outcome, uuid.uuid4())
        receive_event(user, payload, signature, **credentials)
        assert PromotionEntitlement.objects.filter(order=order).count() == int(
            outcome == "succeeded"
        )
    entitlement = order.entitlement
    receive_event(user, payload, signature, **credentials)
    assert order.entitlement.pk == entitlement.pk and PromotionPaymentEvent.objects.count() == 3
    changed = payload | {"outcome": "pending"}
    from apps.catalog.promotion_orders import synthetic_signature

    with pytest.raises(ValidationError):
        receive_event(user, changed, synthetic_signature(changed), **credentials)
    version.amount = Decimal("24.00")
    version.save(update_fields=["amount"])
    order.refresh_from_db()
    assert order.amount == Decimal("12.00") and order.synthetic
    with pytest.raises(ValidationError):
        create_order(user, listing.pk, version.pk + 1, key, **credentials)


def test_invalid_events_foreign_actor_and_revoked_session_never_grant(request, settings):
    user, listing, version, credentials = setup(request, settings)
    order = create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid.uuid4())
    with pytest.raises(PermissionDenied):
        receive_event(user, payload, "invalid", **credentials)
    from apps.catalog.promotion_orders import synthetic_signature

    wrong = payload | {"amount": "999.00"}
    with pytest.raises(ValidationError):
        receive_event(user, wrong, synthetic_signature(wrong), **credentials)
    foreign = User.objects.get(username="fixture-v1-visitor")
    foreign.mfa_enabled = True
    foreign.save(update_fields=["mfa_enabled"])
    with pytest.raises(PermissionDenied):
        receive_event(
            foreign,
            payload,
            signature,
            mfa_version=foreign.mfa_version,
            account_version=foreign.session_version,
        )
    User.objects.filter(pk=user.pk).update(session_version=user.session_version + 1)
    with pytest.raises(PermissionDenied):
        receive_event(user, payload, signature, **credentials)
    assert not PromotionEntitlement.objects.exists() and not PromotionPaymentEvent.objects.exists()


def test_disabled_production_incomplete_product_and_withdrawn_listing_reject(request, settings):
    user, listing, version, credentials = setup(request, settings)
    settings.PROMOTION_TEST_MODE = False
    with pytest.raises(PermissionDenied):
        create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    settings.PROMOTION_TEST_MODE = True
    settings.PRODUCTION = True
    with pytest.raises(PermissionDenied):
        create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    settings.PRODUCTION = False
    version.amount = None
    version.save(update_fields=["amount"])
    with pytest.raises(ValidationError):
        create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    listing.status = "withdrawn"
    listing.save(update_fields=["status"])
    with pytest.raises(PermissionDenied):
        create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    assert not PromotionOrder.objects.exists()
