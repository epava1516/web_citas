"""Paired metadata mechanisms with identical real files; not MOD09 acceptance."""

import hashlib
import json
import os
import time
from collections import defaultdict
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from capacity_target_fixture import populate
from django.db import connection, transaction
from test_photos import photo_environment  # noqa: F401

from apps.mediafiles.models import Photo
from apps.safety import rights_exports

pytestmark = pytest.mark.django_db(transaction=True)


def test_current_image_metadata_paired_reference(request, settings, monkeypatch, record_property):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit paired metadata diagnostic only; not default functional coverage")
    assert not os.environ.get("PYTEST_XDIST_WORKER"), "Paired measurement requires serial execution"
    _owned_database()
    assert settings.MEDIA_STORAGE_PROVIDER == "local" and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    request.getfixturevalue("photo_environment")
    settings.DEBUG = False
    cohorts = []
    for identity in ("capacity-subject-a", "capacity-subject-b"):
        person, listing, rows, calibration = populate(identity)
        assert len(rows) == listing.revisions.count() == 1500
        assert abs(calibration["candidate_bytes"] - 16 * 1024**2) <= .01 * 16 * 1024**2
        photos = list(Photo.objects.filter(revision__listing=listing).select_related("blob").order_by("pk"))
        assert len(photos) == 16
        expected = {str(p.pk): (p.blob.sha256, p.blob.derivative.size) for p in photos}
        assert sum(size for _, size in expected.values()) == calibration["originals_bytes"]
        cohorts.append((person, list(reversed(photos)), expected, calibration))
    original = rights_exports._read_image_blob
    active = None

    def counted(blob):
        content = original(blob)
        if active is not None:
            active["physical_reads"] += 1
            active["physical_bytes"] += len(content)
        return content

    monkeypatch.setattr(rights_exports, "_read_image_blob", counted)
    observations = []
    for cohort, (person, photos, expected, calibration) in enumerate(cohorts):
        identifiers = [str(p.pk) for p in photos]
        before = list(Photo.objects.filter(pk__in=identifiers).order_by("pk").values_list(
            "pk", "blob_id", "revision_id", "approved", "removed_at", "comparison_complete", "position"))
        expected_hashes = [expected[p][0] for p in identifiers]
        manifest_digest = hashlib.sha256("".join(expected_hashes).encode()).hexdigest()
        for round_index in range(6):
            order = ("single", "bulk") if round_index % 2 == 0 else ("bulk", "single")
            for method in order:
                active = {"physical_reads": 0, "physical_bytes": 0}
                counters = {"sql_queries": 0, "sql_execute_seconds": 0.0}
                query_kinds = defaultdict(int)

                def observe(execute, sql, params, many, context):
                    counters["sql_queries"] += 1
                    query_kinds["select" if sql.lstrip().upper().startswith("SELECT") else "other"] += 1
                    started = time.perf_counter()
                    try:
                        return execute(sql, params, many, context)
                    finally:
                        counters["sql_execute_seconds"] += time.perf_counter() - started

                hashes = []
                with transaction.atomic():
                    with connection.execute_wrapper(observe):
                        started = time.perf_counter()
                        cpu_started = time.thread_time()
                        stream = (rights_exports.image_contents(person, identifiers) if method == "bulk"
                                  else (rights_exports.image_content(person, p) for p in identifiers))
                        for position, (photo, content) in enumerate(stream):
                            assert str(photo.pk) == identifiers[position]
                            digest = hashlib.sha256(content).hexdigest()
                            assert digest == expected[str(photo.pk)][0] and len(content) == expected[str(photo.pk)][1]
                            hashes.append(digest)
                            del content
                        cpu_seconds = time.thread_time() - cpu_started
                        wall_seconds = time.perf_counter() - started
                assert hashes == expected_hashes
                assert active["physical_reads"] == 16
                assert active["physical_bytes"] == calibration["originals_bytes"]
                assert counters["sql_queries"] == (48 if method == "single" else 3)
                assert query_kinds["other"] == 0
                assert list(Photo.objects.filter(pk__in=identifiers).order_by("pk").values_list(
                    "pk", "blob_id", "revision_id", "approved", "removed_at", "comparison_complete", "position")) == before
                observations.append({"cohort": cohort, "round": round_index,
                                     "phase": "first" if round_index == 0 else "warm",
                                     "method": method, "django_debug": settings.DEBUG, "service_seconds_instrumented": wall_seconds,
                                     "thread_cpu_seconds": cpu_seconds, **counters, **active,
                                     "revisions": 1500, "candidate_bytes": calibration["candidate_bytes"],
                                     "manifest_digest": manifest_digest})
                active = None
    assert len(observations) == 24
    record_property("n02a_image_metadata_samples", json.dumps(observations, sort_keys=True))
    record_property("n02a_scope", "Two sequential subjects, each1500revisions/~16MiB JSON/16realWebP/~64MiB files. First pair separate,5warm pairs reverse-alternated; identical helper inputs and fresh physical reads/hash. Locks held in actual PostgreSQL transactions. Direct helper comparison only, no HTTP authority/export/token/proxy/generation/p95 acceptance or integrated code speedup.")
