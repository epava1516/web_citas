"""Extend the real restore scenario with retained commercial dependent evidence."""

import hashlib
import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
import test_erasure_execution as erasure_fixture
import test_recovery_pg_restore as recovery
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401

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
from apps.safety.erasure_inventory import canonical
from apps.safety.models import RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)

MODELS = [
    PromotionOrder,
    PromotionPaymentAttempt,
    PromotionPaymentEvent,
    PromotionEntitlement,
    PromotionBumpExecution,
    PromotionOrderAudit,
]


def test_real_restore_preserves_commercial_evidence_without_reactivating_erased_promotion(
    request, settings, monkeypatch, tmp_path, record_property
):
    original_inventory = erasure_fixture.inventory
    commercial = {}

    def with_commercial(*args, **kwargs):
        if not commercial:
            person = RightsRequest.objects.get(pk=args[1]).person
            buyer = person.agency.owner if person.agency_id else person.individual
            buyer.mfa_enabled = True
            buyer.save(update_fields=["mfa_enabled"])
            product = PromotionProduct.objects.create(slug="synthetic-recovery", kind="autobump")
            version = PromotionProductVersion.objects.create(
                product=product, version=1, name_es="Prueba", name_en="Test", duration_days=10
            )

            def order(selected, actor):
                return PromotionOrder.objects.create(
                    buyer=actor,
                    listing=selected.listing,
                    product_version=version,
                    manager_version=selected.manager_version,
                    idempotency_key=uuid.uuid4(),
                    request_digest="1" * 64,
                    amount=Decimal("12.00"),
                    net_amount=Decimal("10.00"),
                    tax_amount=Decimal("2.00"),
                    tax_rate=Decimal("20"),
                    kind="autobump",
                    duration_days=10,
                    bump_interval_minutes=10,
                    daily_bump_limit=10,
                    status="paid",
                )

            own = order(person, buyer)
            peer = Person.objects.exclude(pk=person.pk).first()
            order(peer, User.objects.get(username="fixture-v1-visitor"))
            attempt = PromotionPaymentAttempt.objects.create(order=own, status="succeeded")
            PromotionPaymentEvent.objects.create(
                attempt=attempt,
                event_key=uuid.uuid4(),
                payload_digest="2" * 64,
                outcome="succeeded",
            )
            entitlement = PromotionEntitlement.objects.create(
                order=own,
                starts_at=timezone.now() - timedelta(hours=1),
                ends_at=timezone.now() + timedelta(days=10),
            )
            PromotionBumpExecution.objects.create(
                entitlement=entitlement, window_start=timezone.now() - timedelta(minutes=30)
            )
            PromotionOrderAudit.objects.create(
                actor=buyer, order=own, operation="synthetic_succeeded", payload_digest="3" * 64
            )
            rows = {model.__name__: list(model.objects.order_by("pk").values()) for model in MODELS}
            commercial.update(
                entitlement=str(entitlement.pk),
                digest=hashlib.sha256(canonical(rows).encode()).hexdigest(),
            )
        return original_inventory(*args, **kwargs)

    monkeypatch.setattr(erasure_fixture, "inventory", with_commercial)
    original_child = recovery.CHILD
    check = """
    from apps.catalog.promotion_exposure import ranked,bump_one
    from apps.catalog.promotion_order_models import PromotionOrder,PromotionPaymentAttempt,PromotionPaymentEvent,PromotionEntitlement,PromotionBumpExecution,PromotionOrderAudit
    with override_settings(RECOVERY_MODE=False,PROMOTION_TEST_MODE=True):
        models=[PromotionOrder,PromotionPaymentAttempt,PromotionPaymentEvent,PromotionEntitlement,PromotionBumpExecution,PromotionOrderAudit]
        rows={model.__name__:list(model.objects.order_by('pk').values()) for model in models}
        assert hashlib.sha256(canonical(rows).encode()).hexdigest()==COMMERCIAL_DIGEST
        entitlement=PromotionEntitlement.objects.get(pk=COMMERCIAL_ENTITLEMENT)
        listing=entitlement.order.listing
        assert not ranked([listing])[1]
        assert not bump_one(entitlement.pk)
        assert PromotionBumpExecution.objects.count()==1
"""
    # Resolve fixture identifiers only after the native parent has built its inventory.
    original_run = recovery.subprocess.run

    def run(*args, **kwargs):
        command = args[0] if args else kwargs.get("args")
        if isinstance(command, list) and "-c" in command and original_child in command:
            command = list(command)
            index = command.index(original_child)
            injected = check.replace("COMMERCIAL_DIGEST", repr(commercial["digest"])).replace(
                "COMMERCIAL_ENTITLEMENT", repr(commercial["entitlement"])
            )
            marker = "    # RECOVERY_EXTENSION_ASSERTIONS"
            assert original_child.count(marker) == 1
            command[index] = original_child.replace(marker, injected + marker)
            assert injected in command[index]
            commercial["child_checked"] = True
            args = (command,) + args[1:]
        return original_run(*args, **kwargs)

    monkeypatch.setattr(recovery.subprocess, "run", run)
    recovery.test_old_pg_dump_and_media_cannot_reintroduce_erased_data(
        request, settings, monkeypatch, tmp_path, record_property, encrypted_backup=True
    )
    assert commercial.get("child_checked") is True
    record_property("commercial_restore_checks", {
        "retained_rows_digest": commercial["digest"],
        "restored_child_assertions_completed": True,
        "erased_promotion_not_ranked_or_bumped": True,
    })
