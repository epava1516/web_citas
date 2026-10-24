"""Finite current-detector attribution over distinct synthetic Blob contents."""

import hashlib
import io
import json
import resource
import time
import tracemalloc
from collections import Counter
from dataclasses import asdict

import cv2
import imagehash
import pytest
from django.core.files.base import ContentFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from PIL import Image
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, synthetic_image  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Revision
from apps.mediafiles import services
from apps.mediafiles.models import Blob, Match, Photo
from apps.mediafiles.similarity import compute_signature
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)


def compressed(image, quality):
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality)
    with Image.open(io.BytesIO(output.getvalue())) as decoded:
        return decoded.convert("RGB")


def corpus(request, count, *, dense=False):
    request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    peer = Person.objects.get(subject__username="fixture-v1-model-a")
    query = person.listing.approved_revision.photos.get(removed_at__isnull=True)
    Photo.objects.exclude(pk=query.pk).update(removed_at=timezone.now())
    assert not Match.objects.filter(photo=query).exists()
    with query.blob.original.open("rb") as stream:
        base = Image.open(stream).convert("RGB")
    variants = [
        ("q40", compressed(base, 40)), ("q70", compressed(base, 70)),
        ("crop_left20", base.crop((128, 0, 640, 480))),
        ("crop_top10_left10", base.crop((64, 48, 640, 480))),
        ("rotate90", base.transpose(Image.Transpose.ROTATE_90)),
        ("flat", Image.new("RGB", (640, 480), "white")),
    ]
    query_signature = services.stored_signature(query.blob)
    expected, manifest, bytes_written = set(), [], 0
    for index in range(count):
        if dense:
            kind, image = "near_duplicate", base.copy()
            # Distinct original bytes with almost identical visual content.
            # Real comparator and confirmation decide eligibility, never a stub.
            image.putpixel((0, 0), (index % 256, index // 256, 0))
        else:
            kind, image = variants[index] if index < len(variants) else (
                "unrelated", synthetic_image(910000 + index),
            )
        original, derivative = io.BytesIO(), io.BytesIO()
        image.save(original, format="PNG")
        image.save(derivative, format="WEBP", quality=85, method=4)
        raw, body = original.getvalue(), derivative.getvalue()
        signature = compute_signature(image)
        blob = Blob.objects.create(
            sha256=hashlib.sha256(raw).hexdigest(), status="ready", width=image.width,
            height=image.height, signature=asdict(signature), phash=str(imagehash.phash(image)),
            regional_hashes=[f"{value:016x}" for _, value in signature.window_hashes],
        )
        blob.original.save(f"scan-{index}.png", ContentFile(raw))
        blob.derivative.save(f"scan-{index}.webp", ContentFile(body))
        revision = Revision.objects.create(
            listing=peer.listing, manager_version=peer.manager_version,
            title=f"Synthetic retained candidate {index}",
            description="Synthetic retained image corpus, not a real person or publication.",
        )
        candidate = Photo.objects.create(revision=revision, blob=blob, comparison_complete=True)
        if services.compare_signatures(query_signature, signature).is_candidate:
            expected.add(candidate.pk)
        manifest.append(dict(index=index, kind=kind, original_sha256=blob.sha256,
                             derivative_sha256=hashlib.sha256(body).hexdigest()))
        bytes_written += len(raw) + len(body)
    assert len({row["original_sha256"] for row in manifest}) == count
    if dense:
        assert len(expected) >= count * .9
    Photo.objects.filter(pk=query.pk).update(comparison_complete=False)
    assert bytes_written < 128 * 1024 * 1024
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    return query, expected, digest, bytes_written


@pytest.mark.parametrize("count", [10, 100])
def test_current_distinct_blob_scan_attribution(request, monkeypatch, settings, record_property, count):
    if not any(str(arg).split("::")[0] == "tests/test_similarity_scan_cost.py" for arg in request.config.args):
        pytest.skip("Explicit distinct-Blob detector diagnostic only")
    measure_scan(request, monkeypatch, settings, record_property, count)


@pytest.mark.parametrize("count,dense", [(1000, False), (100, True)],
                         ids=["distinct-1000", "dense-100"])
def test_current_scan_growth_and_density(request, monkeypatch, settings, record_property, count, dense):
    if not any(str(arg).split("::")[0] == "tests/test_similarity_scan_cost.py" for arg in request.config.args):
        pytest.skip("Explicit distinct-Blob detector diagnostic only")
    measure_scan(request, monkeypatch, settings, record_property, count, dense=dense)


def measure_scan(request, monkeypatch, settings, record_property, count, *, dense=False):
    assert connection.vendor == "postgresql"
    query, expected, digest, bytes_written = corpus(request, count, dense=dense)
    # Keep publication refresh queued on this CI's owned Redis. This diagnostic
    # does not measure queue wait or worker execution and never fakes completion.
    settings.CELERY_TASK_ALWAYS_EAGER = False
    assert not celery_app.conf.task_always_eager
    calls, stage_cpu, confirmations = Counter(), Counter(), Counter()

    def observe(name, function):
        def wrapped(*args, **kwargs):
            started = time.thread_time()
            try:
                result = function(*args, **kwargs)
                if name == "confirm_match":
                    confirmations[result.status] += 1
                return result
            finally:
                calls[name] += 1
                stage_cpu[name] += time.thread_time() - started
        return wrapped

    for name in ["stored_signature", "compare_signatures", "confirm_match", "record_match"]:
        monkeypatch.setattr(services, name, observe(name, getattr(services, name)))
    previous_threads = cv2.getNumThreads()
    cv2.setNumThreads(1)
    tracemalloc.start()
    started, cpu_started = time.perf_counter(), time.thread_time()
    try:
        with CaptureQueriesContext(connection) as captured:
            services.detect_matches(query.blob_id)
        elapsed, cpu = time.perf_counter() - started, time.thread_time() - cpu_started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        cv2.setNumThreads(previous_threads)
    actual = set(Match.objects.filter(photo=query).values_list("candidate_id", flat=True))
    assert actual == expected
    assert calls["compare_signatures"] == count
    assert calls["confirm_match"] == calls["record_match"] == len(expected)
    assert not Match.objects.filter(photo=query, candidate__revision__listing__person=query.revision.listing.person).exists()
    query.refresh_from_db()
    assert query.comparison_complete
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert rss < 1024 * 1024  # Safety budget for this Python process, not total services.
    record_property("distinct_blob_scan_diagnostic", dict(
        corpus_version="synthetic-dense-blobs-v1" if dense else "synthetic-distinct-blobs-v1",
        candidates=count, corpus_sha256=digest,
        corpus_file_bytes=bytes_written, expected_candidates=len(expected), recorded_matches=len(actual),
        calls=dict(calls), stage_python_cpu_seconds=dict(stage_cpu), confirmation_statuses=dict(confirmations),
        elapsed_seconds=elapsed, python_thread_cpu_seconds=cpu,
        sql_calls=len(captured), driver_execute_seconds=sum(float(q["time"]) for q in captured),
        operation_python_peak_bytes=peak, process_maxrss_kib=rss, opencv_threads=1,
        limits="Single instrumented call per size, precomputed signatures/ready fixtures and warmed reference comparator; stage times not additive; SQL driver time is not PG CPU; no queue wait, worker, capacity or index-retrieval acceptance",
    ))
