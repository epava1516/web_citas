"""Catalogue-only flow, permissions, versions and PostgreSQL concurrency."""

import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier, Event

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection, connections, transaction
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401

from apps.catalog.promotion_models import (
    PromotionCatalogueAudit,
    PromotionProduct,
    PromotionProductVersion,
)
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


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_catalogue_navigation_save_release_reload(request, live_server, settings, language):
    settings.DEBUG = True
    actor, staff = manager(request)
    cookie = staff.cookies[settings.SESSION_COOKIE_NAME].value
    english = language == "en"
    catalogue = "Promotion catalogue" if english else "Catálogo de promociones"
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
                        "value": cookie,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(live_server.url + f"/{language}/account/")
            page.get_by_role("link", name=catalogue, exact=True).click()
            expect(page.get_by_role("heading", name=catalogue, exact=True)).to_be_visible()
            page.locator("[name=slug]").fill("synthetic_mobile_top")
            page.locator("[name=kind]").select_option("top")
            page.get_by_role(
                "button", name="Create product" if english else "Crear producto"
            ).click()
            page.locator("[name=name_es]").fill("Promoción móvil sintética")
            page.locator("[name=name_en]").fill("Synthetic mobile promotion")
            page.get_by_role("button", name="Save draft" if english else "Guardar borrador").click()
            expect(
                page.get_by_role(
                    "heading",
                    name=("Synthetic mobile promotion" if english else "Promoción móvil sintética"),
                    exact=True,
                )
            ).to_be_visible()
            expect(
                page.get_by_text(
                    "Configuration pending. Sales inactive."
                    if english
                    else "Pendiente de configurar. Ventas inactivas.",
                    exact=True,
                )
            ).to_be_visible()
            page.get_by_role(
                "button", name=("Release configuration" if english else "Publicar configuración")
            ).click()
            page.reload()
            expect(
                page.get_by_role(
                    "button",
                    name=("Release configuration" if english else "Publicar configuración"),
                )
            ).to_have_count(0)
            assert "0.00" not in page.content()
        finally:
            browser.close()
    row = PromotionProductVersion.objects.get(product__slug="synthetic_mobile_top")
    assert row.published_at and row.is_current and not row.sellable
    assert row.amount is None and row.name_en == "Synthetic mobile promotion"


def test_audit_is_atomic_minimal_and_release_replay_does_not_duplicate(request, monkeypatch):
    actor, _ = manager(request)
    auth = actor, actor.mfa_version, actor.session_version
    row = create_product(*auth, {"slug": "synthetic_audit", "kind": "top"})
    event = PromotionCatalogueAudit.objects.get()
    assert event.actor == actor and event.product_version == row
    assert event.operation == "create_product" and len(event.payload_digest) == 64
    row = update_version(*auth, row.product_id, 1, 1, data(row))
    publish_version(*auth, row.product_id, 1, row.edit_version)
    publish_version(*auth, row.product_id, 1, row.edit_version)
    assert list(PromotionCatalogueAudit.objects.values_list("operation", flat=True)) == [
        "create_product",
        "update_version",
        "publish_version",
    ]

    def fail(*args, **kwargs):
        raise RuntimeError("Synthetic audit storage failure")

    monkeypatch.setattr(PromotionCatalogueAudit.objects, "create", fail)
    with pytest.raises(RuntimeError):
        create_product(*auth, {"slug": "synthetic_rollback", "kind": "premium"})
    assert not PromotionProduct.objects.filter(slug="synthetic_rollback").exists()
    assert PromotionCatalogueAudit.objects.count() == 3


@pytest.mark.parametrize("operation", ["create", "update", "publish", "replay"])
@pytest.mark.parametrize("change", ["permission", "session", "mfa"])
def test_revocation_during_observed_product_lock_denies_without_effects(request, operation, change):
    actor, _ = manager(request)
    auth = actor, actor.mfa_version, actor.session_version
    row = create_product(*auth, {"slug": "synthetic_locked", "kind": "top"})
    if operation == "replay":
        publish_version(*auth, row.product_id, 1, row.edit_version)
    original_audits = PromotionCatalogueAudit.objects.count()
    ready = Event()
    backend = {}

    def mutate():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend["pid"] = cursor.fetchone()[0]
            user = User.objects.get(pk=actor.pk)
            ready.set()
            args = user, user.mfa_version, user.session_version
            try:
                if operation == "create":
                    create_version(*args, row.product_id)
                elif operation == "update":
                    update_version(*args, row.product_id, 1, row.edit_version, data(row))
                else:
                    publish_version(*args, row.product_id, 1, row.edit_version)
            except PermissionDenied:
                return "denied"
            return "allowed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            PromotionProduct.objects.select_for_update().get(pk=row.product_id)
            future = pool.submit(mutate)
            assert ready.wait(timeout=5)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                own_pid = cursor.fetchone()[0]
                deadline = time.monotonic() + 5
                blocked = False
                while time.monotonic() < deadline:
                    cursor.execute("SELECT pg_blocking_pids(%s)", [backend["pid"]])
                    blocked = own_pid in cursor.fetchone()[0]
                    if blocked:
                        break
                    time.sleep(0.02)
            assert blocked and not future.done()
            if change == "permission":
                actor.user_permissions.clear()
            else:
                field = "session_version" if change == "session" else "mfa_version"
                User.objects.filter(pk=actor.pk).update(**{field: getattr(actor, field) + 1})
        assert future.result(timeout=10) == "denied"
    row.refresh_from_db()
    assert row.product.versions.count() == 1 and row.edit_version == 1
    assert bool(row.published_at) == (operation == "replay")
    assert PromotionCatalogueAudit.objects.count() == original_audits


@pytest.mark.parametrize("language", ["es", "en"])
def test_direct_routes_deny_unprivileged_account_and_get_has_no_effect(request, language):
    actor, staff = manager(request)
    row = create_product(
        actor,
        actor.mfa_version,
        actor.session_version,
        {"slug": "synthetic_private_catalogue", "kind": "top"},
    )
    root = f"/{language}/operations/promotion-products/"
    edit = root + f"{row.product_id}/versions/1/"
    routes = [root, root + f"{row.product_id}/", edit, edit + "preview/"]
    before = PromotionCatalogueAudit.objects.count()
    for route in routes:
        response = staff.get(route)
        assert response.status_code == 200
        assert response["X-Robots-Tag"] == "noindex, nofollow"
        assert "no-store" in response["Cache-Control"]
    assert PromotionCatalogueAudit.objects.count() == before
    actor.user_permissions.clear()
    for route in routes:
        for method in [staff.get, staff.post]:
            response = method(route)
            assert response.status_code == 403
            assert b"synthetic_private_catalogue" not in response.content
    assert PromotionCatalogueAudit.objects.count() == before
    assert row.product.versions.count() == 1


def test_invalid_http_form_returns_error_without_mutating_draft(request):
    actor, staff = manager(request)
    root = "/en/operations/promotion-products/"
    assert staff.post(root, {"slug": "invalid spaces", "kind": "unknown"}).status_code == 400
    assert not PromotionProduct.objects.exists()
    row = create_product(
        actor,
        actor.mfa_version,
        actor.session_version,
        {"slug": "synthetic_invalid_form", "kind": "top"},
    )
    edit = root + f"{row.product_id}/versions/1/"
    assert staff.post(edit, {"edit_version": 1, "duration_days": 0}).status_code == 400
    assert staff.post(edit + "preview/", {"edit_version": "invalid"}).status_code == 409
    row.refresh_from_db()
    assert row.duration_days == 10 and row.edit_version == 1 and row.published_at is None
    assert PromotionCatalogueAudit.objects.count() == 1


def test_concurrent_releases_preserve_one_current_version_and_both_snapshots(request):
    actor, _ = manager(request)
    auth = actor, actor.mfa_version, actor.session_version
    first = create_product(*auth, {"slug": "synthetic_release_race", "kind": "top"})
    second = create_version(*auth, first.product_id)
    barrier = Barrier(2)

    def release(number):
        close_old_connections()
        try:
            user = User.objects.get(pk=actor.pk)
            barrier.wait(timeout=10)
            return publish_version(
                user, user.mfa_version, user.session_version, first.product_id, number, 1
            ).version
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(release, row.version) for row in (first, second)]
        assert sorted(f.result(timeout=20) for f in futures) == [1, 2]
    rows = first.product.versions.all()
    assert rows.filter(is_current=True).count() == 1
    assert rows.filter(published_at__isnull=False).count() == 2
    assert PromotionCatalogueAudit.objects.filter(operation="publish_version").count() == 2
    assert all(row.duration_days == 10 and row.amount is None for row in rows)
