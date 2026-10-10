"""Diagnostic profile of one target-sized case; never a capacity sample or limit verdict."""

import json
import time
import traceback
from pathlib import Path
from threading import Barrier

import pytest
from capacity_delivery_flow import run_case
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
    with server(settings, record_property) as endpoint:
        try:
            context = {}
            target = prepare_target(request, settings, monkeypatch, endpoint, "capacity-subject-a",
                                    independent_reviewer=True, include_binary=True, details=context)
            metrics.update(fixture=target[5], build_seconds=target[6], scalar_preparation_seconds=target[7])
            full = getattr(settings, "CAPACITY_DELIVERY_PROFILE_FULL", False)
            run_case(0, target, context, endpoint, settings, Barrier(1), metrics, diagnostic=True,
                     full=full)
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
    assert not errors, errors
    assert metrics["success"]
