"""Catalogue-only flow, permissions, versions and PostgreSQL concurrency."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401

from apps.catalog.promotion_models import PromotionProductVersion
from apps.catalog.promotion_services import (
    create_product,
    create_version,
    publish_version,
    update_version,
)
from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)


def manager(request):
    request.getfixturevalue("directory")
    actor = User.objects.get(username="fixture-v1-moderator")
    actor.user_permissions.add(Permission.objects.get(codename="manage_promotion_products"))
    actor = User.objects.get(pk=actor.pk)
    staff = Client()
    staff.force_login(actor)
    session = staff.session
    session["mfa_version"] = actor.mfa_version
    session["account_version"] = actor.session_version
    session.save()
    return actor, staff


def data(row, **changes):
    return (
        dict(
            name_es="Promoción sintética",
            name_en="Synthetic promotion",
            duration_days=10,
            amount=None,
            currency="",
            tax_rate=None,
            bump_interval_minutes=None,
            daily_bump_limit=None,
        )
        | changes
    )


@pytest.mark.parametrize("language", ["es", "en"])
def test_incomplete_preview_release_new_version_and_csrf(request, language):
    actor, staff = manager(request)
    path = f"/{language}/operations/promotion-products/"
    assert Client().get(path).status_code == 302
    response = staff.get(path)
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    created = staff.post(path, {"slug": "synthetic_top_10", "kind": "top"})
    assert created.status_code == 302
    row = PromotionProductVersion.objects.get()
    assert row.amount is None and not row.configuration_ready and not row.sellable
    base = path + f"{row.product_id}/versions/{row.version}/"
    payload = data(row) | {"edit_version": row.edit_version}
    for name in ["amount", "tax_rate", "bump_interval_minutes", "daily_bump_limit"]:
        payload[name] = ""
    assert staff.post(base, payload).status_code == 302
    row.refresh_from_db()
    preview = staff.get(base + "preview/")
    assert preview.status_code == 200 and b"0.00" not in preview.content
    assert staff.post(base + "preview/", {"edit_version": row.edit_version}).status_code == 302
    row.refresh_from_db()
    assert row.is_current and row.published_at and not row.sellable
    assert staff.post(base, payload).status_code == 409
    assert staff.post(path + f"{row.product_id}/").status_code == 302
    next_row = row.product.versions.get(version=2)
    assert next_row.published_at is None and next_row.amount is None
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(actor)
    session = csrf.session
    session["mfa_version"] = actor.mfa_version
    session["account_version"] = actor.session_version
    session.save()
    assert csrf.post(path, {"slug": "synthetic_forgery", "kind": "premium"}).status_code == 403


@pytest.mark.parametrize("change", ["permission", "session", "mfa"])
def test_cached_actor_revocation_denies_without_catalogue_effects(request, change):
    actor, _ = manager(request)
    row = create_product(
        actor, actor.mfa_version, actor.session_version, {"slug": "synthetic_top", "kind": "top"}
    )
    assert actor.has_perm("catalog.manage_promotion_products")
    if change == "permission":
        actor.user_permissions.clear()
    else:
        field = "session_version" if change == "session" else "mfa_version"
        User.objects.filter(pk=actor.pk).update(**{field: getattr(actor, field) + 1})
    with pytest.raises(PermissionDenied):
        create_version(actor, actor.mfa_version, actor.session_version, row.product_id)
    assert row.product.versions.count() == 1


def test_invalid_values_stale_edit_and_released_payload_preserved(request):
    actor, _ = manager(request)
    auth = actor, actor.mfa_version, actor.session_version
    row = create_product(*auth, {"slug": "synthetic_premium", "kind": "premium"})
    for changes in [
        {"duration_days": 0},
        {"amount": Decimal("0")},
        {"tax_rate": Decimal("101")},
        {"daily_bump_limit": 2},
    ]:
        with pytest.raises(ValidationError):
            update_version(*auth, row.product_id, 1, 1, data(row, **changes))
    row.refresh_from_db()
    assert row.edit_version == 1 and row.amount is None
    row = update_version(
        *auth,
        row.product_id,
        1,
        1,
        data(row, amount=Decimal("12.34"), currency="EUR", tax_rate=Decimal("17.25")),
    )
    assert row.configuration_ready and not row.sellable
    with pytest.raises(ValidationError):
        update_version(*auth, row.product_id, 1, 1, data(row))
    publish_version(*auth, row.product_id, 1, 2)
    with pytest.raises(ValidationError):
        update_version(*auth, row.product_id, 1, 2, data(row))
    next_row = create_version(*auth, row.product_id)
    publish_version(*auth, row.product_id, 2, next_row.edit_version)
    row.refresh_from_db()
    assert row.amount == Decimal("12.34") and not row.is_current
    assert row.product.versions.filter(is_current=True).count() == 1


def test_concurrent_new_versions_serialize_on_product(request):
    actor, _ = manager(request)
    row = create_product(
        actor,
        actor.mfa_version,
        actor.session_version,
        {"slug": "synthetic_bump", "kind": "autobump"},
    )
    barrier = Barrier(2)

    def create():
        close_old_connections()
        try:
            user = User.objects.get(pk=actor.pk)
            barrier.wait(timeout=10)
            return create_version(
                user, user.mfa_version, user.session_version, row.product_id
            ).version
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create) for _ in range(2)]
        assert sorted(f.result(timeout=20) for f in futures) == [2, 3]
