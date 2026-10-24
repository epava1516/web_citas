"""Opt-in cost attribution of the current closed portability flow, synthetic only."""

import hashlib
import io
import re
import resource
import sys
import time
import zipfile
from collections import Counter
from functools import partial, wraps
from uuid import uuid4

import pytest
import test_rights_portability_covered_export_races as coverage_fixture
import test_rights_portability_export_races as selection_fixture
import test_rights_portability_response_races as response_fixture
from django.apps import apps as django_apps
from django.db import connection
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_portability_response_draft import REASON

from apps.listings.models import Revision
from apps.safety import crypto, fast_canonical, rights_exports
from apps.safety import rights_portability_coverage_batch as coverage_batch
from apps.safety.models import RightsNotice, RightsPortabilityClosure, RightsResponse
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_response_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [10, 100])
def test_native_closed_flow_cost(request, settings, monkeypatch, record_property, count):
    if not any(str(arg).split("::")[0] == "tests/test_export_flow_stage_cost.py" for arg in request.config.args):
        pytest.skip("Explicit current closed-flow attribution only")
    assert connection.vendor == "postgresql"
    request.getfixturevalue("directory")
    original_ready = selection_fixture.ready

    def ready(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        person = result[-1]
        Revision.objects.bulk_create([
            Revision(listing=person.listing, manager_version=person.manager_version,
                     title=f"Synthetic retained history {index}",
                     description=("Synthetic retained ordinary history. " * 160)[:5400])
            for index in range(count)
        ], batch_size=100)
        return result

    monkeypatch.setattr(selection_fixture, "ready", ready)
    stages, active = {}, []

    def measured(name, function):
        @wraps(function)
        def run(*args, **kwargs):
            item = stages.setdefault(name, dict(calls=0, wall_seconds=0.0,
                                               thread_cpu_seconds=0.0, sql_calls=0))
            started, cpu = time.perf_counter(), time.thread_time()
            active.append(name)
            try:
                return function(*args, **kwargs)
            finally:
                active.pop()
                item["calls"] += 1
                item["wall_seconds"] += time.perf_counter() - started
                item["thread_cpu_seconds"] += time.thread_time() - cpu
        return run

    # Replace references by identity, including already-imported aliases. Every
    # wrapper delegates to the original; no authority, crypto or outcome is faked.
    targets = [
        (rights_exports.source_copy, "source_copy"),
        (fast_canonical.canonical, "canonical"),
        (crypto.seal, "seal_json"), (crypto.unseal, "unseal_json"),
        (rights_exports._read_image_blob, "image_blob_read"),
    ]
    replacements = {function: measured(label, function) for function, label in targets}
    alias_counts = {label: 0 for _, label in targets}
    labels = {function: label for function, label in targets}
    for name, module in list(sys.modules.items()):
        if not name.startswith("apps.safety.") or module is None:
            continue
        for field, value in list(vars(module).items()):
            if callable(value) and any(value is function for function in replacements):
                monkeypatch.setattr(module, field, replacements[value])
                alias_counts[labels[value]] += 1

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
    monkeypatch.setattr(coverage_batch, "inspect_page", coverage_fixture.inspect_page)
    monkeypatch.setattr(response_fixture, "approved_coverage",
                        partial(coverage_fixture.approved_coverage, batched=True))
    sql_total = 0
    coverage_sql = Counter()
    known_tables = {model._meta.db_table for model in django_apps.get_models()}

    def count_sql(execute, sql, params, many, context):
        nonlocal sql_total
        sql_total += 1
        for label in set(active):
            stages[label]["sql_calls"] += 1
        if "coverage_page_intake" in active:
            operation = sql.lstrip().split(None, 1)[0].upper()
            if operation not in {"SELECT", "INSERT", "UPDATE", "DELETE", "SAVEPOINT", "RELEASE", "ROLLBACK", "BEGIN", "COMMIT"}:
                operation = "OTHER"
            tables = sorted(set(re.findall(r'"([a-z_][a-z0-9_]*)"', sql)) & known_tables)
            frame, caller = sys._getframe(1), "outside_safety_module"
            try:
                while frame is not None:
                    module_name = frame.f_globals.get("__name__", "")
                    if module_name.startswith("apps.safety."):
                        caller = module_name + "." + frame.f_code.co_name
                        break
                    frame = frame.f_back
            finally:
                del frame
            # Static model names and code location only; never SQL or parameters.
            coverage_sql[(operation, tuple(tables), caller)] += 1
        return execute(sql, params, many, context)

    started, cpu = time.perf_counter(), time.thread_time()
    with connection.execute_wrapper(count_sql):
        case, author, reviewer, _, _, draft, read_action, receipt = response_fixture.ready_final_draft(
            request, settings, monkeypatch, with_receipt=True, account_only=False, binary=True,
        )
        assert case.person.listing.revisions.count() >= count
        assert stages["coverage_page_intake"]["calls"] >= count
        decision = measured("final_approval", record)(
            reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, "approved",
        )
        version, response_version, key = case.version, case.response_version, uuid4()
        response = measured("closure", close)(
            author, case.pk, version, response_version, decision.pk, key, REASON,
        )
        replay = measured("closure_replay", close)(
            author, case.pk, version, response_version, decision.pk, key, REASON,
        )
        assert replay.pk == response.pk
        case.refresh_from_db()
        assert case.status == "resolved"
        assert case.version == version + 1 and case.response_version == response_version + 1
        assert RightsResponse.objects.filter(request=case).count() == 1
        assert RightsPortabilityClosure.objects.filter(action__request=case).count() == 1
        assert RightsNotice.objects.filter(response=response).count() == 1
        export, client = draft.export, Client()
        manifest = measured("manifest_download", client.post)(url(receipt, export), {"key": uuid4()})
        assert manifest.status_code == 200 and "no-store" in manifest["Cache-Control"]
        image = export.images.get()
        part = export.parts.exclude(attachments=[]).get()
        binary = measured("image_download", client.post)(
            url(receipt, export) + f"image/{image.pk}/", {"key": uuid4()},
        )
        assert binary.status_code == 200 and "no-store" in binary["Cache-Control"]
        assert hashlib.sha256(binary.content).hexdigest() == manifest.json()["images"][0]["sha256"]
        package = measured("zip_download", client.post)(
            url(receipt, export) + f"part/{part.pk}/", {"key": uuid4()},
        )
        assert package.status_code == 200 and "no-store" in package["Cache-Control"]
        with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
            assert archive.namelist() == [str(image.pk) + ".webp"]
            assert archive.read(archive.namelist()[0]) == binary.content
    elapsed, cpu = time.perf_counter() - started, time.thread_time() - cpu
    assert all(stages[label]["calls"] > 0 for _, label in targets)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert rss < 1024 * 1024
    assert sum(coverage_sql.values()) == stages["coverage_page_intake"]["sql_calls"]
    record_property("closed_export_stage_diagnostic", dict(
        corpus_version="retained-history-closed-flow-v1", retained_revisions=count,
        stages=stages, observed_module_aliases=alias_counts, sql_calls=sql_total,
        coverage_sql_composition=[dict(operation=operation, tables=list(tables), caller=caller, count=value)
                                  for (operation, tables, caller), value in sorted(coverage_sql.items())],
        wall_seconds=elapsed, thread_cpu_seconds=cpu, process_maxrss_kib=rss,
        delivered_manifest_bytes=len(manifest.content), delivered_image_bytes=len(binary.content),
        delivered_zip_bytes=len(package.content),
        limits="Instrumented single flow per size, nested stages not additive; history mostly excluded from delivered fields; fixture simulated identity/provenance, not provider/legal attestation; not 1500 revisions/16MiB JSON/64MiB originals, concurrency, p95, capacity or MOD09 reassessment",
    ))
