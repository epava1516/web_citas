"""Two target cases with paired real TCP page requests; no full capacity claim."""

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from django.conf import settings as runtime_settings
from django.db import connections
from test_capacity_selection_tcp import REASON, prepare_target
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsPortabilitySelectionRead, RightsPortabilitySelectionReview
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not getattr(runtime_settings, "CAPACITY_ENVIRONMENT_VERIFIED", False),
                      reason="Requires owned capacity runner with verified kernel limits"),
]


@pytest.mark.usefixtures("photo_environment")
def test_two_target_selection_pages_overlapping_tcp(request, settings, monkeypatch, record_property):
    if getattr(settings, "CAPACITY_SELECTION_GUNICORN", False):
        from capacity_gunicorn import server

        with server(settings, record_property) as endpoint:
            measure_targets(request, settings, monkeypatch, endpoint, record_property)
    else:
        measure_targets(request, settings, monkeypatch, request.getfixturevalue("live_server"), record_property)


def measure_targets(request, settings, monkeypatch, live_server, record_property):
    targets = [prepare_target(request, settings, monkeypatch, live_server, identity,
                              independent_reviewer=True)
               for identity in ["capacity-subject-a", "capacity-subject-b"]]
    assert targets[0][0].pk != targets[1][0].pk
    results = [{"case": str(target[0].pk), "samples": [], "intervals": [], "response_bytes": [],
                "fixture": target[5], "build_seconds": target[6],
                "preparation_seconds": target[7], "first_open_seconds": target[8]}
               for target in targets]
    complete = getattr(settings, "CAPACITY_SELECTION_COMPLETE", False)
    for result in results:
        result.update(approval_samples=[], approval_intervals=[], decisions=[],
                      selections=[], version_preparation_seconds=[])
    barrier = Barrier(2)

    def measure(index):
        case, row, client, endpoint, csrf, *_ = targets[index]
        peer = "capacity-subject-b" if index == 0 else "capacity-subject-a"
        try:
            for generation in range(20 if complete else 1):
                if generation:
                    binding = unseal(row.encrypted_selection)
                    author = User.objects.get(pk=row.actor_id)
                    begin = time.perf_counter()
                    row = save_selection(author, case.pk, case.version, row.assessment_review_id,
                                         uuid4(), row.version, REASON, binding["selection"],
                                         field_evidence=binding.get("field_evidence"))
                    elapsed = time.perf_counter() - begin
                    results[index]["version_preparation_seconds"].append(elapsed)
                    assert elapsed <= 60
                    endpoint = live_server.url + f"/en/moderation/rights/{case.pk}/portability/selection/{row.pk}/review/"
                results[index]["selections"].append(row.pk)
                for round_index in range(31 if complete else 20):
                    barrier.wait(timeout=90)
                    payload = urllib.parse.urlencode({"key": str(uuid4()), "version": case.version,
                        "operation": "inspect", "reason": REASON, "page": round_index + 1 if complete else 1}).encode()
                    query = urllib.request.Request(endpoint, data=payload, headers={
                        "Content-Type": "application/x-www-form-urlencoded", "Referer": endpoint,
                        "X-CSRFToken": csrf,
                    })
                    begin = time.perf_counter()
                    with client.open(query, timeout=90) as response:
                        content = response.read()
                        end = time.perf_counter()
                        assert response.status == 200 and "no-store" in response.headers["Cache-Control"]
                    results[index]["samples"].append(end - begin)
                    results[index]["intervals"].append([begin, end])
                    results[index]["response_bytes"].append(len(content))
                    assert peer.encode() not in content
                    latest = RightsPortabilitySelectionRead.objects.filter(selection=row).latest("pk")
                    assert latest.page_metadata["page"] == (round_index + 1 if complete else 1) and latest.page_metadata["size"] == 50
                    assert latest.page_metadata["total"] == 1501
                    if complete and round_index == 0:
                        negative = urllib.parse.urlencode({"key": str(uuid4()), "version": case.version,
                            "operation": "review", "reason": REASON, "outcome": "approved"}).encode()
                        try:
                            client.open(urllib.request.Request(endpoint, data=negative, headers={
                                "Referer": endpoint, "X-CSRFToken": csrf,
                            }), timeout=90)
                        except urllib.error.HTTPError as error:
                            assert error.code == 409
                            error.read()
                        else:
                            raise AssertionError("Incomplete page review was approved")
                        assert not RightsPortabilitySelectionReview.objects.filter(selection=row).exists()
                if complete:
                    for _ in range(1):
                        barrier.wait(timeout=90)
                        key = uuid4()
                        payload = urllib.parse.urlencode({"key": str(key), "version": case.version,
                            "operation": "review", "reason": REASON, "outcome": "approved"}).encode()
                        begin = time.perf_counter()
                        with client.open(urllib.request.Request(endpoint, data=payload, headers={
                            "Referer": endpoint, "X-CSRFToken": csrf,
                        }), timeout=90) as response:
                            response.read()
                            end = time.perf_counter()
                            assert response.status == 200 and "no-store" in response.headers["Cache-Control"]
                        results[index]["approval_samples"].append(end - begin)
                        results[index]["approval_intervals"].append([begin, end])
                        decision = RightsPortabilitySelectionReview.objects.get(selection=row, action__key=key)
                        assert decision.outcome == "approved" and len(decision.page_reads) == 31
                        pages = list(RightsPortabilitySelectionRead.objects.filter(pk__in=decision.page_reads)
                                     .values_list("page_metadata__page", flat=True))
                        assert set(pages) == set(range(1, 32))
                        results[index]["decisions"].append(decision.pk)
        finally:
            barrier.abort()
            connections.close_all()

    errors = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(measure, index) for index in range(2)]
        for future in futures:
            try:
                future.result(timeout=5000 if complete else 540)
            except Exception as error:
                errors.append(f"{type(error).__name__}: {error}")
    for result in results:
        samples = result["samples"]
        result["p95_seconds"] = sorted(samples)[math.ceil(len(samples) * .95) - 1] if samples else None
        approvals = result.get("approval_samples", [])
        result["approval_p95_seconds"] = sorted(approvals)[math.ceil(len(approvals) * .95) - 1] if approvals else None
    rss_kib = next(int(line.split()[1]) for line in Path("/proc/self/status").read_text().splitlines()
                   if line.startswith("VmHWM:"))
    record_property("selection_tcp_measurements", json.dumps({
        "cases": results, "errors": errors, "process_peak_rss_bytes": rss_kib * 1024,
        "complete_selection": complete,
        "scope": "Two independent real cases, reviewers and TCP clients; 20fresh selection versions,31new pages/version and one approval/version when complete_selection=True, otherwise first-page requests only. Real PG/Redis/WSGI server; topology separately recorded; no binary delivery or full capacity. RSS belongs to shared pytest/application process, not aggregate cgroup memory.",
    }))
    if getattr(settings, "CAPACITY_SELECTION_PROFILE", False):
        def diagnose(target):
            case, _, client, endpoint, csrf, *_ = target
            payload = urllib.parse.urlencode({"key": str(uuid4()), "version": case.version,
                "operation": "inspect", "reason": REASON, "page": 1}).encode()
            query = urllib.request.Request(endpoint, data=payload, headers={
                "Content-Type": "application/x-www-form-urlencoded", "Referer": endpoint,
                "X-CSRFToken": csrf, "X-Capacity-Profile": "1",
            })
            with client.open(query, timeout=90) as response:
                assert response.status == 200
                response.read()
        with ThreadPoolExecutor(max_workers=2) as executor:
            for future in [executor.submit(diagnose, target) for target in targets]:
                future.result(timeout=100)
    assert not errors
    assert rss_kib * 1024 <= 1024 ** 3
    assert all(len(result["samples"]) == (620 if complete else 20) for result in results)
    for first, second in zip(results[0]["intervals"], results[1]["intervals"], strict=True):
        assert max(first[0], second[0]) < min(first[1], second[1]), "TCP pair did not overlap"
    if complete:
        assert all(len(result.get("approval_samples", [])) == 20 and len(set(result["decisions"])) == 20 for result in results)
        assert all(result["approval_p95_seconds"] <= 5 for result in results), [result["approval_p95_seconds"] for result in results]
    assert all(result["p95_seconds"] <= 2 for result in results), [result["p95_seconds"] for result in results]
