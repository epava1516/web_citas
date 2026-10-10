"""Diagnostic cost attribution of whole-source reads at target size; never a capacity verdict."""

import cProfile
import io
import json
import pstats
import time
from contextlib import contextmanager

import pytest
from capacity_delivery_flow import FACTS
from capacity_target_fixture import PATHS, populate
from django.conf import settings as runtime_settings
from django.db import connection, transaction
from test_photos import photo_environment  # noqa: F401
from test_rights_portability import assessment

from apps.safety.crypto import seal
from apps.safety.rights import fingerprint
from apps.safety.rights_exports import canonical, source_copy
from apps.safety.rights_portability_coverage import compile_coverage
from apps.safety.rights_portability_selection import project_selected, row_reference

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not getattr(runtime_settings, "CAPACITY_DELIVERY_PROFILE", False),
                      reason="Requires owned capacity runner diagnostic profile mode"),
]


@contextmanager
def queries(log):
    def wrapper(execute, sql, params, many, context):
        begin = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            log.append((time.perf_counter() - begin, sql[:160]))

    with connection.execute_wrapper(wrapper):
        yield


def timed(results, name, operation, *args, **kwargs):
    begin = time.perf_counter()
    value = operation(*args, **kwargs)
    results.setdefault(name, []).append(time.perf_counter() - begin)
    return value


@pytest.mark.usefixtures("photo_environment")
def test_target_source_cost_attribution(record_property):
    results = {}
    person, listing, rows, manifest = populate("capacity-subject-a")
    facts = assessment()
    facts["revisions"].update(
        status="eligible", basis="contract", origin="provided", automated=True,
        subject_related=True, third_party_reviewed=True,
        reason="Synthetic target text was created exclusively for this subject",
        evidence="Own deterministic generator; no third party text or actual legal decision",
    )
    with transaction.atomic():
        for attempt in range(3):
            log = []
            with queries(log):
                source = timed(results, "source_copy", source_copy, person, listing)
            results.setdefault("source_copy_queries", []).append({
                "count": len(log), "db_seconds": sum(item[0] for item in log),
                "slowest": sorted(log, reverse=True)[:8],
            })
        from apps.safety.rights_source_fingerprint import source_fingerprint

        for _ in range(5):
            timed(results, "source_fingerprint", source_fingerprint, person, listing)
        profile = cProfile.Profile()
        profile.enable()
        source_copy(person, listing)
        profile.disable()
        output = io.StringIO()
        pstats.Stats(profile, stream=output).sort_stats("tottime").print_stats(25)
        results["source_copy_profile"] = output.getvalue()
        text = timed(results, "canonical_source", canonical, source)
        timed(results, "fingerprint_source", fingerprint, text)
        selection = {"revisions": [
            {"row": timed(results, "row_reference_each", row_reference, "revisions", index, row),
             "fields": PATHS}
            for index, row in enumerate(source["revisions"])
        ]}
        timed(results, "project_selected", project_selected, source, facts, selection)
        for name in facts:
            if facts[name]["status"] == "pending":
                facts[name] = dict(FACTS)
        omissions = {name: {} for name in facts}
        timed(results, "compile_coverage", compile_coverage, source, facts, selection, omissions,
              [], {}, allow_partial=True)
        ciphertext = seal({"selection": selection})
        results["selection_ciphertext_bytes"] = len(ciphertext)
        timed(results, "fingerprint_selection_ciphertext", fingerprint, ciphertext)
    summary = {key: (value if not isinstance(value, list) or not value or not isinstance(value[0], float)
                     else {"n": len(value), "total": sum(value), "max": max(value)})
               for key, value in results.items()}
    summary["source_bytes"] = len(text)
    record_property("source_profile", json.dumps(summary))
    record_property("scope", "One target subject; synthetic; in-process; diagnostic only")
