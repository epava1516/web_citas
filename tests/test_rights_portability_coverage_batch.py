"""Atomic individually audited batches against real PostgreSQL and Chromium."""

import shutil
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from django.conf import settings as django_settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connections
from playwright.sync_api import sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_coverage_review_http import login
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.listings.models import Revision
from apps.mediafiles.models import Photo
from apps.safety import rights_portability_coverage_batch as batch
from apps.safety import rights_portability_coverage_inspection as inspection
from apps.safety.models import (
    RightsAction,
    RightsPortabilityCoverageRead,
    RightsPortabilityCoverageReview,
)
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_portability_coverage_store import save_coverage

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Inspect synthetic coverage in an individually audited batch"


def prepared(request, settings, monkeypatch):
    original = fixtures.ready

    def multi_revision(*args, **kwargs):
        result = original(*args, **kwargs)
        person = result[-1]
        original_revision = Revision.objects.filter(listing__person=person).first()
        photos = list(Photo.objects.filter(revision=original_revision))
        for _ in range(2):
            original_revision.pk = uuid4()
            original_revision._state.adding = True
            original_revision.save(force_insert=True)
            for original_photo in photos:
                photo = copy(original_photo)
                photo.pk = uuid4()
                photo.revision = original_revision
                photo._state.adding = True
                photo.save(force_insert=True)
        return result

    monkeypatch.setattr(fixtures, "ready", multi_revision)
    case, author, _, selected, _, _, _ = prepared_selection(request, settings, monkeypatch, False)
    coverage = save_coverage(
        author,
        case.pk,
        case.version,
        selected.pk,
        uuid4(),
        0,
        REASON,
        {name: {} for name in SECTIONS},
        {},
        allow_partial=True,
    )
    reviewer = User.objects.get(pk=selected.action.actor_id)
    return case, author, coverage, reviewer


def test_batch_preserves_page_audits_and_idempotency(request, settings, monkeypatch):
    case, author, coverage, reviewer = prepared(request, settings, monkeypatch)
    calls = []
    original = inspection.compile_coverage

    def compiled(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(inspection, "compile_coverage", compiled)
    key = uuid4()
    args = reviewer, case.pk, case.version, coverage.pk, key, REASON, "revisions"
    pages = batch.inspect_batch(*args)
    assert 1 < len(pages) <= 4
    assert len(calls) == 1
    ids = [read.pk for read, page in pages]
    assert len(ids) == len(set(ids))
    assert all(len(page["fields"]) <= 50 for read, page in pages)
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == len(ids)
    assert [read.pk for read, page in batch.inspect_batch(*args)] == ids
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == len(ids)
    with pytest.raises(ValidationError, match="Conflicting"):
        batch.inspect_batch(*args, page_count=2)
    with pytest.raises(PermissionDenied):
        batch.inspect_batch(
            author, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions"
        )
    assert not RightsPortabilityCoverageReview.objects.filter(coverage=coverage).exists()


def test_batch_rolls_back_all_reads_if_a_later_page_fails(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    original = batch.inspect_page
    calls = []

    def fail_second(*args, **kwargs):
        calls.append(True)
        if len(calls) == 2:
            raise ValidationError("Synthetic later page failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(batch, "inspect_page", fail_second)
    key = uuid4()
    with pytest.raises(ValidationError, match="later page"):
        batch.inspect_batch(reviewer, case.pk, case.version, coverage.pk, key, REASON, "revisions")
    assert len(calls) == 2
    assert not RightsAction.objects.filter(key=key).exists()
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()


@pytest.mark.parametrize("count", [0, 5, True, "4"])
def test_batch_rejects_unbounded_count(count):
    with pytest.raises(ValidationError, match="one to four"):
        batch.inspect_batch(None, None, None, None, uuid4(), REASON, "revisions", page_count=count)


@pytest.mark.parametrize("language", ["es", "en"])
def test_private_http_batch_requires_post_and_renders_all_pages(
    request, settings, monkeypatch, language
):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    client = login(reviewer)
    url = f"/{language}/moderation/rights/{case.pk}/portability/coverage/{coverage.pk}/review/"
    response = client.get(url)
    assert response.status_code == 200 and not response.context["inspected_pages"]
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()
    data = {
        "operation": "inspect",
        "key": str(uuid4()),
        "version": case.version,
        "reason": REASON,
        "dataset": "revisions",
        "row_number": 1,
        "field_page": 1,
        "page_count": 4,
    }
    response = client.post(url, data)
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    pages = response.context["inspected_pages"]
    assert 1 < len(pages) <= 4
    assert response.content.count(b'data-coverage-page="') == len(pages)
    assert REASON.encode() not in client.get(url).content
    assert login(reviewer, csrf=True).post(url, data).status_code == 403


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_batch_displays_multiple_individual_pages(
    live_server, request, settings, monkeypatch, language
):
    settings.DEBUG = True
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    client = login(reviewer)
    cookie = client.cookies[django_settings.SESSION_COOKIE_NAME].value
    url = f"{live_server.url}/{language}/moderation/rights/{case.pk}/portability/coverage/{coverage.pk}/review/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": cookie,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(url)
            page.locator("#id_dataset").select_option("revisions")
            page.locator("#id_reason").fill(REASON)
            page.locator("#id_page_count").fill("4")
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.locator("form").first.locator('button[type="submit"]').click()
            assert response.value.status == 200
            assert 1 < page.locator("[data-coverage-page]").count() <= 4
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()


def test_revocation_before_batch_return_rolls_back_every_read(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    original = batch.inspect_page

    def revoke():
        try:
            User.objects.filter(pk=reviewer.pk).update(is_active=False)
        finally:
            connections.close_all()

    def inspected_then_revoked(*args, **kwargs):
        result = original(*args, **kwargs)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(revoke).result(timeout=10)
        return result

    monkeypatch.setattr(batch, "inspect_page", inspected_then_revoked)
    key = uuid4()
    with pytest.raises(PermissionDenied):
        batch.inspect_batch(
            reviewer, case.pk, case.version, coverage.pk, key, REASON, "revisions", page_count=1
        )
    assert not User.objects.get(pk=reviewer.pk).is_active
    assert not RightsAction.objects.filter(key=key).exists()
    assert not RightsPortabilityCoverageRead.objects.filter(coverage=coverage).exists()


def test_binary_batch_stops_after_last_image_page(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared(request, settings, monkeypatch)
    pages = batch.inspect_batch(
        reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions", binary=True
    )
    assert len(pages) == 1
    assert pages[0][1]["binary"]
    assert 1 < len(pages[0][1]["fields"]) <= 20
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage, binary=True).count() == 1
