"""Full native closed flow with1500 synthetic retained revisions and real WebP."""

import hashlib
import io
import json
import os
import threading
import time
import zipfile
from functools import partial
from pathlib import Path
from uuid import uuid4

import pytest
import test_rights_portability_covered_export_races as coverage_fixture
import test_rights_portability_export_races as selection_fixture
import test_rights_portability_response_races as response_fixture
from django.db import connection
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_portability_response_draft import REASON

from apps.listings.models import Revision
from apps.safety import rights_portability_coverage_batch as coverage_batch
from apps.safety.models import RightsNotice, RightsPortabilityClosure, RightsResponse
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_response_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def test_large_history_native_approval_closure_and_binary_delivery(
    request,
    settings,
    monkeypatch,
    tmp_path,
    record_property,
):
    request.getfixturevalue("directory")
    original_ready = selection_fixture.ready
    description = ("Synthetic retained large source. " * 200)[:6000]
    count = 1500

    def ready(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        person = result[-1]
        Revision.objects.bulk_create(
            [
                Revision(
                    listing=person.listing,
                    manager_version=person.manager_version,
                    title=f"Synthetic retained history {index}",
                    description=description,
                )
                for index in range(count)
            ],
            batch_size=100,
        )
        return result

    monkeypatch.setattr(selection_fixture, "ready", ready)
    progress = tmp_path / "native-closed-flow-progress.json"
    stages = {}
    state = {"active": None, "terminal": False, "success": False}
    stop = threading.Event()
    page_size = os.sysconf("SC_PAGE_SIZE")

    def rss():
        return int(Path("/proc/self/statm").read_text().split()[1]) * page_size

    def sample():
        while not stop.wait(0.05):
            active = state["active"]
            if active in stages:
                stages[active]["sampled_process_rss_peak_bytes"] = max(
                    stages[active]["sampled_process_rss_peak_bytes"],
                    rss(),
                )

    def save_progress():
        progress.write_text(json.dumps({"state": state, "stages": stages}))
        progress.chmod(0o600)

    def measured(name, function):
        def run(*args, **kwargs):
            item = stages.setdefault(
                name,
                {
                    "calls": 0,
                    "sql_queries": 0,
                    "seconds_total_instrumented": 0.0,
                    "seconds_max_instrumented": 0.0,
                    "sampled_process_rss_peak_bytes": rss(),
                },
            )
            state["active"] = name
            if item["calls"] % 25 == 0:
                save_progress()
            started = time.perf_counter()

            def counter(execute, sql, params, many, context):
                item["sql_queries"] += 1
                return execute(sql, params, many, context)

            try:
                with connection.execute_wrapper(counter):
                    return function(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - started
                item["calls"] += 1
                item["seconds_total_instrumented"] += elapsed
                item["seconds_max_instrumented"] = max(item["seconds_max_instrumented"], elapsed)
                item["sampled_process_rss_peak_bytes"] = max(
                    item["sampled_process_rss_peak_bytes"], rss()
                )
                state["active"] = None
                if item["calls"] % 25 == 0 or name != "coverage_page_intake":
                    save_progress()

        return run

    for module, field, label in [
        (coverage_fixture, "prepared_covered_selection", "selection_preparation"),
        (coverage_fixture, "save_coverage", "coverage_preparation"),
        (coverage_fixture, "inspect_page", "coverage_page_intake"),
        (coverage_fixture, "record", "coverage_approval"),
        (response_fixture, "generate", "covered_generation"),
        (response_fixture, "prepare", "final_draft_preparation"),
        (response_fixture, "inspect", "final_draft_inspection"),
    ]:
        monkeypatch.setattr(module, field, measured(label, getattr(module, field)))
    # The UI already uses the native four-page batch service. Keep all1511 page
    # inspections and their measurements, without rebuilding the source per page.
    monkeypatch.setattr(coverage_batch, "inspect_page", coverage_fixture.inspect_page)
    monkeypatch.setattr(
        response_fixture, "approved_coverage",
        partial(coverage_fixture.approved_coverage, batched=True),
    )
    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    try:
        case, author, reviewer, _, _, draft, read_action, receipt = (
            response_fixture.ready_final_draft(
                request,
                settings,
                monkeypatch,
                with_receipt=True,
                account_only=False,
                binary=True,
            )
        )
        assert stages["coverage_page_intake"]["calls"] >= count
        assert case.person.listing.revisions.count() >= count
        decision = measured("final_approval", record)(
            reviewer,
            case.pk,
            case.version,
            draft.pk,
            read_action.pk,
            uuid4(),
            REASON,
            "approved",
        )
        version, response_version, key = case.version, case.response_version, uuid4()
        response = measured("closure", close)(
            author,
            case.pk,
            version,
            response_version,
            decision.pk,
            key,
            REASON,
        )
        replay = measured("closure_replay", close)(
            author,
            case.pk,
            version,
            response_version,
            decision.pk,
            key,
            REASON,
        )
        assert replay.pk == response.pk
        case.refresh_from_db()
        assert case.status == "resolved"
        assert case.version == version + 1 and case.response_version == response_version + 1
        assert RightsResponse.objects.filter(request=case).count() == 1
        assert RightsPortabilityClosure.objects.filter(action__request=case).count() == 1
        assert RightsNotice.objects.filter(response=response).count() == 1
        export, client = draft.export, Client()
        manifest = measured("manifest_download", client.post)(
            url(receipt, export), {"key": uuid4()}
        )
        assert manifest.status_code == 200 and "no-store" in manifest["Cache-Control"]
        image = export.images.get()
        part = export.parts.exclude(attachments=[]).get()
        binary = measured("image_download", client.post)(
            url(receipt, export) + f"image/{image.pk}/",
            {"key": uuid4()},
        )
        assert binary.status_code == 200
        assert hashlib.sha256(binary.content).hexdigest() == manifest.json()["images"][0]["sha256"]
        package = measured("zip_download", client.post)(
            url(receipt, export) + f"part/{part.pk}/",
            {"key": uuid4()},
        )
        assert package.status_code == 200
        with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
            assert archive.namelist() == [str(image.pk) + ".webp"]
            assert archive.read(archive.namelist()[0]) == binary.content
        state["success"] = True
    finally:
        stop.set()
        sampler.join(timeout=2)
        state["terminal"] = True
        save_progress()
        record_property("historical_revisions", count)
        record_property("stages", json.dumps(stages))
        record_property("private_progress", str(progress))
        record_property("success", state["success"])
        record_property(
            "scope",
            "Native services/PG and full page intake; synthetic identity/provenance/exclusions, no provider/legal attestation. History mostly excluded from delivered fields; not8MiB binary or selected-history transport acceptance.",
        )
