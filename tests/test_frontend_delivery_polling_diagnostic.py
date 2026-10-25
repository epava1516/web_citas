"""Explicit mobile HTTP/browser references; synthetic fixtures, no app changes."""

import hashlib
import io
import json
import math
import os
import resource
import shutil
import time
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from PIL import Image
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_photos import raw_image
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability_jobs import REASON, enqueue, prepared
from test_rights_portability_response_draft import operator

from apps.listings.models import Listing, Revision
from apps.mediafiles.models import Photo
from apps.safety import rights_portability_jobs as jobs
from apps.safety.models import RightsExport, RightsExportDownload, RightsPortabilityExportJob

pytestmark = pytest.mark.django_db(transaction=True)
VIEWPORT = {"width": 390, "height": 844}
ASSETS = {"app.css": "css", "form-errors.js": "form_errors", "htmx.min.js": "htmx"}
TEXT = {
    "es": {"queued": "Esperando para generar la copia privada.",
           "running": "Validando y generando la copia privada.",
           "rejected": "La solicitud o la autorización cambió. Consulta el expediente vigente antes de intentarlo de nuevo."},
    "en": {"queued": "Waiting to generate the private copy.",
           "running": "Validating and generating the private copy.",
           "rejected": "The request or authorization changed. Inspect the current request before trying again."},
}


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def _guard(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit owned serial mobile browser diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert request.config.pluginmanager.hasplugin("scripts.local_ci_broker")
    generation = request.getfixturevalue("isolated_test_broker")
    assert generation == os.environ["LOCAL_CI_TEST_QUEUE_GENERATION"] == settings.TASK_QUEUE_GENERATION
    _owned_database()
    assert connection.vendor == "postgresql" and not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert settings.MEDIA_STORAGE_PROVIDER == "local" and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    settings.DEBUG = True  # Native live-server static assets, no route interception.


def _rss():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert rss < 1024 * 1024
    return rss


def _api(context, url, **kwargs):
    started = time.monotonic()
    response = context.request.get(url, **kwargs)
    body = response.body()
    elapsed = time.monotonic() - started
    assert math.isfinite(elapsed) and elapsed >= 0
    return response, body, {"wall_including_body_seconds": elapsed, "decoded_bytes": len(body),
                            "body_sha256": _sha(body), "status": response.status,
                            "cache_control": response.headers.get("cache-control"),
                            "nosniff": response.headers.get("x-content-type-options"),
                            "content_type": response.headers.get("content-type", "").split(";")[0]}


class BrowserLedger:
    """Observe finished real requests; retain only logical kinds, counts and hashes."""

    def __init__(self, page, *, poll_path=None, language=None, private=False):
        self.page, self.poll_path, self.language, self.private = page, poll_path, language, private
        self.rows, self.assets, self.errors, self.inflight = [], [], [], {}
        self.pending = []
        self.max_inflight = 0
        page.on("request", self.started)
        page.on("requestfinished", self.finished)
        page.on("requestfailed", self.failed)
        page.on("pageerror", self.page_error)

    def kind(self, request):
        path = urlsplit(request.url).path
        if self.poll_path and path == self.poll_path and request.resource_type == "xhr":
            assert request.method == "GET" and request.headers.get("hx-request", "").lower() == "true"
            return "poll"
        if self.private and "/photos/" in path and path.endswith("/private/"):
            return "private_image"
        return ASSETS.get(path.rsplit("/", 1)[-1])

    def started(self, request):
        try:
            kind = self.kind(request)
            if kind:
                self.inflight[request] = (kind, time.monotonic())
                self.max_inflight = max(self.max_inflight, sum(row[0] == "poll" for row in self.inflight.values()))
        except Exception as exc:
            self.errors.append({"stage": "request_classification", "type": type(exc).__name__})

    def finished(self, request):
        entry = self.inflight.pop(request, None)
        if entry is not None:
            # Record completed references/clocks quickly. Body reads happen only
            # in flush(), outside Playwright event callbacks.
            self.pending.append((request, entry, time.monotonic()))

    def flush(self):
        pending, self.pending = self.pending, []
        for request, (kind, started), completed in pending:
            step = "response"
            try:
                response = request.response()
                assert response is not None
                status = response.status
                # A static304 carries no new entity body. Preserve it as
                # revalidation, not an observer failure or zero-size asset.
                revalidated = status == 304 and kind in ASSETS.values()
                step = "body"
                body = b"" if revalidated else response.body()
                step = "timing"
                timing = {key: value for key, value in request.timing.items()
                          if isinstance(value, (int, float)) and math.isfinite(value)}
                row = {"kind": kind, "start_monotonic": started, "complete_monotonic": completed,
                       "wall_seconds": completed - started, "decoded_bytes": len(body),
                       "sha256": None if revalidated else _sha(body), "status": status, "browser_timing": timing,
                       "encoding": response.headers.get("content-encoding", "identity"),
                       "body_scope": "no_new_body_static_revalidation" if revalidated else "decoded_response_body",
                       "cache_control": response.headers.get("cache-control"),
                       "nosniff": response.headers.get("x-content-type-options")}
                step = "status_or_oracle"
                assert revalidated or (status == 200 and body)
                if kind == "poll":
                    states = [state for state, text in TEXT[self.language].items() if text.encode() in body]
                    assert len(states) == 1 and REASON.encode() not in body
                    assert "no-store" in response.headers.get("cache-control", "")
                    assert b"<html" not in body.lower()
                    row["state"] = states[0]
                    self.rows.append(row)
                elif kind == "private_image":
                    assert response.headers.get("content-type", "").startswith("image/webp")
                    assert response.headers.get("cache-control") == "private, no-store"
                    assert response.headers.get("x-content-type-options") == "nosniff"
                    self.rows.append(row)
                else:
                    self.assets.append(row)
            except Exception as exc:
                message = str(exc)
                category = ("body_resource_retired" if "No resource with given identifier" in message
                            or "No data found for resource" in message else
                            "target_closed" if "closed" in message.lower() else "other")
                self.errors.append({"stage": step, "kind": kind,
                                    "type": type(exc).__name__, "category": category})

    def failed(self, request):
        if self.inflight.pop(request, None) is not None:
            self.errors.append({"stage": "request_failed", "type": "ObservedRequestFailed"})

    def page_error(self, error):
        self.errors.append({"stage": "page_error", "type": type(error).__name__})

    def wait(self, predicate, timeout=12000):
        deadline = time.monotonic() + timeout / 1000
        while True:
            self.flush()
            assert not self.errors, "Browser observer reported an error taxonomy"
            if predicate() and not self.pending:
                break
            assert time.monotonic() < deadline, "Bounded real browser observation expired"
            self.page.wait_for_timeout(50)  # Pump real browser events; no timer/HTTP mock.
        assert not self.errors

    def detach(self):
        for event, callback in [("request", self.started), ("requestfinished", self.finished),
                                ("requestfailed", self.failed), ("pageerror", self.page_error)]:
            self.page.remove_listener(event, callback)


def _derivative(revision_id):
    photo = Photo.objects.select_related("blob").get(revision_id=revision_id, removed_at__isnull=True)
    with photo.blob.derivative.open("rb") as stream:
        body = stream.read()
    with photo.blob.original.open("rb") as stream:
        original = stream.read()
    with Image.open(io.BytesIO(body)) as image:
        image.load()
        assert image.format == "WEBP" and not image.getexif() and "exif" not in image.info
        shape = [image.width, image.height]
    assert photo.blob.status == "ready" and photo.comparison_complete and not photo.approved
    assert _sha(original) == photo.blob.sha256
    return {"body_sha256": _sha(body), "decoded_bytes": len(body), "size": shape,
            "format": "WEBP", "exif": False, "original_sha256": _sha(original)}, photo.pk


@pytest.mark.parametrize("language", ["es", "en"])
def test_private_photo_browser_delivery(request, settings, live_server, tmp_path, language, record_property):
    _guard(request, settings)
    user, person, _ = request.getfixturevalue("scenario")
    settings.MEDIA_ROOT = tmp_path / "private"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    revision = Revision.objects.create(listing=Listing.objects.create(person=person), manager_version=1)
    upload = tmp_path / "synthetic.jpg"
    original = raw_image(34)
    upload.write_bytes(original)
    browser = context = anonymous = ledger = None
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
                args=["--no-sandbox"])
            context = browser.new_context(viewport=VIEWPORT)
            page = context.new_page()
            ledger = BrowserLedger(page, private=True)
            page.goto(live_server.url + f"/{language}/account/login/", wait_until="networkidle")
            ledger.wait(lambda: not ledger.inflight)
            page.locator("[name=email]").fill(user.email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            with page.expect_navigation(wait_until="networkidle"):
                page.locator("button[type=submit]").click()
            ledger.wait(lambda: not ledger.inflight)
            page.goto(live_server.url + f"/{language}/draft/{revision.pk}/3/", wait_until="networkidle")
            ledger.wait(lambda: not ledger.inflight)
            page.locator("[name=image]").set_input_files(str(upload))
            upload_started = time.monotonic()
            page.get_by_role("button", name="Upload photo" if language == "en" else "Subir foto", exact=True).click()
            expect(page.locator("html")).to_have_attribute("lang", language)
            image = page.locator("img")
            expect(image).to_be_visible()
            ledger.wait(lambda: len(ledger.rows) >= 1 and image.evaluate("img => img.complete && img.naturalWidth > 0"))
            upload_to_preview_seconds = time.monotonic() - upload_started
            stored, photo_id = db_sync(lambda: _derivative(revision.pk))
            assert stored["original_sha256"] == _sha(original)
            private_path = f"/{language}/photos/{photo_id}/private/"
            assert urlsplit(image.get_attribute("src")).path == private_path
            assert image.evaluate("img => [img.naturalWidth, img.naturalHeight]") == stored["size"]
            first = ledger.rows[-1]
            assert first["sha256"] == stored["body_sha256"] and first["decoded_bytes"] == stored["decoded_bytes"]
            reload_started = time.monotonic()
            page.reload()
            expect(image).to_be_visible()
            ledger.wait(lambda: len(ledger.rows) >= 2 and image.evaluate("img => img.complete && img.naturalWidth > 0"))
            reload_to_preview_seconds = time.monotonic() - reload_started
            assert ledger.rows[-1]["sha256"] == stored["body_sha256"]
            samples = []
            for ordinal in range(6):
                response, body, sample = _api(context, live_server.url + private_path)
                assert response.status == 200 and _sha(body) == stored["body_sha256"]
                assert sample["decoded_bytes"] == stored["decoded_bytes"]
                assert sample["cache_control"] == "private, no-store" and sample["nosniff"] == "nosniff"
                assert sample["content_type"] == "image/webp" and _sha(body) != stored["original_sha256"]
                sample.update(ordinal=ordinal + 1, position="first_api" if ordinal == 0 else "later_api")
                samples.append(sample)
            condition = {"If-None-Match": '"' + stored["body_sha256"] + '"',
                         "If-Modified-Since": "Wed, 21 Oct 2099 07:28:00 GMT"}
            response, body, conditional = _api(context, live_server.url + private_path, headers=condition)
            assert response.status == 200 and _sha(body) == stored["body_sha256"]
            anonymous = browser.new_context(viewport=VIEWPORT)
            response, _, denied = _api(anonymous, live_server.url + private_path, max_redirects=0)
            assert response.status == 302 and not denied["content_type"].startswith("image/")
            # The actual authenticated response SHA differs from original bytes;
            # do not guess any private storage path.
            page.get_by_role("button", name="Remove photo" if language == "en" else "Eliminar foto").click()
            expect(page.locator("img")).to_have_count(0)
            response, _, removed = _api(context, live_server.url + private_path, headers=condition)
            assert response.status == 404 and not removed["content_type"].startswith("image/")
            assert db_sync(lambda: Photo.objects.filter(revision_id=revision.pk, removed_at__isnull=True).count()) == 0
            assert stored == db_sync(lambda: _retained_derivative(photo_id))
            ledger.wait(lambda: not ledger.inflight)
            assert {row["kind"] for row in ledger.assets if row["status"] == 200} >= {"css", "form_errors"}
            assert not ledger.errors
            report = {"version": "n05b-private-v1", "language": language, "viewport": VIEWPORT,
                      "browser": browser.version, "stored": stored, "browser_images": ledger.rows,
                      "upload_to_preview_seconds": upload_to_preview_seconds,
                      "reload_to_preview_seconds": reload_to_preview_seconds,
                      "api_samples": samples, "conditional_positive": conditional,
                      "anonymous_denied": denied, "after_remove": removed,
                      "assets": ledger.assets, "observer_errors": ledger.errors, "process_maxrss_kib": _rss(),
                      "limits": "Mobile real Chromium/native upload-preview-reload-remove. Eager local processing is fixture scope, no queue/worker/capacity credit. Six same authenticated context API GETs include body time, not OS cold. Decoded body bytes are not wire size; no LCP/p95/Internet/provider/quality-change claim. Native private endpoint/denial/hash checks only; no original file path or URLs in report."}
            record_property("n05b_private_delivery", json.dumps(report, sort_keys=True, allow_nan=False))
        finally:
            if ledger:
                ledger.detach()
            for child in [anonymous, context, browser]:
                if child:
                    child.close()


def _retained_derivative(photo_id):
    photo = Photo.objects.select_related("blob").get(pk=photo_id)
    assert photo.removed_at is not None
    # Snapshot the retained bytes without pretending removal purges its original.
    with photo.blob.derivative.open("rb") as stream:
        body = stream.read()
    with photo.blob.original.open("rb") as stream:
        original = stream.read()
    with Image.open(io.BytesIO(body)) as image:
        image.load()
        assert image.format == "WEBP" and not image.getexif() and "exif" not in image.info
        shape = [image.width, image.height]
    return {"body_sha256": _sha(body), "decoded_bytes": len(body), "size": shape,
            "format": "WEBP", "exif": False, "original_sha256": _sha(original)}


@pytest.mark.parametrize("language", ["es", "en"])
def test_natural_export_job_polling(request, settings, monkeypatch, live_server, language, record_property):
    _guard(request, settings)
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch)
    # Existing helper stubs jobs.dispatch only. The following is controlled
    # domain state preparation, never broker/worker or actual export generation.
    job = enqueue(case, author, row, decision)
    staff = operator(author)
    cookie = staff.cookies[settings.SESSION_COOKIE_NAME].value
    canonical_path = f"/{language}/moderation/rights/{case.pk}/portability/export/jobs/{job.pk}/"
    exports_before = RightsExport.objects.count()
    downloads_before = RightsExportDownload.objects.count()
    browser = context = fallback = ledger = no_js_ledger = None
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
                args=["--no-sandbox"])
            context = browser.new_context(viewport=VIEWPORT)
            auth = [{"name": settings.SESSION_COOKIE_NAME, "value": cookie, "url": live_server.url}]
            context.add_cookies(auth)
            page = context.new_page()
            ledger = BrowserLedger(page, poll_path=canonical_path, language=language)
            initial = page.goto(live_server.url + canonical_path)
            assert initial.status == 200 and "no-store" in initial.headers.get("cache-control", "")
            expect(page.locator("html")).to_have_attribute("lang", language)
            expect(page.get_by_role("status")).to_have_text(TEXT[language]["queued"])
            assert page.locator("#portability-job").get_attribute("hx-trigger") == "every 3s"
            assert page.locator("#portability-job").get_attribute("hx-get") == canonical_path
            ledger.wait(lambda: len([record for record in ledger.rows if record["state"] == "queued"]) >= 2)
            token = db_sync(lambda: jobs.claim(job.pk))
            assert token is not None
            expect(page.get_by_role("status")).to_have_text(TEXT[language]["running"], timeout=12000)
            ledger.wait(lambda: any(record["state"] == "running" for record in ledger.rows))
            db_sync(lambda: jobs.finish_attempt(job.pk, token, rejected=True))
            expect(page.get_by_role("alert")).to_have_text(TEXT[language]["rejected"], timeout=12000)
            ledger.wait(lambda: any(record["state"] == "rejected" for record in ledger.rows) and not ledger.inflight)
            assert page.locator("#portability-job").get_attribute("hx-get") is None
            before_quiet = len(ledger.rows)
            quiet_start = time.monotonic()
            page.wait_for_timeout(6500)
            quiet_seconds = time.monotonic() - quiet_start
            ledger.flush()
            assert quiet_seconds >= 6.5 and len(ledger.rows) == before_quiet and not ledger.inflight
            assert ledger.max_inflight == 1 and not ledger.errors
            starts = [record["start_monotonic"] for record in ledger.rows]
            intervals = [later - earlier for earlier, later in zip(starts, starts[1:])]
            assert all(math.isfinite(value) and value > 0 for value in intervals)
            assert REASON not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert {record["kind"] for record in ledger.assets if record["status"] == 200} >= {"css", "form_errors", "htmx"}
            fallback = browser.new_context(viewport=VIEWPORT, java_script_enabled=False)
            fallback.add_cookies(auth)
            no_js = fallback.new_page()
            no_js_ledger = BrowserLedger(no_js, poll_path=canonical_path, language=language)
            response = no_js.goto(live_server.url + canonical_path)
            assert response.status == 200 and "no-store" in response.headers.get("cache-control", "")
            expect(no_js.locator("html")).to_have_attribute("lang", language)
            expect(no_js.get_by_role("alert")).to_have_text(TEXT[language]["rejected"])
            assert no_js.locator("#portability-job").get_attribute("hx-get") is None
            no_js.wait_for_timeout(6500)
            no_js_ledger.flush()
            assert not no_js_ledger.rows and not no_js_ledger.inflight and not no_js_ledger.errors
            assert REASON not in no_js.content()
            state = db_sync(lambda: RightsPortabilityExportJob.objects.filter(pk=job.pk).values(
                "state", "attempts", "export_id", "encrypted_reason").get())
            assert state == {"state": "rejected", "attempts": 1, "export_id": None, "encrypted_reason": ""}
            assert db_sync(RightsExport.objects.count) == exports_before
            assert db_sync(RightsExportDownload.objects.count) == downloads_before
            report = {"version": "n05b-polling-v1", "language": language, "viewport": VIEWPORT,
                      "browser": browser.version, "requests": ledger.rows, "interval_seconds": intervals,
                      "max_inflight": ledger.max_inflight, "terminal_quiet_seconds": quiet_seconds,
                      "terminal_no_new_requests": True, "no_js_poll_count": len(no_js_ledger.rows),
                      "states": ["queued", "running", "rejected"], "assets": ledger.assets,
                      "observer_errors": ledger.errors + no_js_ledger.errors, "process_maxrss_kib": _rss(),
                      "limits": "Actual native HTMX every3s, mobile ES/EN canonical job, natural ticks and actual HTTP bodies. Only helper dispatch is stubbed; claim/finish_attempt domain transitions controlled by test, no worker/broker/automatic-revocation/export-generation credit. 6500ms terminal observation covers two declared periods; measured intervals not exact3.000s SLA or p95. Same canonical URL with JSdisabled validates terminal fallback. Bytes decoded, not wire; no raw URL/cookie/reason/subject data or body stored. Desktop/gallery/keyboard remain separate reused witnesses."}
            record_property("n05b_polling", json.dumps(report, sort_keys=True, allow_nan=False))
        finally:
            for observer in [no_js_ledger, ledger]:
                if observer:
                    observer.detach()
            for child in [fallback, context, browser]:
                if child:
                    child.close()
