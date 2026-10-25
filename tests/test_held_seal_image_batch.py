"""Real held-seal caller locks and paired guard cost; no MOD09 acceptance."""

import ast
import hashlib
import io
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import DatabaseError, connection, connections, transaction
from PIL import Image
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection
from test_rights_validation_seal import check, generated

from apps.core.models import Person
from apps.mediafiles.models import Blob, Photo
from apps.safety import rights_exports, rights_portability_export
from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsExportDownload
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_image_read import inspect
from apps.safety.rights_portability_image_selection import prepare, save
from apps.safety.rights_portability_selection_review import record

pytestmark = pytest.mark.django_db(transaction=True)

# Function extracted without decorators from commit6bffd48; frozen exactly, not
# a reimplementation. Parent independently checks the source/body hash.
BASELINE_SOURCE = 'def _verify_current_images(export, person):\n    from .rights_exports import image_content\n\n    binding = RightsExportPortabilityBinding.objects.select_related("review__selection").get(\n        export=export\n    )\n    declarations = unseal(binding.review.selection.encrypted_selection).get("images", [])\n    for declaration in declarations:\n        _, current = image_content(person, declaration["photo"])\n        if hashlib.sha256(current).hexdigest() != declaration["content_digest"]:\n            raise ValidationError("Portable image content changed")\n        del current\n\n'
BASELINE_SHA256 = "94f391fe875267666ef2316ae5470965f9cc888481241adbb8232e72deb6761c"


def _baseline_guard():
    assert hashlib.sha256(BASELINE_SOURCE.encode()).hexdigest() == BASELINE_SHA256
    module = ast.parse(BASELINE_SOURCE)
    assert len(module.body) == 1 and isinstance(module.body[0], ast.FunctionDef)
    assert module.body[0].name == "_verify_current_images"
    namespace = dict(vars(rights_portability_export))
    exec(compile(module, "<guard-6bffd48>", "exec"), namespace)
    return namespace["sensitive_variables"]()(namespace["_verify_current_images"])


def _two_image_selection(request, settings, monkeypatch, account_only, binary=False):
    """Broaden only the original binary fixture recipe; all services stay native."""
    assert binary and not account_only
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    revision = person.listing.approved_revision
    assert revision.photos.count() == 1
    output = io.BytesIO()
    Image.new("RGB", (32, 24), (117, 59, 203)).save(output, format="WEBP", lossless=True)
    content = output.getvalue()
    blob = Blob.objects.create(sha256=hashlib.sha256(content).hexdigest(), status="ready",
                               width=32, height=24)
    blob.original.save(str(uuid4()) + ".webp", ContentFile(content))
    blob.derivative.save(str(uuid4()) + ".webp", ContentFile(content))
    Photo.objects.create(revision=revision, blob=blob, position=1, comparison_complete=True)
    case, author, baseline, previous, profile, subject, receipt = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    with transaction.atomic():
        locked, scoped_person, listing = reviewer_case(author, case.pk)
        source = source_copy(scoped_person, listing, locked)
    positions = [(item["photo"], revision_index, image_index)
                 for revision_index, row in enumerate(source["revisions"])
                 for image_index, item in enumerate(row["images"])]
    assert len(positions) == 2
    positions.sort(reverse=True)
    reason = "Inspect both synthetic images before complete covered delivery"
    facts = {"status": "eligible", "basis": "contract", "origin": "provided",
             "automated": True, "subject_related": True, "third_party_reviewed": True,
             "reason": reason, "evidence": "Two synthetic private WebP contents and native reads"}
    for _, revision_index, image_index in positions:
        page = prepare(author, case.pk, case.version, baseline.assessment_review_id,
                       uuid4(), reason, revision_index, image_index)
        selected = save(author, uuid4(), page["token"], reason, True, facts)
    reviewer = previous.action.actor
    record(reviewer, case.pk, case.version, selected.pk, uuid4(), reason)
    declarations = unseal(selected.encrypted_selection)["images"]
    assert [item["photo"] for item in declarations] == [item[0] for item in positions]
    for declaration in declarations:
        inspect(reviewer, case.pk, case.version, selected.pk,
                declaration["photo"], uuid4(), reason)
    decision, _ = record(reviewer, case.pk, case.version, selected.pk,
                         uuid4(), reason, "review", "approved")
    return case, author, selected, decision, profile, subject, receipt


def _generated_two(request, settings, monkeypatch):
    import test_rights_portability_covered_export_races as coverage_fixture

    _owned_database()
    settings.DEBUG = False  # Set before generation: seal rule_version includes settings.
    assert settings.MEDIA_STORAGE_PROVIDER == "local" and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    with monkeypatch.context() as patch:
        patch.setattr(coverage_fixture, "prepared_covered_selection", _two_image_selection)
        result = generated(request, settings, monkeypatch)
    case, author, export, _ = result
    check(case, author, export)  # The delivery caller may need its first full seal.
    assert check(case, author, export) is True
    declarations = unseal(export.portability_binding.review.selection.encrypted_selection)["images"]
    identifiers = [item["photo"] for item in declarations]
    assert len(identifiers) == 2 and identifiers == sorted(identifiers, reverse=True)
    photos = {str(row.pk): row for row in Photo.objects.select_related("blob").filter(pk__in=identifiers)}
    expected = []
    for declaration in declarations:
        photo = photos[declaration["photo"]]
        with photo.blob.derivative.open("rb") as stream:
            content = stream.read()
        digest = hashlib.sha256(content).hexdigest()
        assert digest == declaration["content_digest"]
        expected.append((photo.pk, photo.blob_id, digest, len(content)))
    assert len({row[1] for row in expected}) == 2
    return result, expected


def _assert_locks_held(expected):
    """Independent real PG attempts must find both kinds of selected row locked."""
    assert connection.in_atomic_block and connection.vendor == "postgresql"
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_backend_pid()")
        caller_pid = cursor.fetchone()[0]

    def probe():
        connections.close_all()
        observed = 0
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                assert cursor.fetchone()[0] != caller_pid
                cursor.execute("SET LOCAL statement_timeout='3s'")
                cursor.execute("SET LOCAL lock_timeout='1s'")
                for photo_id, blob_id, _, _ in expected:
                    for model, identifier in ((Blob, blob_id), (Photo, photo_id)):
                        try:
                            with transaction.atomic():
                                model.objects.select_for_update(nowait=True).get(pk=identifier)
                        except DatabaseError as error:
                            assert getattr(error.__cause__, "sqlstate", None) == "55P03"
                            observed += 1
                        else:
                            raise AssertionError("Selected image row was not already locked by seal replay")
            return observed
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        assert pool.submit(probe).result(timeout=20) == 4
    return 4


def _audit_counts():
    return RightsAction.objects.count(), RightsExportDownload.objects.count()


def test_held_seal_guard_paired_reference_and_preexisting_locks(
    request, settings, monkeypatch, record_property
):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit paired held-seal diagnostic; not default functional coverage")
    assert not os.environ.get("PYTEST_XDIST_WORKER"), "Paired measurement requires serial execution"
    (case, author, export, _), expected = _generated_two(request, settings, monkeypatch)
    settings.DEBUG = False
    candidate = rights_portability_export._verify_current_images
    baseline = _baseline_guard()
    original_read = rights_exports._read_image_blob
    active = None

    def read(blob):
        content = original_read(blob)
        if active is not None:
            active.append((blob.pk, hashlib.sha256(content).hexdigest(), len(content)))
        return content

    monkeypatch.setattr(rights_exports, "_read_image_blob", read)
    expected_reads = [(blob_id, digest, size) for _, blob_id, digest, size in expected]
    manifest_digest = hashlib.sha256("".join(row[2] for row in expected).encode()).hexdigest()
    before = _audit_counts()
    samples = []
    for round_index in range(6):
        order = ("baseline", "candidate") if round_index % 2 == 0 else ("candidate", "baseline")
        for method in order:
            observations = []
            implementation = baseline if method == "baseline" else candidate

            def guarded(current_export, person):
                nonlocal active
                assert current_export.pk == export.pk
                lock_count = _assert_locks_held(expected)
                counters = {"sql_queries": 0, "sql_execute_seconds": 0.0}

                def observe(execute, sql, params, many, context):
                    assert sql.lstrip().upper().startswith("SELECT") and not many
                    counters["sql_queries"] += 1
                    started = time.perf_counter()
                    try:
                        return execute(sql, params, many, context)
                    finally:
                        counters["sql_execute_seconds"] += time.perf_counter() - started

                active = []
                with connection.execute_wrapper(observe):
                    started = time.perf_counter()
                    cpu_started = time.thread_time()
                    implementation(current_export, person)
                    cpu = time.thread_time() - cpu_started
                    wall = time.perf_counter() - started
                reads = active
                active = None
                assert reads == expected_reads
                assert counters["sql_queries"] == (7 if method == "baseline" else 4)
                observations.append({"round": round_index, "method": method,
                                     "phase": "first" if round_index == 0 else "warm",
                                     "django_debug": settings.DEBUG, "wall_seconds": wall,
                                     "thread_cpu_seconds": cpu, **counters,
                                     "reads": len(reads), "bytes": sum(row[2] for row in reads),
                                     "pre_guard_locks": lock_count,
                                     "manifest_digest": manifest_digest})

            with monkeypatch.context() as patch:
                patch.setattr(rights_portability_export, "_verify_current_images", guarded)
                assert check(case, author, export) is True
            assert len(observations) == 1  # No fallback/full validation or duplicate guard.
            samples.extend(observations)
    assert len(samples) == 12 and _audit_counts() == before
    record_property("n02b_held_guard_samples", json.dumps(samples, sort_keys=True))
    record_property("n02b_baseline_sha256", BASELINE_SHA256)
    record_property("n02b_scope", "Actual held-seal caller, two distinct small synthetic WebP images in reverse PK order;12 paired guard samples and four preexisting PG row-lock witnesses per invocation. No HTTP/full-size MOD09/p95 or external identity verification claim.")


def test_held_seal_rejects_changed_last_file_without_success_audits(
    request, settings, monkeypatch, record_property
):
    (case, author, export, _), expected = _generated_two(request, settings, monkeypatch)
    settings.DEBUG = False
    candidate = rights_portability_export._verify_current_images
    original_read = rights_exports._read_image_blob
    derivative = Blob.objects.get(pk=expected[-1][1]).derivative
    with derivative.open("rb") as stream:
        original = stream.read()
    changed = bytearray(original)
    changed[-1] ^= 1
    assert changed[:12] == original[:12]
    before = _audit_counts()
    guard_calls, reads = [], []

    def read(blob):
        content = original_read(blob)
        reads.append(blob.pk)
        return content

    def guarded(current_export, person):
        guard_calls.append(_assert_locks_held(expected))
        return candidate(current_export, person)

    try:
        with derivative.open("wb") as stream:
            stream.write(changed)
        with monkeypatch.context() as patch:
            patch.setattr(rights_exports, "_read_image_blob", read)
            patch.setattr(rights_portability_export, "_verify_current_images", guarded)
            with pytest.raises(ValidationError, match="Portable image content changed"):
                check(case, author, export)
        assert guard_calls == [4]
        assert reads == [row[1] for row in expected]
        assert _audit_counts() == before
    finally:
        with derivative.open("wb") as stream:
            stream.write(original)
    assert check(case, author, export) is True
    record_property("n02b_late_drift", json.dumps({"guard_calls": 1, "pre_guard_locks": 4,
                                                  "reads": 2, "audit_counts_unchanged": True,
                                                  "restored_and_revalidated": True}, sort_keys=True))
