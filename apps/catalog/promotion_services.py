"""Catalogue-only mutations, fresh MFA/session authority and immutable released payloads."""

import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.core.models import User

from .promotion_models import PromotionCatalogueAudit, PromotionProduct, PromotionProductVersion

EDITABLE = (
    "name_es",
    "name_en",
    "duration_days",
    "amount",
    "currency",
    "tax_rate",
    "bump_interval_minutes",
    "daily_bump_limit",
)


def audit(actor, row, operation):
    payload = {field: getattr(row, field) for field in EDITABLE}
    payload.update(
        product=str(row.product_id),
        version=row.version,
        edit_version=row.edit_version,
        published_at=row.published_at,
        is_current=row.is_current,
    )
    PromotionCatalogueAudit.objects.create(
        actor=actor,
        product_version=row,
        operation=operation,
        edit_version=row.edit_version,
        payload_digest=hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False).encode()
        ).hexdigest(),
    )


def fresh_actor(user, mfa_version, account_version):
    actor = User.objects.get(pk=user.pk)
    if (
        not actor.is_active
        or not actor.mfa_enabled
        or actor.session_version != user.session_version
        or actor.mfa_version != user.mfa_version
        or mfa_version != actor.mfa_version
        or account_version != actor.session_version
        or not actor.has_perm("catalog.manage_promotion_products")
    ):
        raise PermissionDenied
    return actor


def authority(user, mfa_version, account_version):
    return fresh_actor(user, mfa_version, account_version)


def draft(product, number):
    name = {"premium": "Premium", "top": "Top", "autobump": "Autosubida"}[product.kind]
    return PromotionProductVersion.objects.create(
        product=product,
        version=number,
        name_es=name,
        name_en="Auto bump" if product.kind == "autobump" else name,
        duration_days={"premium": 30, "top": 10, "autobump": 7}[product.kind],
    )


@transaction.atomic
def create_product(user, mfa_version, account_version, values):
    fresh_actor(user, mfa_version, account_version)
    product = PromotionProduct(slug=values["slug"], kind=values["kind"])
    product.full_clean()
    product.save()
    row = draft(product, 1)
    actor = fresh_actor(user, mfa_version, account_version)
    audit(actor, row, "create_product")
    return row


@transaction.atomic
def create_version(user, mfa_version, account_version, product_id):
    fresh_actor(user, mfa_version, account_version)
    product = PromotionProduct.objects.select_for_update().get(pk=product_id)
    fresh_actor(user, mfa_version, account_version)
    number = (product.versions.aggregate(value=Max("version"))["value"] or 0) + 1
    row = draft(product, number)
    actor = fresh_actor(user, mfa_version, account_version)
    audit(actor, row, "create_version")
    return row


@transaction.atomic
def update_version(user, mfa_version, account_version, product_id, number, edit_version, values):
    fresh_actor(user, mfa_version, account_version)
    product = PromotionProduct.objects.select_for_update().get(pk=product_id)
    row = PromotionProductVersion.objects.select_for_update().get(product=product, version=number)
    fresh_actor(user, mfa_version, account_version)
    if row.published_at is not None or row.edit_version != edit_version:
        raise ValidationError("Versión publicada o modificada / Released or changed version")
    if set(values) != set(EDITABLE):
        raise ValidationError("Campos de producto inválidos / Invalid product fields")
    for field in EDITABLE:
        setattr(row, field, values[field])
    row.edit_version += 1
    row.full_clean()
    row.save()
    actor = fresh_actor(user, mfa_version, account_version)
    audit(actor, row, "update_version")
    return row


@transaction.atomic
def publish_version(user, mfa_version, account_version, product_id, number, edit_version):
    fresh_actor(user, mfa_version, account_version)
    product = PromotionProduct.objects.select_for_update().get(pk=product_id)
    row = PromotionProductVersion.objects.select_for_update().get(product=product, version=number)
    fresh_actor(user, mfa_version, account_version)
    if row.edit_version != edit_version:
        raise ValidationError("Versión modificada / Version changed")
    if row.is_current:
        return row
    if row.published_at is not None:
        raise ValidationError("Crear una nueva versión / Create a new version")
    row.full_clean()
    product.versions.filter(is_current=True).update(is_current=False)
    row.published_at = timezone.now()
    row.is_current = True
    row.save(update_fields=["published_at", "is_current"])
    actor = fresh_actor(user, mfa_version, account_version)
    audit(actor, row, "publish_version")
    return row
