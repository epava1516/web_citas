"""Native closure and multipart JSON transport with selected synthetic Unicode history."""

import hashlib
import http.cookiejar
import io
import json
import os
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from uuid import uuid4

import pytest
import test_rights_portability_coverage_use as coverage_use_fixture
import test_rights_portability_export_races as selection_fixture
import test_rights_portability_response_races as response_fixture
from django.core.files.base import ContentFile
from django.db import connection, transaction
from django.db.backends.utils import CursorWrapper
from PIL import Image
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_portability_response_draft import REASON

from apps.core.models import User
from apps.listings.models import Revision
from apps.mediafiles.models import Blob
from apps.safety.crypto import unseal
from apps.safety.models import RightsNotice, RightsPortabilityClosure, RightsResponse
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_response_review import record
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_review import record as selection_review
from apps.safety.rights_portability_selection_store import save_selection
from scripts.reconstruct_rights_copy import reconstruct

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("large", [False, True], ids=["functional", "measured"])
def test_native_closed_selected_json_over_local_tcp(
    request, settings, monkeypatch, live_server, tmp_path, record_property, large
):
    assert connection.vendor == "postgresql"
    original_ready = selection_fixture.ready
    original_selection = coverage_use_fixture.prepared_selection
    history_count = 360 if large else 2
    description = "🧪" * 6000
    assert len(description) == 6000 and len(description.encode()) == 24000
    expected = {}
    stages = {}
    state = {"active": None}
    stop = threading.Event()
    page_bytes = os.sysconf("SC_PAGE_SIZE")

    def rss():
        return int(Path("/proc/self/statm").read_text().split()[1]) * page_bytes

    def sample():
        while not stop.wait(0.05):
            active = state["active"]
            if active in stages:
                stages[active]["sampled_process_rss_peak_bytes"] = max(
                    stages[active]["sampled_process_rss_peak_bytes"], rss()
                )

    def measured(name, function):
        def call(*args, **kwargs):
            if not large:
                return function(*args, **kwargs)
            item = stages.setdefault(name, {"sql_queries": 0, "seconds": 0.0, "sampled_process_rss_peak_bytes": rss()})
            state["active"] = name
            started = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                item["seconds"] += time.perf_counter() - started
                item["sampled_process_rss_peak_bytes"] = max(item["sampled_process_rss_peak_bytes"], rss())
                state["active"] = None
        return call

    if large:
        for method in ("execute", "executemany"):
            original = getattr(CursorWrapper, method)

            def counted(cursor, *args, _original=original, **kwargs):
                active = state["active"]
                if active in stages:
                    stages[active]["sql_queries"] += 1
                return _original(cursor, *args, **kwargs)

            monkeypatch.setattr(CursorWrapper, method, counted)
        for field, label in [
            ("approved_coverage", "selection_coverage_native_intake_and_approval"),
            ("generate", "generation"),
            ("prepare", "final_draft_preparation"),
            ("inspect", "final_draft_inspection"),
        ]:
            monkeypatch.setattr(response_fixture, field, measured(label, getattr(response_fixture, field)))

    def ready_with_binary(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        person = result[-1]
        photo = person.listing.revisions.first().photos.order_by("position", "pk").first()
        Revision.objects.bulk_create([
            Revision(listing=person.listing, manager_version=person.manager_version,
                     title=f"Synthetic selected Unicode history {index}", description=description)
            for index in range(history_count)
        ], batch_size=100)
        width, height = (64, 64)
        bitmap = Image.frombytes("RGB", (width, height), random.Random(4242).randbytes(width * height * 3))
        output = io.BytesIO()
        bitmap.save(output, format="WEBP", lossless=True, method=0)
        content = output.getvalue()
        assert len(content) <= 10 * 1024 * 1024
        assert len(content) < 8 * 1024 * 1024
        digest = hashlib.sha256(content).hexdigest()
        blob = Blob.objects.create(sha256=digest, status="ready", width=width, height=height)
        blob.derivative.save("synthetic-closed-transport.webp", ContentFile(content))
        photo.blob = blob
        photo.save(update_fields=["blob"])
        expected.update(sha256=digest, bytes=len(content), photo=str(photo.pk))
        return result

    def selection_with_history(*args, **kwargs):
        case, author, baseline, previous, profile, subject, receipt = original_selection(*args, **kwargs)
        with transaction.atomic():
            locked, person, listing = reviewer_case(author, case.pk)
            source = source_copy(person, listing, locked)
        body = unseal(baseline.encrypted_selection)
        chosen = [
            {"row": row_reference("revisions", index, revision), "fields": ["/description"]}
            for index, revision in enumerate(source["revisions"])
            if revision["description"] == description
        ]
        assert len(chosen) == history_count
        body["selection"]["revisions"] = chosen
        selected = save_selection(author, case.pk, case.version, baseline.assessment_review_id,
                                  uuid4(), baseline.version, REASON, body["selection"],
                                  field_evidence=body["field_evidence"])
        reviewer = User.objects.get(pk=previous.action.actor_id)
        _, projection = selection_review(reviewer, case.pk, case.version, selected.pk, uuid4(), REASON)
        decision, _ = selection_review(reviewer, case.pk, case.version, selected.pk,
                                                uuid4(), REASON, "review", "approved")
        assert projection["datasets"]["revisions"] == [
            {"fields": {"/description": description}} for _ in range(history_count)
        ]
        return case, author, selected, decision, profile, subject, receipt

    monkeypatch.setattr(coverage_use_fixture, "prepared_selection", selection_with_history)

    monkeypatch.setattr(selection_fixture, "ready", ready_with_binary)
    sampler = threading.Thread(target=sample, daemon=True)
    if large:
        sampler.start()
    success = False
    try:
        case, author, reviewer, _, _, draft, read_action, receipt = response_fixture.ready_final_draft(
            request, settings, monkeypatch, with_receipt=True, account_only=False, binary=True
        )
        decision = measured("final_approval", record)(reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, "approved")
        version, responses, key = case.version, case.response_version, uuid4()
        response = measured("closure", close)(author, case.pk, version, responses, decision.pk, key, REASON)
        assert measured("closure_replay", close)(author, case.pk, version, responses, decision.pk, key, REASON).pk == response.pk
        case.refresh_from_db()
        assert case.status == "resolved" and (case.version, case.response_version) == (version + 1, responses + 1)
        assert RightsResponse.objects.filter(request=case).count() == RightsPortabilityClosure.objects.filter(action__request=case).count() == 1
        assert RightsNotice.objects.filter(response=response).count() == 1

        cookies = http.cookiejar.CookieJar()
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
        with client.open(live_server.url + receipt, timeout=30) as page:
            assert page.status == 200 and "no-store" in page.headers["Cache-Control"]
        csrf = next(cookie.value for cookie in cookies if cookie.name == settings.CSRF_COOKIE_NAME)

        def post(path, *, token=True):
            payload = urllib.parse.urlencode({"key": str(uuid4())}).encode()
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Referer": live_server.url + receipt}
            if token:
                headers["X-CSRFToken"] = csrf
            query = urllib.request.Request(live_server.url + path, data=payload, headers=headers)
            try:
                with client.open(query, timeout=120) as result:
                    return result.status, dict(result.headers), result.read()
            except urllib.error.HTTPError as error:
                return error.code, dict(error.headers), error.read()

        endpoint = url(receipt, draft.export)
        assert post(endpoint, token=False)[0] == 403
        status, headers, manifest_bytes = measured("manifest_tcp_download", post)(endpoint)
        assert status == 200 and "no-store" in headers["Cache-Control"]
        manifest = json.loads(manifest_bytes)
        image = draft.export.images.get()
        assert str(image.photo_id) == expected["photo"]
        if not large:
            assert manifest["images"][0]["sha256"] == expected["sha256"]
        if large:
            assert manifest["schema"] == "rights-data-manifest-v1"
            assert manifest["size"] > 8 * 1024 * 1024 and len(manifest["data_parts"]) >= 2
            manifest_path = tmp_path / "manifest.json"
            manifest_path.write_bytes(manifest_bytes)
            for fragment in manifest["data_parts"]:
                status, part_headers, part_bytes = measured("json_parts_tcp_download", post)(
                    endpoint + f"part/{fragment['id']}/"
                )
                assert status == 200 and "no-store" in part_headers["Cache-Control"]
                assert len(part_bytes) <= 8 * 1024 * 1024
                (tmp_path / f"rights-data-part-{fragment['position']}.zip").write_bytes(part_bytes)
            output_path = tmp_path / "reconstructed.json"
            assert measured("json_reconstruction", reconstruct)(manifest_path, tmp_path, output_path) == manifest["size"]
            delivered = json.loads(output_path.read_bytes())
            assert delivered["images"][0]["sha256"] == expected["sha256"]
            record_property("selected_json_bytes", manifest["size"])
            record_property("selected_json_sha256", manifest["sha256"])
            record_property("json_parts", len(manifest["data_parts"]))
        else:
            delivered = manifest
            assert len(manifest_bytes) < 8 * 1024 * 1024
        assert delivered["datasets"]["revisions"] == [
            {"fields": {"/description": description}} for _ in range(history_count)
        ]
        assert "field_evidence" not in delivered
        record_property("selected_revisions", history_count)

        image_url = endpoint + f"image/{image.pk}/"
        status, headers, binary = measured("webp_tcp_download", post)(image_url)
        assert status == 200 and headers["Content-Type"] == "image/webp" and "no-store" in headers["Cache-Control"]
        assert len(binary) == expected["bytes"] and hashlib.sha256(binary).hexdigest() == expected["sha256"]
        part = draft.export.parts.exclude(attachments=[]).get()
        status, headers, package = measured("zip_tcp_download", post)(endpoint + f"part/{part.pk}/")
        assert status == 200 and "no-store" in headers["Cache-Control"] and len(package) <= 64 * 1024 * 1024
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            assert archive.namelist() == [str(image.pk) + ".webp"]
            assert archive.read(archive.namelist()[0]) == binary
        assert post(endpoint)[2] == manifest_bytes
        original_epoch = author.session_version
        User.objects.filter(pk=author.pk).update(session_version=original_epoch + 1)
        assert post(image_url)[0] == 404
        assert post(endpoint)[0] == 404
        if large:
            assert post(endpoint + f"part/{manifest['data_parts'][0]['id']}/")[0] == 404
        User.objects.filter(pk=author.pk).update(session_version=original_epoch)
        assert post(image_url)[2] == binary
        wrong_receipt = receipt.rsplit("/", 2)[0] + "/" + "x" * 43 + "/"
        assert post(wrong_receipt + f"export/{draft.export.pk}/")[0] == 404
        success = True
    finally:
        stop.set()
        if large:
            sampler.join(timeout=2)
        record_property("source_binary_bytes", expected.get("bytes", 0))
        record_property("source_binary_sha256", expected.get("sha256", ""))
        record_property("measurement_enabled", large)
        record_property("stages", json.dumps(stages))
        record_property("success", success)
        record_property("scope", "Real PostgreSQL/native approvals and local TCP HTTP. Synthetic eligibility/identity; Selected Unicode revision descriptions; large multipart JSON reconstructed exactly, small WebP/ZIP. RSS includes pytest fixture and local client/server in same process, sampled50ms; no Gunicorn/Caddy/p95/capacity claimed.")
