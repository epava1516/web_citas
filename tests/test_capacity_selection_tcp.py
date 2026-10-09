"""Finite real TCP selection-page probe; not full capacity acceptance."""

import cProfile
import http.cookiejar
import io
import json
import math
import pstats
import time
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from capacity_target_fixture import PATHS, populate
from django.conf import settings as runtime_settings
from django.db import connection, transaction
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import LegalAcceptance, User
from apps.safety.crypto import unseal
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not getattr(runtime_settings, "CAPACITY_ENVIRONMENT_VERIFIED", False),
                      reason="Requires owned capacity runner with verified kernel limits"),
]
REASON = "Measure independently inspected synthetic target page over actual TCP"


def prepare_target(request, settings, monkeypatch, live_server, identity, *,
                   independent_reviewer=False, include_binary=False, details=None):
    assert connection.vendor == "postgresql"
    request.getfixturevalue("directory")
    started = time.perf_counter()
    _, _, _, manifest = populate(identity)
    build_seconds = time.perf_counter() - started
    original = fixtures.ready

    def target_ready(*args, **kwargs):
        return original(*args, **(kwargs | {"subject_username": identity}))

    started = time.perf_counter()
    with monkeypatch.context() as patch:
        patch.setattr(fixtures, "ready", target_ready)
        case, author, baseline, previous, profile, subject, receipt = fixtures.prepared_selection(
            request, settings, patch, False
        )
    with transaction.atomic():
        locked, profile, listing = reviewer_case(author, case.pk)
        source = source_copy(profile, listing, locked)
    assert len(source["revisions"]) == 1500
    body = unseal(baseline.encrypted_selection)
    body["selection"]["revisions"] = [
        {"row": row_reference("revisions", index, row), "fields": PATHS}
        for index, row in enumerate(source["revisions"])
    ]
    row = save_selection(author, case.pk, case.version, baseline.assessment_review_id,
                         uuid4(), baseline.version, REASON, body["selection"],
                         field_evidence=body["field_evidence"])
    preparation_seconds = time.perf_counter() - started
    binary_operations = []
    if include_binary:
        from apps.safety.rights_portability_image_selection import prepare, save

        conditions = {
            "status": "eligible", "basis": "contract", "origin": "provided",
            "automated": True, "subject_related": True, "third_party_reviewed": True,
            "reason": REASON,
            "evidence": "Synthetic subject-provided target binary, independently reviewed before release",
        }
        for revision_index, revision in enumerate(source["revisions"]):
            for image_index, image in enumerate(revision["images"]):
                begin = time.perf_counter()
                page = prepare(author, case.pk, case.version, row.assessment_review_id,
                               uuid4(), REASON, revision_index, image_index)
                prepared_seconds = time.perf_counter() - begin
                assert page["declaration"]["photo"] == image["photo"]
                begin = time.perf_counter()
                row = save(author, uuid4(), page["token"], REASON, True, conditions)
                saved_seconds = time.perf_counter() - begin
                binary_operations.append({"photo": image["photo"],
                    "revision_index": revision_index, "image_index": image_index,
                    "content_digest": page["declaration"]["content_digest"],
                    "prepare_seconds": prepared_seconds, "save_seconds": saved_seconds})
                assert prepared_seconds <= 60 and saved_seconds <= 60
        binding = unseal(row.encrypted_selection)
        assert len(binding["images"]) == len(binary_operations) == 16
        assert len(binding["selection"]["revisions"]) == 1500
        assert all(set(item["fields"]) == set(PATHS)
                   for item in binding["selection"]["revisions"])
        assert {item["content_digest"] for item in binding["images"]} == {
            item["sha256"] for item in manifest["originals"]
        }
    reviewer = User.objects.get(pk=previous.action.actor_id)
    if independent_reviewer:
        from test_rights_verification import read

        previous_reviewer = reviewer
        reviewer = User.objects.create_user(username=identity + "-reviewer",
            email=identity + "-reviewer@example.invalid", role=previous_reviewer.role, mfa_enabled=True,
            email_verified_at=timezone.now())
        reviewer.user_permissions.set(previous_reviewer.user_permissions.all())
        LegalAcceptance.objects.bulk_create([
            LegalAcceptance(user=reviewer, document_id=item.document_id, action=item.action)
            for item in LegalAcceptance.objects.filter(user=previous_reviewer, agency__isnull=True)
        ])
    browser = Client()
    browser.force_login(reviewer)
    reviewer.refresh_from_db()
    session = browser.session
    session["mfa_version"] = reviewer.mfa_version
    session["account_version"] = reviewer.session_version
    session.save()
    if independent_reviewer:
        read(browser, case)
    cookies = http.cookiejar.CookieJar()
    host = urllib.parse.urlparse(live_server.url).hostname
    cookie_host = host if "." in host else host + ".local"
    cookies.set_cookie(http.cookiejar.Cookie(
        0, settings.SESSION_COOKIE_NAME, browser.cookies[settings.SESSION_COOKIE_NAME].value,
        None, False, cookie_host, False, False, "/", True, False, None, True, None, None, {}
    ))
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    path = f"/en/moderation/rights/{case.pk}/portability/selection/{row.pk}/review/"
    endpoint = live_server.url + path
    opened = time.perf_counter()
    with client.open(endpoint, timeout=60) as response:
        assert response.status == 200 and "no-store" in response.headers["Cache-Control"]
        response.read()
    first_open = time.perf_counter() - opened
    csrf = next(cookie.value for cookie in cookies if cookie.name == settings.CSRF_COOKIE_NAME)
    if details is not None:
        details.update(author=author, reviewer=reviewer, profile=profile, subject=subject,
                       receipt=receipt, binary_preparation_operations=binary_operations)
    return case, row, client, endpoint, csrf, manifest, build_seconds, preparation_seconds, first_open


@pytest.mark.usefixtures("photo_environment")
def test_target_selection_page_tcp(request, settings, monkeypatch, live_server, record_property):
    case, row, client, endpoint, csrf, manifest, build_seconds, preparation_seconds, first_open = prepare_target(
        request, settings, monkeypatch, live_server, "capacity-subject-a"
    )
    samples, sizes = [], []
    try:
        for _ in range(20):
            payload = urllib.parse.urlencode({"key": str(uuid4()), "version": case.version,
                                             "operation": "inspect", "reason": REASON, "page": 1}).encode()
            query = urllib.request.Request(endpoint, data=payload, headers={
                "Content-Type": "application/x-www-form-urlencoded", "Referer": endpoint,
                "X-CSRFToken": csrf,
            })
            opened = time.perf_counter()
            with client.open(query, timeout=60) as response:
                content = response.read()
                elapsed = time.perf_counter() - opened
                assert response.status == 200 and "no-store" in response.headers["Cache-Control"]
            samples.append(elapsed)
            sizes.append(len(content))
            from apps.safety.models import RightsPortabilitySelectionRead
            latest = RightsPortabilitySelectionRead.objects.filter(selection=row).latest("pk")
            assert latest.page_metadata["page"] == 1 and latest.page_metadata["size"] == 50
            assert latest.page_metadata["total"] == 1501
    finally:
        p95 = sorted(samples)[math.ceil(len(samples) * .95) - 1] if samples else None
        rss_kib = next(int(line.split()[1]) for line in Path("/proc/self/status").read_text().splitlines()
                       if line.startswith("VmHWM:"))
        record_property("selection_tcp_measurements", json.dumps({
            "samples": samples, "response_bytes": sizes, "p95_seconds": p95,
            "process_peak_rss_bytes": rss_kib * 1024,
            "rss_scope": "Linux VmHWM of pytest/application process through 20th complete TCP response; not cgroup memory or total environment",
            "first_open_seconds": first_open, "build_seconds": build_seconds,
            "preparation_seconds": preparation_seconds, "fixture": manifest,
            "scope": "One case, repeated page 1, real Django live_server TCP; no concurrency, page completion, approval, image selection or full capacity",
        }))
    from apps.safety import rights_portability_selection_views as selection_views

    profile = cProfile.Profile()
    original_record = selection_views.record

    def profiled_record(*args, **kwargs):
        profile.enable()
        try:
            return original_record(*args, **kwargs)
        finally:
            profile.disable()

    monkeypatch.setattr(selection_views, "record", profiled_record)
    diagnostic_payload = urllib.parse.urlencode({"key": str(uuid4()), "version": case.version,
                                                "operation": "inspect", "reason": REASON, "page": 1}).encode()
    diagnostic_query = urllib.request.Request(endpoint, data=diagnostic_payload, headers={
        "Content-Type": "application/x-www-form-urlencoded", "Referer": endpoint,
        "X-CSRFToken": csrf,
    })
    with client.open(diagnostic_query, timeout=60) as response:
        assert response.status == 200
        response.read()
    summary = io.StringIO()
    pstats.Stats(profile, stream=summary).sort_stats("cumulative").print_stats(35)
    record_property("selection_service_profile", summary.getvalue())
    assert rss_kib * 1024 <= 1024 ** 3, "Application process exceeds 1GiB RSS"
    assert len(samples) == 20
    assert p95 <= 2, f"Target page TCP p95 {p95:.3f}s exceeds 2s"
