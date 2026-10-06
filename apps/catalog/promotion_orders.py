"""Synthetic-only commercial services; no browser-confirmed or provider payment."""

import hashlib
import json
import uuid
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from apps.core.agencies import can_manage_person
from apps.core.models import User
from apps.core.verification import locked_manager_person
from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible

from .promotion_models import PromotionProduct, PromotionProductVersion
from .promotion_order_models import (
    PromotionEntitlement,
    PromotionOrder,
    PromotionOrderAudit,
    PromotionPaymentAttempt,
    PromotionPaymentEvent,
)


def test_mode():
    if settings.PRODUCTION or not getattr(settings, "PROMOTION_TEST_MODE", False):
        raise PermissionDenied("Synthetic commercial mode disabled")


def actor(user, mfa_version, account_version):
    current = User.objects.get(pk=user.pk)
    if (
        not current.is_active
        or current.account_erased_at
        or not current.mfa_enabled
        or current.mfa_version != mfa_version
        or current.session_version != account_version
        or current.mfa_version != user.mfa_version
        or current.session_version != user.session_version
    ):
        raise PermissionDenied
    return current


def digest(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def audit(user, order, operation):
    PromotionOrderAudit.objects.create(
        actor=user,
        order=order,
        operation=operation,
        payload_digest=digest(
            {"order": order.pk, "status": order.status, "manager": order.manager_version}
        ),
    )


def authorize(user, person, listing, mfa_version, account_version):
    current = actor(user, mfa_version, account_version)
    if not can_manage_person(current, person) or not publicly_visible(listing):
        raise PermissionDenied("Publication or management no longer eligible")
    return current


@transaction.atomic
def create_order(user, listing_id, product_version_id, key, *, mfa_version, account_version):
    test_mode()
    current = actor(user, mfa_version, account_version)
    initial = Listing.objects.get(pk=listing_id)
    person = locked_manager_person(current, initial.person_id)
    listing = (
        Listing.objects.select_for_update()
        .select_related("approved_revision", "person")
        .get(pk=listing_id)
    )
    current = authorize(user, person, listing, mfa_version, account_version)
    key = uuid.UUID(str(key))
    signature = digest(
        {"listing": listing.pk, "version": product_version_id, "manager": person.manager_version}
    )
    previous = PromotionOrder.objects.filter(buyer=current, idempotency_key=key).first()
    if previous:
        if previous.request_digest != signature:
            raise ValidationError("Order key conflict")
        authorize(user, person, listing, mfa_version, account_version)
        return previous
    initial_version = PromotionProductVersion.objects.get(pk=product_version_id)
    product = PromotionProduct.objects.select_for_update().get(pk=initial_version.product_id)
    version = PromotionProductVersion.objects.select_for_update().get(pk=product_version_id)
    if (
        not product.active
        or not version.is_current
        or not version.published_at
        or not version.configuration_ready
    ):
        raise ValidationError("Product configuration unavailable")
    net = (version.amount / (Decimal("1") + version.tax_rate / Decimal("100"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    try:
        with transaction.atomic():
            order = PromotionOrder.objects.create(
                buyer=current,
                listing=listing,
                product_version=version,
                manager_version=person.manager_version,
                idempotency_key=key,
                request_digest=signature,
                amount=version.amount,
                currency=version.currency,
                tax_rate=version.tax_rate,
                net_amount=net,
                tax_amount=version.amount - net,
                kind=product.kind,
                duration_days=version.duration_days,
                bump_interval_minutes=version.bump_interval_minutes,
                daily_bump_limit=version.daily_bump_limit,
            )
            PromotionPaymentAttempt.objects.create(order=order)
            audit(current, order, "create_order")
    except IntegrityError:
        raise ValidationError("Concurrent order key conflict") from None
    authorize(user, person, listing, mfa_version, account_version)
    return order


def synthetic_signature(payload):
    return salted_hmac(
        "promotion-synthetic-event-v1",
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        algorithm="sha256",
    ).hexdigest()


def synthetic_event(attempt, outcome, event_key):
    """Internal test adapter; no public signing endpoint or real payment claim."""
    test_mode()
    if outcome not in {"pending", "failed", "succeeded"}:
        raise ValidationError("Unsupported synthetic outcome")
    payload = {
        "schema": "synthetic-promotion-payment-v1",
        "attempt": str(attempt.pk),
        "event": str(uuid.UUID(str(event_key))),
        "outcome": outcome,
        "amount": str(attempt.order.amount),
        "currency": attempt.order.currency,
    }
    return payload, synthetic_signature(payload)


@transaction.atomic
def receive_event(user, payload, signature, *, mfa_version, account_version):
    test_mode()
    if not isinstance(payload, dict) or set(payload) != {
        "schema",
        "attempt",
        "event",
        "outcome",
        "amount",
        "currency",
    }:
        raise ValidationError("Invalid synthetic event")
    if payload["schema"] != "synthetic-promotion-payment-v1" or payload["outcome"] not in {
        "pending",
        "failed",
        "succeeded",
    }:
        raise ValidationError("Invalid synthetic event")
    if not isinstance(signature, str) or not constant_time_compare(
        signature, synthetic_signature(payload)
    ):
        raise PermissionDenied("Invalid synthetic event authentication")
    current = actor(user, mfa_version, account_version)
    initial = PromotionPaymentAttempt.objects.select_related("order__listing").get(
        pk=uuid.UUID(payload["attempt"])
    )
    if initial.order.buyer_id != current.pk:
        raise PermissionDenied
    person = locked_manager_person(current, initial.order.listing.person_id)
    listing = (
        Listing.objects.select_for_update()
        .select_related("approved_revision", "person")
        .get(pk=initial.order.listing_id)
    )
    order = PromotionOrder.objects.select_for_update().get(pk=initial.order_id)
    attempt = PromotionPaymentAttempt.objects.select_for_update().get(pk=initial.pk)
    current = authorize(user, person, listing, mfa_version, account_version)
    if person.manager_version != order.manager_version or order.status == "cancelled":
        raise PermissionDenied("Order management or state changed")
    if payload["amount"] != str(order.amount) or payload["currency"] != order.currency:
        raise ValidationError("Synthetic payment amount mismatch")
    key = uuid.UUID(payload["event"])
    payload_digest = digest(payload)
    previous = PromotionPaymentEvent.objects.filter(event_key=key).first()
    if previous:
        if previous.attempt_id != attempt.pk or previous.payload_digest != payload_digest:
            raise ValidationError("Event key conflict")
        authorize(user, person, listing, mfa_version, account_version)
        return order
    if attempt.status == "succeeded" and payload["outcome"] != "succeeded":
        raise ValidationError("Successful synthetic payment is terminal")
    try:
        with transaction.atomic():
            PromotionPaymentEvent.objects.create(
                attempt=attempt,
                event_key=key,
                payload_digest=payload_digest,
                outcome=payload["outcome"],
            )
            attempt.status = payload["outcome"]
            attempt.save(update_fields=["status"])
            if payload["outcome"] == "succeeded":
                order.status = "paid"
                order.save(update_fields=["status"])
                now = timezone.now()
                PromotionEntitlement.objects.get_or_create(
                    order=order,
                    defaults={
                        "starts_at": now,
                        "ends_at": now + timedelta(days=order.duration_days),
                    },
                )
            audit(current, order, "synthetic_" + payload["outcome"])
    except IntegrityError:
        raise ValidationError("Concurrent event key conflict") from None
    authorize(user, person, listing, mfa_version, account_version)
    return order
