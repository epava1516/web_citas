"""Explicit historical-photo growth with two fixed, eligible ready image contents."""

import hashlib
import io
import json
import math
import os
import resource
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import cv2
import imagehash
import pytest
from capacity_runtime_role import _owned_database
from django.core.files.base import ContentFile
from django.db import connection
from PIL import Image
from test_photo_disposition_authority import ledger
from test_photos import photo_environment, synthetic_image  # noqa: F401

from apps.core.models import Person, User
from apps.listings.history import rectification_history_ids
from apps.listings.models import Listing, Revision
from apps.mediafiles import services, tasks
from apps.mediafiles.models import Blob, Match, Photo
from apps.mediafiles.similarity import compute_signature
from config.celery import app as celery_app

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.usefixtures("photo_environment")]


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _measured(function):
    totals = {"sql_calls": 0, "sql_execute_seconds": 0.0}

    def observe(execute, sql, params, many, context):
        totals["sql_calls"] += 1
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            totals["sql_execute_seconds"] += time.perf_counter() - started

    started, cpu = time.perf_counter(), time.thread_time()
    with connection.execute_wrapper(observe):
        function()
    result = {"wall_seconds": time.perf_counter() - started,
              "thread_cpu_seconds": time.thread_time() - cpu, **totals}
    assert all(math.isfinite(value) and value >= 0 for value in result.values())
    return result


def _owner(label):
    user = User.objects.create(username=f"n03f2-{label}", email=f"n03f2-{label}@example.invalid")
    person = Person.objects.create(individual=user, subject=user, alias="Synthetic retained corpus")
    listing = Listing.objects.create(person=person)
    revision = Revision.objects.create(listing=listing, manager_version=person.manager_version)
    listing.approved_revision = revision
    listing.save(update_fields=["approved_revision"])
    return person, revision


def _ready_blob(image, label):
    original, derivative = io.BytesIO(), io.BytesIO()
    image.save(original, format="PNG")
    image.save(derivative, format="WEBP", quality=98, method=4)
    raw, body = original.getvalue(), derivative.getvalue()
    signature = compute_signature(image)
    blob = Blob.objects.create(
        sha256=hashlib.sha256(raw).hexdigest(), status="ready", attempts=1,
        width=image.width, height=image.height, signature=asdict(signature),
        phash=str(imagehash.phash(image)),
        regional_hashes=[f"{value:016x}" for _, value in signature.window_hashes],
    )
    blob.original.save(f"n03f2-{label}.png", ContentFile(raw))
    blob.derivative.save(f"n03f2-{label}.webp", ContentFile(body))
    manifest = {"kind": label, "original_sha256": blob.sha256,
                "derivative_sha256": hashlib.sha256(body).hexdigest(),
                "original_bytes": len(raw), "derivative_bytes": len(body),
                "signature_sha256": _digest(asdict(signature)),
                "width": image.width, "height": image.height}
    return blob, manifest


def _file_manifest(blobs):
    result = []
    for blob in blobs:
        row = {"original_sha256": blob.sha256}
        for name in ("original", "derivative"):
            with getattr(blob, name).open("rb") as stream:
                body = stream.read()
            row[name] = {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        result.append(row)
    return result


@pytest.mark.parametrize("retained", [0, 10, 100], ids=["history-0", "history-10", "history-100"])
def test_retained_history_with_fixed_current_corpus(
    request, settings, monkeypatch, record_property, retained
):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial retained-population diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert request.config.pluginmanager.hasplugin("scripts.local_ci_broker")
    generation = request.getfixturevalue("isolated_test_broker")
    assert generation == os.environ["LOCAL_CI_TEST_QUEUE_GENERATION"] == settings.TASK_QUEUE_GENERATION
    _owned_database()
    assert connection.vendor == "postgresql" and not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert settings.MEDIA_STORAGE_PROVIDER == "local" and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    # No workers are launched. Publication refresh remains queued in this case's
    # owned isolated namespace; captured media transport is never execution proof.
    settings.CELERY_TASK_ALWAYS_EAGER = False
    assert celery_app.conf.task_always_eager is False
    assert Blob.objects.count() == Photo.objects.count() == Match.objects.count() == 0
    previous_threads = cv2.getNumThreads()
    cv2.setNumThreads(1)
    try:
        base = synthetic_image(43)
        compressed = io.BytesIO()
        base.crop((128, 0, 640, 480)).save(compressed, format="JPEG", quality=70)
        with Image.open(io.BytesIO(compressed.getvalue())) as decoded:
            peer_image = decoded.convert("RGB")
        query_blob, query_manifest = _ready_blob(base, "query")
        peer_blob, peer_manifest = _ready_blob(peer_image, "peer")
        assert query_blob.sha256 != peer_blob.sha256
        assert services.compare_signatures(services.stored_signature(query_blob),
                                           services.stored_signature(peer_blob)).is_candidate
        _, query_revision = _owner("query")
        _, peer_revision = _owner("peer")
        history_person, history_source = _owner("history")
        query = Photo.objects.create(revision=query_revision, blob=query_blob, comparison_complete=False)
        peer = Photo.objects.create(revision=peer_revision, blob=peer_blob, comparison_complete=True)
        history_revisions = []
        history_photos = []
        for index in range(retained):
            revision = Revision.objects.create(listing=history_person.listing,
                                               manager_version=history_person.manager_version)
            history_revisions.append(revision.pk)
            history_photos.append(Photo.objects.create(
                revision=revision, blob=query_blob if index % 2 == 0 else peer_blob,
                comparison_complete=False))
        execution = ledger(history_person)  # Native persisted synthetic authority; no human/provider claim.
        expected_history = {history_source.pk, *history_revisions}
        actual_history = set(rectification_history_ids().values_list("pk", flat=True))
        assert actual_history == expected_history
        assert not {query_revision.pk, peer_revision.pk} & actual_history
        assert Photo.objects.filter(revision_id__in=actual_history).count() == retained
        assert Photo.objects.exclude(revision_id__in=actual_history).count() == 2
        assert Blob.objects.count() == 2 and Photo.objects.count() == retained + 2
        history_ids = [photo.pk for photo in history_photos]
        history_before = list(Photo.objects.filter(pk__in=history_ids).order_by("pk").values())
        revisions_before = list(Revision.objects.filter(pk__in=expected_history).order_by("pk").values())
        execution_before = type(execution).objects.filter(pk=execution.pk).values().get()
        blobs_before = list(Blob.objects.order_by("sha256").values())
        files_before = _file_manifest([query_blob, peer_blob])
        manifest = [query_manifest, peer_manifest]
        corpus_bytes = sum(row["original_bytes"] + row["derivative_bytes"] for row in manifest)
        assert corpus_bytes < 128 * 1024 * 1024
        dispatches, calls, confirmations, samples = [], Counter(), [], []
        original_stored, original_confirm = services.stored_signature, services.confirm_match

        def observed_signature(blob):
            calls[blob.sha256] += 1
            return original_stored(blob)

        def observed_confirmation(*args, **kwargs):
            result = original_confirm(*args, **kwargs)
            confirmations.append(asdict(result))
            return result

        def selector(expected):
            dispatches.clear()
            measured = _measured(tasks.recover_media_jobs.run)
            assert dispatches == expected
            assert measured["sql_calls"] == 1
            return {**measured, "dispatches": len(dispatches)}

        monkeypatch.setattr(services, "stored_signature", observed_signature)
        monkeypatch.setattr(services, "confirm_match", observed_confirmation)
        monkeypatch.setattr(tasks.process_blob, "delay", dispatches.append)
        canonical = None
        for ordinal in range(6):
            # Only this active origin's Match and flag are reset; historical rows
            # and corpus bytes remain retained. This setup is outside all clocks.
            Match.objects.filter(photo=query).delete()
            Photo.objects.filter(pk=query.pk).update(comparison_complete=False)
            before_selector = selector([str(query_blob.pk)])
            calls.clear()
            confirmations.clear()
            cv2.setRNGSeed(1847)  # Declared diagnostic seed, not a production algorithm change.
            detector = _measured(lambda: services.detect_matches(query_blob.pk))
            detector_calls = dict(calls)
            assert len(confirmations) == 1 and confirmations[0]["status"] == "confirmed"
            assert detector_calls[peer_blob.sha256] == 1
            assert set(detector_calls) == {query_blob.sha256, peer_blob.sha256}
            matches = list(Match.objects.filter(photo=query).select_related("candidate__blob"))
            assert {match.candidate_id for match in matches} == {peer.pk}
            assert Match.objects.count() == 1
            match = matches[0]
            assert match.method == "orb" and match.score == confirmations[0]["inlier_ratio"]
            result = {"query_original_sha256": query_blob.sha256,
                      "candidate_original_sha256": match.candidate.blob.sha256,
                      "method": match.method, "score": match.score,
                      "confirmation": confirmations[0]}
            if canonical is None:
                canonical = result
            assert result == canonical
            query.refresh_from_db()
            peer.refresh_from_db()
            assert query.comparison_complete and peer.comparison_complete
            assert not Photo.objects.filter(pk__in=history_ids, comparison_complete=True).exists()
            after_selector = selector([])
            assert history_before == list(Photo.objects.filter(pk__in=history_ids).order_by("pk").values())
            assert revisions_before == list(Revision.objects.filter(pk__in=expected_history).order_by("pk").values())
            assert execution_before == type(execution).objects.filter(pk=execution.pk).values().get()
            assert blobs_before == list(Blob.objects.order_by("sha256").values())
            assert set(rectification_history_ids().values_list("pk", flat=True)) == expected_history
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert rss < 1024 * 1024  # Linux process high-water KiB, not whole-service RSS.
            samples.append({"ordinal": ordinal + 1, "phase": "first" if ordinal == 0 else "later",
                            "detector": detector, "selector_before": before_selector,
                            "selector_after": after_selector,
                            "signature_calls_query": detector_calls[query_blob.sha256],
                            "signature_calls_peer": detector_calls[peer_blob.sha256],
                            "confirmation_calls": len(confirmations), "recorded_matches": len(matches),
                            "result_sha256": _digest(result), "process_maxrss_kib": rss})
        assert files_before == _file_manifest([query_blob, peer_blob])
        assert Photo.objects.count() == retained + 2 and Blob.objects.count() == 2
        report = {"version": "n03f2-retained-population-v1", "retained_historical_photos": retained,
                  "historical_revisions_including_empty_source": retained + 1,
                  "active_current_photos": 2, "ready_blobs": 2,
                  "corpus": manifest, "corpus_sha256": _digest(manifest), "corpus_file_bytes": corpus_bytes,
                  "canonical_result": canonical, "samples": samples, "opencv_threads": 1,
                  "diagnostic_rng_seed": 1847,
                  "limits": "Six full direct detector calls per retained population: first plus five later. Ready signatures/files prepared outside clocks, no process generation, no worker/Beat/TCP/provider/80k claim. Selector uses captured transport, one native SQL query, no execution simulation. SQL includes numeric connection execute timing, not server CPU. Process RSS is cumulative high-water. No candidate application change, latency SLO or inferred improvement; first call includes real comparator initialization. Diagnostic wrappers delegate real functions; RNG seed set before each call, threads restored. Persisted historical ledger is synthetic authority, never human approval."}
        record_property("n03f2_retained_population", json.dumps(report, sort_keys=True, allow_nan=False))
    finally:
        cv2.setNumThreads(previous_threads)
