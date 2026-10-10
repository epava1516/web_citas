"""Diagnostic profile of one target-sized case; never a capacity sample or limit verdict."""

import json
import tarfile
import time
import traceback
from pathlib import Path
from threading import Barrier

import pytest
from capacity_delivery_flow import run_case
from capacity_fingerprint_profile import fingerprint_profile
from capacity_gunicorn import server
from django.conf import settings as runtime_settings
from django.db import connections
from test_capacity_selection_tcp import prepare_target
from test_reports import directory, photo_environment  # noqa: F401

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not getattr(runtime_settings, "CAPACITY_DELIVERY_PROFILE", False),
                      reason="Requires owned capacity runner diagnostic profile mode"),
]


@pytest.mark.usefixtures("photo_environment")
def test_owned_target_stage_profiles(request, settings, monkeypatch, record_property):
    metrics, errors = {"success": False}, []
    settings.RIGHTS_VERIFICATION_BACKEND = "simulator"
    baseline_capture = getattr(settings, "CAPACITY_BASELINE_CAPTURE", False)
    baseline_source = getattr(settings, "CAPACITY_BASELINE_INPUT", "")
    baseline_key = getattr(settings, "CAPACITY_BASELINE_KEY", "")
    descriptor = None
    if baseline_source:
        from cryptography.exceptions import InvalidTag
        from diagnostic_baseline import restore
        from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
        try:
            descriptor = restore(baseline_source, baseline_key)
            metrics["baseline"] = "HIT_DIAGNOSTIC_REUSED_PREPARATION"
        except (ValueError, OSError, KeyError, TypeError, tarfile.TarError, InvalidTag,
                ObjectDoesNotExist, PermissionDenied, ValidationError) as rejected:
            # Scratch cleanup must finish before fallback; no approval fixture.
            metrics["baseline"] = "CACHE_REJECTED"
            metrics["baseline_rejection"] = type(rejected).__name__
    captured = []
    with server(settings, record_property) as endpoint:
        try:
            context = {}
            if descriptor is not None:
                from diagnostic_baseline import resume
                resume(descriptor, endpoint, settings, metrics)
                metrics["success"] = "post_validation_profile" in metrics
                assert metrics["success"]
                record_property("diagnostic_baseline", json.dumps({"event": metrics["baseline"]}))
                return
            target = prepare_target(request, settings, monkeypatch, endpoint, "capacity-subject-a",
                                    independent_reviewer=True, include_binary=True, details=context)
            metrics.update(fixture=target[5], build_seconds=target[6], scalar_preparation_seconds=target[7])
            full = getattr(settings, "CAPACITY_DELIVERY_PROFILE_FULL", False)
            if full:
                metrics["fingerprint_sql"] = fingerprint_profile(
                    settings, endpoint, context["profile"], target[0])
            run_case(0, target, context, endpoint, settings, Barrier(1), metrics, diagnostic=True,
                     full=full, approved_boundary=captured.append if baseline_capture else None)
            metrics["success"] = (metrics.get("success") is not False and "post_validation_profile" in metrics
                                  if full else
                                  metrics.get("diagnostic_stopped_after") == "coverage_page_read")
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}")
            metrics["failure_traceback"] = traceback.format_exc(limit=12)[-6000:]
        except KeyboardInterrupt:
            errors.append("DiagnosticInterrupted: operator stopped this diagnostic; no capacity verdict")
            metrics["operator_interrupted"] = True
        finally:
            connections.close_all()
            # The WSGI wrapper writes after the response body is closed: wait for every stage file.
            stages = [name[:-len("_profiled_seconds")] for name in metrics if name.endswith("_profiled_seconds")]
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline and not all(
                any(Path("/tmp").glob(f"capacity-profile-{stage}-*.txt")) for stage in stages
            ):
                time.sleep(0.2)
            served = {path.name: path.read_text() for path in Path("/tmp").glob("capacity-profile-*.txt")}
            record_property("delivery_profile", json.dumps({
                "metrics": metrics, "errors": errors, "server_profiles": served,
                "scope": "One synthetic1500/16MiB/64MiB case; reduced populations; cProfile overhead "
                         "included; diagnostic of cost attribution only, never compared to limits.",
            }))
    if baseline_capture and not errors:
        from diagnostic_baseline import capture
        assert len(captured) == 1
        metrics["baseline_capture"] = capture(captured[0], "/tmp/diagnostic-baseline.bin", baseline_key)
        metrics["success"] = True
        record_property("diagnostic_baseline", json.dumps(metrics["baseline_capture"]))
    assert not errors, errors
    assert metrics["success"]
