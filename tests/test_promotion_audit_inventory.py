"""Synthetic audit census fixtures; no actual catalogue operation acceptance."""

import pytest
from django.db import transaction
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.catalog.promotion_models import (
    PromotionCatalogueAudit,
    PromotionProduct,
    PromotionProductVersion,
)
from apps.core.models import User
from apps.safety.erasure_inventory import source_manifest
from apps.safety.rights_access_scope_inventory import source as access_source
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("scope", ["account", "profile"])
def test_operator_audit_is_scoped_and_changes_invalidate_inventory(
    request, settings, monkeypatch, scope
):
    if scope == "account":
        case, _, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, _, _, _, _, person = ready(request, settings, monkeypatch, "access")
        subject = person.subject
    product = PromotionProduct.objects.create(slug="synthetic_inventory", kind="top")
    row = PromotionProductVersion.objects.create(
        product=product, version=1, name_es="Sintético", name_en="Synthetic", duration_days=10
    )
    foreign = User.objects.get(username="fixture-v1-visitor")
    assert foreign.pk != subject.pk

    def capture():
        with transaction.atomic():
            current, person, _ = locked_case(case.pk, lock_listing=True)
            a = access_source(current, person)
            e = source_manifest(person, current)
            return tuple(
                next(
                    item
                    for item in body["entries"]
                    if item["model"] == "catalog.PromotionCatalogueAudit"
                )
                for body in (a, e)
            )

    before = capture()
    assert all(item["count"] == 0 for item in before)
    PromotionCatalogueAudit.objects.create(
        actor=foreign,
        product_version=row,
        operation="create_product",
        edit_version=1,
        payload_digest="0" * 64,
    )
    assert capture() == before
    own = PromotionCatalogueAudit.objects.create(
        actor=subject,
        product_version=row,
        operation="create_product",
        edit_version=1,
        payload_digest="1" * 64,
    )
    after = capture()
    assert all(item["count"] == 1 and item["purpose"] == "dependent_evidence" for item in after)
    for field, old, new in zip(["digest", "state_digest"], before, after):
        assert old[field] != new[field]
    own.payload_digest = "2" * 64
    own.save(update_fields=["payload_digest"])
    changed = capture()
    assert all(item["count"] == 1 for item in changed)
    for field, old, new in zip(["digest", "state_digest"], after, changed):
        assert old[field] != new[field]
