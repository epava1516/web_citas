"""Explicit finite commercial references; no provider, native checkout100 or optimization claim."""

import hashlib
import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
from html.parser import HTMLParser
from math import ceil
from pathlib import Path

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.utils import timezone, translation
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.promotion_models import (
    PromotionCatalogueAudit,
    PromotionProduct,
    PromotionProductVersion,
)
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
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)
COMMERCIAL_MODELS = (
    PromotionProduct, PromotionProductVersion, PromotionCatalogueAudit,
    PromotionOrder, PromotionPaymentAttempt, PromotionPaymentEvent,
    PromotionEntitlement, PromotionBumpExecution, PromotionOrderAudit,
)
SCOPE = (
    "Finite current synthetic Django Client reference, first plus5 subsequent GETs per segment; "
    "native25/50 pagination; complete body within wall/processCPU intervals; independent connection "
    "execute_wrapper integer cursor count/time, no debug queries_log or circular buffer. "
    "Setup/oracles/snapshots outside clocks. Global nested HTTP observer is separate, never summed. "
    "Negative GETs and distinct native catalogue POSTs are individual controls, not a retry/time distribution. "
    "No performance budget/gain/percentile, browser/network/provider/worker/live payment or CSRF claim."
)


class _FormHTML(HTMLParser):
    """Read actual rendered option identities/labels and blank numeric inputs."""

    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.selects, self.inputs = {}, {}
        self.current_select = self.current_option = None
        self.option_text = []
        self.feed(body.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "select":
            self.current_select = attrs.get("name")
            self.selects[self.current_select] = {}
        elif tag == "option" and self.current_select is not None:
            self.current_option = attrs.get("value", "")
            self.option_text = []
        elif tag == "input" and attrs.get("name"):
            self.inputs[attrs["name"]] = attrs.get("value", "")

    def handle_data(self, data):
        if self.current_option is not None:
            self.option_text.append(data)

    def handle_endtag(self, tag):
        if tag == "option" and self.current_select is not None:
            if self.current_option:
                self.selects[self.current_select][self.current_option] = "".join(self.option_text).strip()
            self.current_option = None
        elif tag == "select":
            self.current_select = None


def _guard(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit finite owned serial commercial reference only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert connection.vendor == "postgresql" and not settings.PRODUCTION
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    language = translation.get_language()
    request.addfinalizer(lambda: translation.activate(language))


def _snapshot():
    # All scalar columns, including all audit/ledger rows, remain local to the test.
    return {model._meta.label: list(model.objects.order_by("pk").values())
            for model in COMMERCIAL_MODELS}


def _digest(snapshot):
    return hashlib.sha256(repr(snapshot).encode()).hexdigest()


@contextmanager
def _report(record_property, rows, controls, metadata):
    try:
        yield
    finally:
        record_property("commercial_surface_samples", json.dumps({
            "rows": rows, "controls": controls, "scope": SCOPE, "metadata": metadata,
        }, sort_keys=True))


def _request(client, path, rows, *, method="GET", payload=None, **labels):
    totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

    def observe(execute, sql, params, many, context):
        totals["sql_queries"] += 1
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            totals["sql_execute_seconds"] += time.perf_counter() - started

    cpu_started = time.process_time()
    started = time.perf_counter()
    with connection.execute_wrapper(observe):
        response = client.get(path) if method == "GET" else client.post(path, payload)
        body = response.content
    totals.update(wall_seconds=time.perf_counter() - started,
                  cpu_seconds=time.process_time() - cpu_started)
    match = response.resolver_match
    rows.append({
        **labels, "method": method, "status": response.status_code,
        "route_name": match.view_name, "path": match.route, "path_is_resolver_shape": True,
        "response_language": response.wsgi_request.LANGUAGE_CODE,
        "response_bytes": len(body), "headers": {
            name: response.get(name) for name in ["Cache-Control", "Content-Language", "Content-Type",
                                                  "X-Robots-Tag", "Referrer-Policy"]
        }, **totals,
    })
    return response, body


def _private(response, route, language):
    assert response.status_code == 200 and response.resolver_match.view_name == route
    assert response.wsgi_request.LANGUAGE_CODE == response["Content-Language"] == language
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert response["Referrer-Policy"] == "same-origin"


def _segment(client, path, rows, *, route, language, axis, cohort, page, check):
    before = _snapshot()
    before_sha = _digest(before)
    for ordinal in range(6):
        response, body = _request(client, path, rows, axis=axis, cohort=cohort, language=language,
                                  page=page, ordinal=ordinal, snapshot_sha256=before_sha)
        _private(response, route, language)
        check(response, body)
    assert _snapshot() == before, "GET segment changed commercial domain rows"


def _client(username, *, catalogue_permission=False):
    user = User.objects.get(username=username)
    if not user.mfa_enabled:
        user.mfa_enabled = True
        user.save(update_fields=["mfa_enabled"])
    if catalogue_permission:
        user.user_permissions.add(Permission.objects.get(
            codename="manage_promotion_products", content_type__app_label="catalog"))
        user = User.objects.get(pk=user.pk)
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session["account_version"] = user.session_version
    session.save()
    return user, client


def _negative(client, path, controls, *, language, state, status, redirect=None, forbidden=()):
    before = _snapshot()
    response, body = _request(client, path, controls, language=language, state=state,
                              kind="negative_get", ordinal=0, snapshot_sha256=_digest(before))
    assert response.status_code == status
    assert response.wsgi_request.LANGUAGE_CODE == response["Content-Language"] == language
    if redirect is not None:
        if redirect == "login":
            assert response.url.startswith(reverse("login") + "?next=")
        else:
            assert response.url == reverse(redirect)
    if response.wsgi_request.user.is_authenticated:
        assert response["Cache-Control"] == "private, no-store"
    assert all(str(value).encode() not in body for value in forbidden)
    assert _snapshot() == before


def _stale_mfa(user, client, path, controls, language):
    session = client.session
    session["mfa_version"] = user.mfa_version + 1
    session.save()
    try:
        # Enabled MFA is checked in AccountGateMiddleware before view.actor()/authority().
        _negative(client, path, controls, language=language, state="stale_mfa",
                  status=302, redirect="mfa_challenge")
    finally:
        session = client.session
        session["mfa_version"] = user.mfa_version
        session.save()


def _product(index, *, published=True, active=True, kind="top", amount=Decimal("12.00"),
             currency="EUR", tax_rate=Decimal("20.00"), current=True, prefix="n08b"):
    product = PromotionProduct.objects.create(slug=f"{prefix}-{index:03d}", kind=kind, active=active)
    row = PromotionProductVersion.objects.create(
        product=product, version=1, name_es=f"Promoción sintética {index:03d}",
        name_en=f"Synthetic promotion {index:03d}", duration_days=10,
        amount=amount, currency=currency, tax_rate=tax_rate,
        published_at=timezone.now() if published else None, is_current=current,
    )
    assert not row.sellable
    return row


def _options(response, body, listings, versions, language):
    form = response.context["form"]
    assert {row.pk for row in form.fields["listing"].queryset} == {row.pk for row in listings}
    assert {row.pk for row in form.fields["product"].queryset} == {row.pk for row in versions}
    rendered = _FormHTML(body)
    assert rendered.selects["listing"] == {str(row.pk): row.person.alias for row in listings}
    assert rendered.selects["product"] == {
        str(row.pk): f'{row.name_en if language == "en" else row.name_es} · {row.amount} {row.currency}'
        for row in versions
    }
    warning = ("Simulation only. No money is charged." if language == "en"
               else "Solo simulación. No se cobra dinero.")
    assert warning.encode() in body
    assert all(not row.sellable for row in versions)


def _page(response, expected, total, size, number):
    page = response.context["page"]
    shown = list(page.object_list)
    assert [row.pk for row in shown] == [row.pk for row in expected]
    assert page.number == number and page.paginator.count == total
    assert page.paginator.per_page == size and page.paginator.num_pages == max(1, ceil(total / size))
    assert len(shown) == len({row.pk for row in shown})
    return shown


def _orders(buyer, listing, version, start, count):
    request_digest = hashlib.sha256(json.dumps({
        "listing": listing.pk, "version": version.pk, "manager": listing.person.manager_version,
    }, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
    rows = PromotionOrder.objects.bulk_create([
        PromotionOrder(buyer=buyer, listing=listing, product_version=version,
                       manager_version=listing.person.manager_version,
                       idempotency_key=uuid.uuid4(),
                       request_digest=request_digest,
                       amount=Decimal("12.00"), currency="EUR", tax_rate=Decimal("20.00"),
                       tax_amount=Decimal("2.00"), net_amount=Decimal("10.00"),
                       kind="top", duration_days=10, status="pending")
        for index in range(start, start + count)
    ])
    stamp = timezone.now() - timedelta(days=1)
    for index, row in enumerate(rows, start):
        row.created_at = stamp + timedelta(seconds=index)
    if rows:
        PromotionOrder.objects.bulk_update(rows, ["created_at"])
        PromotionPaymentAttempt.objects.bulk_create([PromotionPaymentAttempt(order=row) for row in rows])
    return rows


def _no_grants():
    assert not PromotionPaymentEvent.objects.exists()
    assert not PromotionEntitlement.objects.exists()
    assert not PromotionBumpExecution.objects.exists()


def test_commercial_history_and_detail_reference(request, settings, record_property):
    _guard(request, settings)
    request.getfixturevalue("directory")
    settings.PROMOTION_TEST_MODE = True
    user, client = _client("fixture-v1-individual")
    other, _ = _client("fixture-v1-agency")
    listing = Listing.objects.select_related("person").get(person__individual=user)
    foreign_listing = Listing.objects.select_related("person").get(
        person__subject__username="fixture-v1-model-a")
    assert not PromotionProduct.objects.exists() and not PromotionOrder.objects.exists()
    version = _product(0)
    foreign = _orders(other, foreign_listing, version, 900, 1)[0]
    own, rows, controls = [], [], []
    metadata = {"axis": "history_and_detail", "planned_measured_gets": 120,
                "planned_negative_gets": 8, "planned_posts": 0, "planned_total_calls": 128,
                "history_cohorts": [0, 1, 10, 26, 100], "native_page_size": 25,
                "fixed_listing_options": 1, "fixed_product_options": 1,
                "setup": "directory once; bulk pending orders and attempts; no native checkout100 or payments",
                "directory_calls": 1, "populate_calls": 0,
                "snapshot_scope": "all scalar columns of all9 commercial models; digest only"}
    with _report(record_property, rows, controls, metadata):
        for count in [0, 1, 10, 26, 100]:
            own.extend(_orders(user, listing, version, len(own), count - len(own)))
            ordered = sorted(own, key=lambda row: (row.created_at, row.pk), reverse=True)
            for language in ["es", "en"]:
                translation.activate(language)
                all_links = {row.pk: f'href="{reverse("promotion_order_detail", args=[row.pk])}"'.encode()
                             for row in [*own, foreign]}
                for number in range(1, max(1, ceil(count / 25)) + 1):
                    expected = ordered[(number - 1) * 25:number * 25]
                    expected_ids = {row.pk for row in expected}

                    def check(response, body):
                        shown = _page(response, expected, count, 25, number)
                        assert all(row.buyer_id == user.pk and row.synthetic and row.status == "pending" for row in shown)
                        _options(response, body, [listing], [version], language)
                        for identifier, link in all_links.items():
                            assert (link in body) == (identifier in expected_ids)
                        assert str(foreign.pk).encode() not in body

                    _segment(client, reverse("promotion_orders") + f"?page={number}", rows,
                             route="promotion_orders", language=language, axis="history", cohort=count,
                             page=number, check=check)
        selected = own[-1]
        for language in ["es", "en"]:
            translation.activate(language)

            def check_detail(response, body):
                row = response.context["order"]
                assert row.pk == selected.pk and row.buyer_id == user.pk and row.listing_id == listing.pk
                assert row.product_version_id == version.pk and row.status == "pending" and row.synthetic
                assert row.amount == Decimal("12.00") and row.net_amount == Decimal("10.00")
                assert row.tax_amount == Decimal("2.00") and row.tax_rate == Decimal("20.00")
                assert row.duration_days == 10 and row.manager_version == listing.person.manager_version
                assert row.payment_attempt.status == "pending"
                assert str(foreign.pk).encode() not in body
                warning = ("Simulation only. No real payment or service booking." if language == "en"
                           else "Solo simulación. Sin pago real ni reserva de servicios.")
                assert warning.encode() in body

            detail = reverse("promotion_order_detail", args=[selected.pk])
            _segment(client, detail, rows, route="promotion_order_detail", language=language,
                     axis="detail", cohort=100, page=0, check=check_detail)
            _negative(client, reverse("promotion_order_detail", args=[foreign.pk]), controls,
                      language=language, state="foreign_buyer_detail", status=404, forbidden=[foreign.pk])
            _negative(Client(), reverse("promotion_orders"), controls, language=language,
                      state="anonymous_history", status=302, redirect="login")
            _negative(Client(), detail, controls, language=language, state="anonymous_detail",
                      status=302, redirect="login", forbidden=[selected.pk])
            _stale_mfa(user, client, reverse("promotion_orders"), controls, language)
        assert PromotionOrder.objects.filter(buyer=user).count() == 100
        assert PromotionOrder.objects.count() == PromotionPaymentAttempt.objects.count() == 101
        assert not PromotionOrderAudit.objects.exists()
        _no_grants()
        assert len(rows) == 120 and len(controls) == 8
        metadata["readonly_segments_verified"] = True


def test_commercial_order_options_reference(request, settings, record_property):
    _guard(request, settings)
    request.getfixturevalue("directory")
    settings.PROMOTION_TEST_MODE = True
    population = populate(101)
    assert population["published"] == 101 and population["shared_synthetic_photo_fixture"]
    user, client = _client("fixture-v1-agency")
    managed = list(Listing.objects.filter(status="published", person__agency__owner=user)
                   .select_related("person").order_by("pk"))
    assert len(managed) == 100 and not PromotionOrder.objects.exists()
    foreign = Listing.objects.get(person__individual__username="fixture-v1-individual")
    agency = managed[0].person.agency
    for label, status, erased in [("paused", "paused", None), ("erased", "published", timezone.now())]:
        person = Person.objects.create(agency=agency, alias=f"Synthetic excluded {label}",
                                       publication_erased_at=erased)
        Listing.objects.create(person=person, status=status)
    assert not PromotionProduct.objects.exists()
    products = PromotionProduct.objects.bulk_create([
        PromotionProduct(slug=f"n08b-choice-{index:03d}", kind="autobump" if index == 99 else "top",
                         active=index == 0) for index in range(100)
    ])
    versions = PromotionProductVersion.objects.bulk_create([
        PromotionProductVersion(product=product, version=1, name_es=f"Opción sintética {index:03d}",
                                name_en=f"Synthetic option {index:03d}", duration_days=10,
                                amount=Decimal("12.00"), currency="EUR", tax_rate=Decimal("20.00"),
                                published_at=timezone.now(), is_current=True)
        for index, product in enumerate(products)
    ])
    decoys = [
        _product(0, prefix="n08b-decoy-inactive", active=False),
        _product(0, prefix="n08b-decoy-noncurrent", current=False),
        _product(0, prefix="n08b-decoy-draft", published=False, current=False),
        _product(0, prefix="n08b-decoy-nullamount", amount=None),
        _product(0, prefix="n08b-decoy-currency", currency=""),
        _product(0, prefix="n08b-decoy-nulltax", tax_rate=None),
    ]
    rows, controls = [], []
    metadata = {"axis": "order_form_options", "planned_measured_gets": 96,
                "planned_negative_gets": 4, "planned_posts": 0, "planned_total_calls": 100,
                "listing_cohorts": [0, 1, 10, 100], "product_cohorts": [0, 1, 10, 100],
                "own_history_count": 0, "directory_calls": 1, "populate_calls": 1,
                "shared_synthetic_photo_fixture": True,
                "setup": "bulk cohort options after native seed; GET filters only, no native purchase/publication100 claim",
                "product_decoys": 6, "listing_decoys": {"foreign": 1, "paused_managed": 1, "erased_managed": 1},
                "get_only_product": "autobump without frequency remains offered by native GET but is not purchase-ready",
                "snapshot_scope": "all scalar columns of all9 commercial models; digest only"}
    with _report(record_property, rows, controls, metadata):
        for count in [0, 1, 10, 100]:
            Listing.objects.filter(pk__in=[row.pk for row in managed]).update(status="paused")
            Listing.objects.filter(pk__in=[row.pk for row in managed[:count]]).update(status="published")
            for language in ["es", "en"]:
                translation.activate(language)

                def check_listings(response, body):
                    _page(response, [], 0, 25, 1)
                    _options(response, body, managed[:count], versions[:1], language)
                    assert str(foreign.pk).encode() not in body

                _segment(client, reverse("promotion_orders"), rows, route="promotion_orders",
                         language=language, axis="listing_options", cohort=count, page=1, check=check_listings)
        Listing.objects.filter(pk__in=[row.pk for row in managed]).update(status="paused")
        Listing.objects.filter(pk=managed[0].pk).update(status="published")
        for count in [0, 1, 10, 100]:
            PromotionProduct.objects.filter(pk__in=[row.pk for row in products]).update(active=False)
            PromotionProduct.objects.filter(pk__in=[row.pk for row in products[:count]]).update(active=True)
            for language in ["es", "en"]:
                translation.activate(language)

                def check_products(response, body):
                    _page(response, [], 0, 25, 1)
                    _options(response, body, managed[:1], versions[:count], language)
                    offered = _FormHTML(body).selects["product"]
                    assert all(str(row.pk) not in offered for row in decoys)

                _segment(client, reverse("promotion_orders"), rows, route="promotion_orders",
                         language=language, axis="product_options", cohort=count, page=1, check=check_products)
        assert not versions[-1].configuration_ready and not versions[-1].sellable
        for language in ["es", "en"]:
            translation.activate(language)
            _negative(Client(), reverse("promotion_orders"), controls, language=language,
                      state="anonymous_options", status=302, redirect="login")
            _stale_mfa(user, client, reverse("promotion_orders"), controls, language)
        assert not PromotionOrder.objects.exists() and not PromotionPaymentAttempt.objects.exists()
        assert not PromotionOrderAudit.objects.exists()
        _no_grants()
        assert len(rows) == 96 and len(controls) == 4
        metadata["readonly_segments_verified"] = True


def _drafts(products, start=1, end=1):
    return PromotionProductVersion.objects.bulk_create([
        PromotionProductVersion(product=product, version=number, name_es=f"Versión sintética {number:03d}",
                                name_en=f"Synthetic version {number:03d}", duration_days=10,
                                amount=None, currency="", tax_rate=None)
        for product in products for number in range(start, end + 1)
    ])


def _catalogue_journey(client, actor, controls, language):
    """Five distinct native POSTs; replay must preserve the four audit events and ledger absence."""
    slug = f"n08b-native-{language}"
    root = reverse("promotion_products")

    def post(path, payload, operation):
        response, _ = _request(client, path, controls, method="POST", payload=payload,
                               language=language, state=operation, kind="individual_native_post", ordinal=0)
        assert response.status_code == 302
        assert response["Cache-Control"] == "private, no-store"
        assert response.wsgi_request.LANGUAGE_CODE == response["Content-Language"] == language
        return response

    response = post(root, {"slug": slug, "kind": "top"}, "create_product")
    product = PromotionProduct.objects.get(slug=slug)
    first = product.versions.get(version=1)
    assert response.url == reverse("promotion_version_edit", args=[product.pk, 1])
    assert first.amount is None and first.published_at is None and not first.sellable
    post(reverse("promotion_product_versions", args=[product.pk]), {}, "create_version")
    row = product.versions.get(version=2)
    assert row.amount is None and row.edit_version == 1 and row.published_at is None
    edit = reverse("promotion_version_edit", args=[product.pk, 2])
    preview = reverse("promotion_version_preview", args=[product.pk, 2])
    response = post(edit, {"edit_version": 1, "name_es": f"Recorrido sintético {language}",
                           "name_en": f"Synthetic journey {language}", "duration_days": 10,
                           "amount": "", "currency": "", "tax_rate": "",
                           "bump_interval_minutes": "", "daily_bump_limit": ""}, "update_version")
    assert response.url == preview
    row.refresh_from_db()
    assert row.amount is None and row.tax_rate is None and row.edit_version == 2
    assert row.name_es == f"Recorrido sintético {language}" and row.name_en == f"Synthetic journey {language}"
    post(preview, {"edit_version": row.edit_version}, "publish_version")
    row.refresh_from_db()
    assert row.is_current and row.published_at and not row.configuration_ready and not row.sellable
    released = list(PromotionProductVersion.objects.filter(pk=row.pk).values())
    audits = list(PromotionCatalogueAudit.objects.filter(product_version__product=product).order_by("pk"))
    assert [event.operation for event in audits] == ["create_product", "create_version", "update_version", "publish_version"]
    assert [event.product_version_id for event in audits] == [first.pk, row.pk, row.pk, row.pk]
    assert [event.edit_version for event in audits] == [1, 1, 2, 2]
    assert all(event.actor_id == actor.pk and len(event.payload_digest) == 64 for event in audits)
    audit_snapshot = list(PromotionCatalogueAudit.objects.filter(product_version__product=product).order_by("pk").values())
    post(preview, {"edit_version": row.edit_version}, "publish_replay")
    assert list(PromotionProductVersion.objects.filter(pk=row.pk).values()) == released
    assert list(PromotionCatalogueAudit.objects.filter(product_version__product=product).order_by("pk").values()) == audit_snapshot
    assert product.versions.count() == 2 and product.versions.filter(is_current=True).count() == 1
    assert not PromotionOrder.objects.exists() and not PromotionPaymentAttempt.objects.exists()
    assert not PromotionOrderAudit.objects.exists()
    _no_grants()


def test_commercial_catalogue_versions_edit_preview_reference(request, settings, record_property):
    _guard(request, settings)
    request.getfixturevalue("directory")
    actor, client = _client("fixture-v1-moderator", catalogue_permission=True)
    _, unprivileged = _client("fixture-v1-visitor")
    assert not PromotionProduct.objects.exists()
    products, drafts, rows, controls = [], [], [], []
    metadata = {"axis": "catalogue_versions_edit_preview", "planned_measured_gets": 180,
                "planned_negative_gets": 18, "planned_posts": 10, "planned_total_calls": 208,
                "catalogue_cohorts": [0, 1, 10, 51, 100], "version_cohorts": [1, 10, 51, 100],
                "native_page_size": 50, "directory_calls": 1, "populate_calls": 0,
                "setup": "bulk synthetic draft catalogue cohorts; incomplete numeric fields stay NULL",
                "native_journey_posts_per_language": 5, "native_journey_audits_per_language": 4,
                "snapshot_scope": "all scalar columns of all9 commercial models; digest only"}
    with _report(record_property, rows, controls, metadata):
        for count in [0, 1, 10, 51, 100]:
            added = PromotionProduct.objects.bulk_create([
                PromotionProduct(slug=f"n08b-catalogue-{index:03d}", kind="top")
                for index in range(len(products), count)
            ])
            products.extend(added)
            drafts.extend(_drafts(added))
            for language in ["es", "en"]:
                translation.activate(language)
                links = {product.pk: f'href="{reverse("promotion_product_versions", args=[product.pk])}"'.encode()
                         for product in products}
                for number in range(1, max(1, ceil(count / 50)) + 1):
                    expected = products[(number - 1) * 50:number * 50]
                    expected_ids = {product.pk for product in expected}

                    def check_catalogue(response, body):
                        _page(response, expected, count, 50, number)
                        for identifier, link in links.items():
                            assert (link in body) == (identifier in expected_ids)
                        warning = ("Sales are inactive." if language == "en" else "Ventas inactivas.")
                        assert warning.encode() in body

                    _segment(client, reverse("promotion_products") + f"?page={number}", rows,
                             route="promotion_products", language=language, axis="catalogue", cohort=count,
                             page=number, check=check_catalogue)
        product = products[0]
        own_versions = [drafts[0]]
        for count in [1, 10, 51, 100]:
            own_versions.extend(_drafts([product], len(own_versions) + 1, count))
            ordered = sorted(own_versions, key=lambda row: (row.version, row.pk), reverse=True)
            for language in ["es", "en"]:
                translation.activate(language)
                preview_links = {row.pk: f'href="{reverse("promotion_version_preview", args=[product.pk, row.version])}"'.encode()
                                 for row in own_versions}
                edit_links = {row.pk: f'href="{reverse("promotion_version_edit", args=[product.pk, row.version])}"'.encode()
                              for row in own_versions}
                for number in range(1, ceil(count / 50) + 1):
                    expected = ordered[(number - 1) * 50:number * 50]
                    expected_ids = {row.pk for row in expected}

                    def check_versions(response, body):
                        shown = _page(response, expected, count, 50, number)
                        assert response.context["product"].pk == product.pk
                        assert all(row.product_id == product.pk and row.amount is None
                                   and row.published_at is None and not row.sellable for row in shown)
                        for identifier in preview_links:
                            assert (preview_links[identifier] in body) == (identifier in expected_ids)
                            assert (edit_links[identifier] in body) == (identifier in expected_ids)

                    _segment(client, reverse("promotion_product_versions", args=[product.pk]) + f"?page={number}", rows,
                             route="promotion_product_versions", language=language, axis="versions", cohort=count,
                             page=number, check=check_versions)
        selected = own_versions[-1]
        for language in ["es", "en"]:
            translation.activate(language)
            for route in ["promotion_version_edit", "promotion_version_preview"]:
                path = reverse(route, args=[product.pk, selected.version])

                def check_draft(response, body):
                    row = response.context["row"]
                    assert row.pk == selected.pk and row.product_id == product.pk and row.version == 100
                    assert row.amount is None and row.tax_rate is None and row.currency == ""
                    assert row.published_at is None and not row.is_current and not row.configuration_ready and not row.sellable
                    if route == "promotion_version_edit":
                        rendered = _FormHTML(body)
                        assert rendered.inputs["amount"] == "" and rendered.inputs["tax_rate"] == ""
                        assert rendered.inputs["name_es"] == row.name_es and rendered.inputs["name_en"] == row.name_en
                        label = "Amount before tax" if language == "en" else "Importe sin impuestos"
                        assert label.encode() in body
                    else:
                        name = row.name_en if language == "en" else row.name_es
                        assert f"<h1>{name}</h1>".encode() in body and b"0.00" not in body
                        warning = ("Configuration pending. Sales inactive." if language == "en"
                                   else "Pendiente de configurar. Ventas inactivas.")
                        assert warning.encode() in body

                _segment(client, path, rows, route=route, language=language, axis=route,
                         cohort=100, page=0, check=check_draft)
            paths = [reverse("promotion_products"), reverse("promotion_product_versions", args=[product.pk]),
                     reverse("promotion_version_edit", args=[product.pk, selected.version]),
                     reverse("promotion_version_preview", args=[product.pk, selected.version])]
            for path in paths:
                _negative(Client(), path, controls, language=language, state="anonymous_catalogue",
                          status=302, redirect="login")
                _negative(unprivileged, path, controls, language=language, state="unprivileged_catalogue",
                          status=403, forbidden=[product.slug])
        for language in ["es", "en"]:
            translation.activate(language)
            _catalogue_journey(client, actor, controls, language)
        actor.user_permissions.clear()
        for language in ["es", "en"]:
            translation.activate(language)
            _negative(client, reverse("promotion_products"), controls, language=language,
                      state="catalogue_permission_revoked", status=403, forbidden=[product.slug])
        assert len(rows) == 180
        assert sum(row["method"] == "GET" for row in controls) == 18
        assert sum(row["method"] == "POST" for row in controls) == 10
        assert len(controls) == 28 and PromotionCatalogueAudit.objects.count() == 8
        metadata["readonly_segments_verified"] = True
