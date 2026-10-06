import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import transaction
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_order_models import (
    PromotionBumpExecution,
    PromotionEntitlement,
    PromotionOrder,
    PromotionOrderAudit,
    PromotionPaymentAttempt,
    PromotionPaymentEvent,
)
from apps.core.models import Person, User
from apps.listings.models import Listing
from apps.safety.erasure_inventory import source_manifest
from apps.safety.rights_access_scope_inventory import source as access_source
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("scope", ["account", "profile"])
def test_commercial_records_are_scoped_and_mutations_invalidate_both_inventories(
    request, settings, monkeypatch, scope
):
    if scope == "account":
        case, _, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
        person, _ = Person.objects.get_or_create(
            individual=subject, defaults={"alias": "Synthetic", "subject": subject}
        )
    else:
        case, _, _, _, _, person = ready(request, settings, monkeypatch, "access")
        subject = person.subject
    listing, _ = Listing.objects.get_or_create(person=person)
    product = PromotionProduct.objects.create(slug="synthetic_orders", kind="top")
    version = PromotionProductVersion.objects.create(
        product=product, version=1, name_es="Prueba", name_en="Test", duration_days=10
    )

    def capture():
        with transaction.atomic():
            current, current_person, _ = locked_case(case.pk, lock_listing=True)
            return [
                {
                    r["model"]: r
                    for r in body["entries"]
                    if r["model"].startswith("catalog.Promotion")
                    and r["model"] != "catalog.PromotionCatalogueAudit"
                }
                for body in [
                    access_source(current, current_person),
                    source_manifest(current_person, current),
                ]
            ]

    def order(buyer, selected):
        return PromotionOrder.objects.create(
            buyer=buyer,
            listing=selected,
            product_version=version,
            manager_version=1,
            idempotency_key=uuid.uuid4(),
            request_digest="1" * 64,
            amount=Decimal("12.00"),
            net_amount=Decimal("10.00"),
            tax_amount=Decimal("2.00"),
            tax_rate=Decimal("20"),
            kind="top",
            duration_days=10,
        )

    before = capture()
    foreign = User.objects.get(username="fixture-v1-visitor")
    foreign_person, _ = Person.objects.get_or_create(
        individual=foreign, defaults={"alias": "Foreign"}
    )
    foreign_listing, _ = Listing.objects.get_or_create(person=foreign_person)
    foreign_order = order(foreign, foreign_listing)
    PromotionOrderAudit.objects.create(
        actor=foreign, order=foreign_order, operation="create", payload_digest="0" * 64
    )
    assert capture() == before
    own = order(subject, listing)
    attempt = PromotionPaymentAttempt.objects.create(order=own)
    event = PromotionPaymentEvent.objects.create(
        attempt=attempt, event_key=uuid.uuid4(), payload_digest="1" * 64, outcome="pending"
    )
    entitlement = PromotionEntitlement.objects.create(
        order=own, starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=10)
    )
    bump = PromotionBumpExecution.objects.create(
        entitlement=entitlement, window_start=timezone.now()
    )
    audit = PromotionOrderAudit.objects.create(
        actor=subject, order=own, operation="create", payload_digest="1" * 64
    )
    after = capture()
    assert all(len(body) == 6 for body in after)
    for index, digest in enumerate(["digest", "state_digest"]):
        for label, entry in after[index].items():
            assert entry["count"] == 1 and entry["purpose"] == "dependent_evidence"
            assert entry[digest] != before[index][label][digest]
    own.status = "cancelled"
    own.save(update_fields=["status"])
    attempt.status = "failed"
    attempt.save(update_fields=["status"])
    event.outcome = "failed"
    event.save(update_fields=["outcome"])
    entitlement.suspended_at = timezone.now()
    entitlement.save(update_fields=["suspended_at"])
    bump.window_start += timedelta(minutes=1)
    bump.save(update_fields=["window_start"])
    audit.payload_digest = "2" * 64
    audit.save(update_fields=["payload_digest"])
    changed = capture()
    for index, digest in enumerate(["digest", "state_digest"]):
        for label, entry in changed[index].items():
            assert entry["count"] == 1 and entry[digest] != after[index][label][digest]
