"""Dense detector reference with equivalent fresh Match insertion per sample."""

import hashlib
import json
import resource
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path

import cv2
import pytest
from django.db import connection
from test_similarity_scan_cost import corpus, directory, photo_environment  # noqa: F401

from apps.mediafiles import services, similarity
from apps.mediafiles.models import Match, Photo
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)


def test_dense_prepared_query_reference(request, settings, monkeypatch, record_property):
    if not any(Path(str(arg).split("::")[0]).name == Path(__file__).name for arg in request.config.args):
        pytest.skip("Explicit finite serial detector contrast only")
    assert connection.vendor == "postgresql"
    query, expected, digest, bytes_written = corpus(request, 100, dense=True)
    settings.CELERY_TASK_ALWAYS_EAGER = False
    assert not celery_app.conf.task_always_eager
    original_features = similarity._orb_features
    original_stored = services.stored_signature
    original_confirm = services.confirm_match
    state, samples = {}, []

    def features(*args, **kwargs):
        state["feature_calls"] += 1
        return original_features(*args, **kwargs)

    def stored(blob):
        state["candidate_sha256"] = blob.sha256
        return original_stored(blob)

    def confirm(*args, **kwargs):
        # Fix only the diagnostic RNG, identically before each comparison in both runs.
        cv2.setRNGSeed(1847)
        result = original_confirm(*args, **kwargs)
        state["results"][state["candidate_sha256"]] = asdict(result)
        state["confirm_calls"] += 1
        return result

    monkeypatch.setattr(similarity, "_orb_features", features)
    monkeypatch.setattr(services, "stored_signature", stored)
    monkeypatch.setattr(services, "confirm_match", confirm)
    previous_threads = cv2.getNumThreads()
    cv2.setNumThreads(1)
    try:
        for ordinal in range(6):
            # Original fresh-insertion state, never an already populated second pass.
            Match.objects.filter(photo=query).delete()
            Photo.objects.filter(pk=query.pk).update(comparison_complete=False)
            state.clear()
            state.update(feature_calls=0, confirm_calls=0, results={})
            totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

            def observe(execute, sql, params, many, context):
                totals["sql_queries"] += 1
                started = time.perf_counter()
                try:
                    return execute(sql, params, many, context)
                finally:
                    totals["sql_execute_seconds"] += time.perf_counter() - started

            cv2.setRNGSeed(1847)
            tracemalloc.start()
            started, cpu = time.perf_counter(), time.thread_time()
            try:
                with connection.execute_wrapper(observe):
                    services.detect_matches(query.blob_id)
                elapsed, used_cpu = time.perf_counter() - started, time.thread_time() - cpu
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            matches = list(Match.objects.filter(photo=query).select_related("candidate__blob"))
            assert {m.candidate_id for m in matches} == expected
            assert state["confirm_calls"] == len(expected)
            query.refresh_from_db()
            assert query.comparison_complete
            assert not Match.objects.filter(photo=query, candidate__revision__listing__person=query.revision.listing.person).exists()
            persisted = {m.candidate.blob.sha256: {"method": m.method, "score": m.score} for m in matches}
            result_digest = hashlib.sha256(json.dumps(state["results"], sort_keys=True).encode()).hexdigest()
            match_digest = hashlib.sha256(json.dumps(persisted, sort_keys=True).encode()).hexdigest()
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert rss < 1024 * 1024
            samples.append({"ordinal": ordinal, "wall_seconds": elapsed, "thread_cpu_seconds": used_cpu,
                            "feature_calls": state["feature_calls"], "confirm_calls": state["confirm_calls"],
                            "match_count": len(matches), "complete_result_sha256": result_digest,
                            "persisted_method_score_sha256": match_digest,
                            "operation_python_peak_bytes": peak, "process_maxrss_kib": rss, **totals})
    finally:
        cv2.setNumThreads(previous_threads)
    assert len({s["complete_result_sha256"] for s in samples}) == 1
    assert len({s["persisted_method_score_sha256"] for s in samples}) == 1
    record_property("n03b_dense_reference", json.dumps({
        "corpus_sha256": digest, "corpus_bytes": bytes_written, "candidates": 100,
        "expected_matches": len(expected), "samples": samples,
        "scope": "Six fresh-insertion detector calls, first separate+five later, one dense100 corpus, fixed diagnostic RNG and cv2thread1. No queue/upload/p95/capacity or global cache claim."
    }, sort_keys=True))
