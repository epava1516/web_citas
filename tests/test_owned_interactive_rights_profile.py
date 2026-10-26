"""Three finite normal-machine references; preparation and oracles are untimed."""

import hashlib
import json
import math
import os
import platform
import stat
from pathlib import Path
from time import perf_counter, process_time
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.db import connection
from django.utils import timezone
from test_complaint_resolutions import REASON as COMPLAINT_REASON
from test_complaint_resolutions import RESPONSE, inspection, listing_case
from test_processing_review import REASON as PROCESSING_REASON
from test_processing_review import prepared
from test_rectification_review import REASON as RECTIFICATION_REASON
from test_rectification_review import independent_case
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.complaint_resolutions import resolve, source_version
from apps.safety.crypto import digest, unseal
from apps.safety.erasure_inventory import canonical
from apps.safety.models import (
    ComplaintAction,
    ComplaintNotice,
    ComplaintResolution,
    ProcessingPlanRead,
    ProcessingPlanReview,
    RightsAction,
    RightsRectificationProposalRead,
    RightsRectificationReview,
    RightsRectificationSourceRead,
)
from apps.safety.processing_review import record
from apps.safety.rectification_review import inspect as inspect_proposal
from apps.safety.rectification_review import review as review_proposal
from apps.safety.rights import fingerprint
from apps.safety.rights_rectification import preview

pytestmark = pytest.mark.django_db(transaction=True)
PURPOSE = "Independently inspect current synthetic rights evidence for normal reference"


def _owned_serial(request, settings):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL interactive reference only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _digest(value):
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(body.encode()).hexdigest()


def _same(left, right):
    # Avoid putting private local values into assertion explanations or properties.
    assert _digest(left) == _digest(right)


def _state():
    result = {}
    for model in apps.get_models(include_auto_created=True):
        fields = [field.attname for field in model._meta.concrete_fields]
        pk_field = model._meta.pk.attname
        result[model._meta.label] = {
            row[pk_field]: row
            for row in model._base_manager.order_by("pk").values(*fields)
        }
    return result


def _snapshot_digest(state):
    # UUID primary keys stay local; JSON object keys must be strings.
    return _digest({label: list(rows.values()) for label, rows in state.items()})


def _assert_delta(before, after, *, additions=None, updates=None):
    additions, updates = additions or {}, updates or {}
    _same(sorted(before), sorted(after))
    for label, original in before.items():
        current = after[label]
        expected_new = additions.get(label, set())
        assert set(current) - set(original) == expected_new
        assert not set(original) - set(current)
        for pk, row in original.items():
            expected = row | updates.get((label, pk), {})
            _same(current[pk], expected)
    # Every declared new record/updated parent must exist in the full snapshot.
    for label, pks in additions.items():
        assert label in before and pks <= set(after[label])
    for label, pk in updates:
        assert pk in before[label] and pk in after[label]


def _new(model, before):
    label = model._meta.label
    added = list(model._base_manager.exclude(pk__in=before[label]).order_by("pk"))
    assert len(added) == 1
    return added[0]


def _files(settings):
    root, rows = Path(settings.MEDIA_ROOT), []
    if root.exists():
        for path in sorted(root.rglob("*")):
            assert not path.is_symlink()
            if path.is_file():
                metadata = path.stat()
                body_hash = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(65536), b""):
                        body_hash.update(chunk)
                rows.append((str(path.relative_to(root)), metadata.st_size,
                             metadata.st_mtime_ns, stat.S_IMODE(metadata.st_mode),
                             body_hash.hexdigest()))
    return {"count": len(rows), "sha256": _digest(rows)}


def _session(client, user):
    session = client.session
    session["mfa_version"] = user.mfa_version
    session["account_version"] = user.session_version
    session.save()


def _measure(observed, group, index, call, *, http=False, consume=None):
    metric = {"group": group, "sample": "first" if index == 0 else "followup",
              "followup_index": index, "sql_calls": 0, "sql_elapsed_ms": 0.0}

    def forward(execute, sql, params, many, context):
        started = perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            metric["sql_calls"] += 1
            metric["sql_elapsed_ms"] += (perf_counter() - started) * 1000

    cpu_started, wall_started = process_time(), perf_counter()
    with connection.execute_wrapper(forward):
        result = call()
        if http:
            assert not result.streaming
            body = bytes(result.content)
            metric.update(http_status=result.status_code, http_bytes=len(body))
    metric.update(wall_ms=(perf_counter() - wall_started) * 1000,
                  process_cpu_ms=(process_time() - cpu_started) * 1000)
    if consume is not None:
        # These native results are eager DTOs/models. Verify/serialize them untimed.
        _digest(consume(result))
    assert metric["wall_ms"] > 0 and metric["process_cpu_ms"] >= 0
    assert metric["sql_calls"] > 0 and metric["sql_elapsed_ms"] >= 0
    assert all(math.isfinite(metric[key]) for key in
               ("wall_ms", "process_cpu_ms", "sql_elapsed_ms"))
    observed["measurements"].append(metric)
    return result


def _resources():
    result = {"machine": platform.machine(), "logical_cpus": os.cpu_count(),
              "scope": "Single premeasurement observation; no host-load isolation claim"}
    for name, filename in {
        "cpu_max": "/sys/fs/cgroup/cpu.max",
        "memory_max": "/sys/fs/cgroup/memory.max",
        "memory_swap_max": "/sys/fs/cgroup/memory.swap.max",
        "cpuset_effective": "/sys/fs/cgroup/cpuset.cpus.effective",
    }.items():
        path = Path(filename)
        result[name] = path.read_text().strip() if path.is_file() else None
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        result["cpu_model"] = next((line.split(":", 1)[1].strip()
                                    for line in cpuinfo.read_text().splitlines()
                                    if line.startswith("model name")), None)
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        result["memory_total_kib"] = next((int(line.split()[1])
                                           for line in meminfo.read_text().splitlines()
                                           if line.startswith("MemTotal:")), None)
    return result


def _profile(workflow):
    return {"workflow": workflow, "resources": _resources(), "baseline": "normal native machine stage; no candidate",
            "measurements": [], "oracles_complete": False,
            "limits": "Synthetic native readiness; Client GET or native service; no socket, worker, "
                      "human, provider, p95, SLA, or full-workflow latency claim. "
                      "Snapshots/preparation/assertions excluded; SQL overlaps wall; warmed fixture. "
                      "SQL counts only driver-exposed execute calls; CPU excludes PostgreSQL server."}


def _publish(record_property, observed):
    record_property("owned_interactive_rights_profile", json.dumps(
        observed, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ))


def _queues(observed, client, kind, expected, phase):
    context_key = "cases" if kind == "rights" else "complaints"
    headings = {
        "rights": {"es": "Cola privada de derechos", "en": "Private rights queue"},
        "complaints": {"es": "Cola privada de reclamaciones", "en": "Private review requests"},
    }
    for language in ("es", "en"):
        baseline = _state()
        path = f"/{language}/moderation/{kind}/"
        for index in range(6):
            response = _measure(observed, f"{phase}_{language}", index,
                                lambda: client.get(path), http=True)
            try:
                assert response.status_code == 200
                assert response.get("Cache-Control") == "private, no-store"
                assert response.get("X-Robots-Tag") == "noindex, nofollow"
                assert response.get("Content-Language") == language
                assert response.wsgi_request.LANGUAGE_CODE == language
                assert headings[kind][language].encode() in response.content
                _same([row.pk for row in response.context[context_key]], expected)
            finally:
                response.close()
        _assert_delta(baseline, _state())


def _replays(observed, group, call, check, *, consume=None):
    baseline = _state()
    for index in range(6):
        result = _measure(observed, group, index, call, consume=consume)
        check(result)
    _assert_delta(baseline, _state())


def _action(action, case, actor, key, version, operation, reason, signature, began, ended):
    valid = (action.request_id == case.pk and action.actor_id == actor.pk
             and action.key == key and action.expected_version == version
             and action.operation == operation and action.payload_digest == signature
             and action.purged_at is None and action.final_response_id is None
             and action.clarification_prompt == "" and began <= action.created_at <= ended)
    assert valid
    _same(unseal(action.encrypted_reason), {"reason": reason})


def test_owned_processing_plan_normal_reference(request, settings, monkeypatch, record_property):
    _owned_serial(request, settings)
    observed = _profile("processing_plan")
    try:
        case, _, _, plan, reviewer, client = prepared(request, settings, monkeypatch)
        _session(client, reviewer)
        case.refresh_from_db()
        version = case.version
        expected_body = unseal(plan.encrypted_plan)
        assert expected_body["enforced"] is False and expected_body["partial"] is True
        assert all(row["operation"] == "continue" for row in expected_body["decisions"])
        before_all, files_before = _state(), _files(settings)
        _queues(observed, client, "rights", [case.pk], "rights_queue")
        additions = {}
        for operation in ("inspect", "review"):
            key, before = uuid4(), _state()
            outcome = "approved" if operation == "review" else ""

            def call():
                return record(reviewer, case.pk, plan.pk, key, version,
                              operation, PROCESSING_REASON, outcome)

            began = timezone.now()
            result, body = _measure(observed, f"processing_{operation}_new", 0, call,
                                    consume=lambda value: [value[0].pk, value[1]])
            ended = timezone.now()
            model = ProcessingPlanRead if operation == "inspect" else ProcessingPlanReview
            row, action = _new(model, before), _new(RightsAction, before)
            signature = fingerprint(canonical({
                "plan": str(plan.pk), "version": version, "operation": operation,
                "reason": PROCESSING_REASON, "outcome": outcome,
                "plan_digest": fingerprint(plan.encrypted_plan),
            }))
            _action(action, case, reviewer, key, version, "processing_" + operation,
                    PROCESSING_REASON, signature, began, ended)
            valid = (result.pk == row.pk and row.action_id == action.pk
                     and row.plan_id == plan.pk and row.proof_id == plan.proof_id
                     and row.plan_digest == fingerprint(plan.encrypted_plan)
                     and row.source_digest == plan.source_digest
                     and began <= row.created_at <= ended)
            assert valid
            if operation == "inspect":
                _same(body, expected_body)
            else:
                assert body is None and row.outcome == "approved"
            stage_added = {RightsAction._meta.label: {action.pk}, model._meta.label: {row.pk}}
            _assert_delta(before, _state(), additions=stage_added)
            for label, pks in stage_added.items():
                additions.setdefault(label, set()).update(pks)

            def check(value):
                assert value[0].pk == row.pk
                _same(value[1], expected_body if operation == "inspect" else None)

            _replays(observed, f"processing_{operation}_replay", call, check,
                     consume=lambda value: [value[0].pk, value[1]])
        _assert_delta(before_all, _state(), additions=additions)
        files_after = _files(settings)
        _same(files_before, files_after)
        observed["integrity"] = {"snapshot_before_sha256": _snapshot_digest(before_all),
                                 "snapshot_after_sha256": _snapshot_digest(_state()),
                                 "installed_models": len(before_all),
                                 "files_before": files_before, "files_after": files_after}
        assert len(observed["measurements"]) == 26
        assert len({row["group"] for row in observed["measurements"]}) == 6
        observed.update(oracles_complete=True, groups=6, observations=26,
                        exact_new_actions=2, exact_new_reads=1, exact_new_reviews=1,
                        parent_rows_unchanged=True, files_unchanged=True)
    finally:
        _publish(record_property, observed)


def test_owned_rectification_normal_reference(request, settings, monkeypatch, record_property):
    _owned_serial(request, settings)
    observed = _profile("rectification")
    try:
        case, reviewer, client, person, proposal, _ = independent_case(
            request, settings, monkeypatch,
        )
        _session(client, reviewer)
        case.refresh_from_db()
        version = case.version
        expected_changes = {"alias": "Synthetic reviewed correction"}
        _same(unseal(proposal.encrypted_changes), expected_changes)
        before_all, files_before = _state(), _files(settings)
        began = timezone.now()
        source = _measure(observed, "rectification_source_preview", 0,
                          lambda: preview(reviewer, case.pk, version, PURPOSE),
                          consume=lambda value: value)
        ended = timezone.now()
        _same(source["alias"], person.alias)
        source_read = _new(RightsRectificationSourceRead, before_all)
        valid = (source_read.request_id == case.pk and source_read.actor_id == reviewer.pk
                 and source_read.case_version == version and source_read.purpose == PURPOSE
                 and source_read.source_digest == proposal.source_digest
                 and began <= source_read.created_at <= ended)
        assert valid
        additions = {RightsRectificationSourceRead._meta.label: {source_read.pk}}
        _assert_delta(before_all, _state(), additions=additions)
        before = _state()
        began = timezone.now()
        changes = _measure(observed, "rectification_proposal_inspect", 0,
                           lambda: inspect_proposal(reviewer, case.pk, proposal.pk,
                                                    version, PURPOSE),
                           consume=lambda value: value)
        ended = timezone.now()
        _same(changes, expected_changes)
        read = _new(RightsRectificationProposalRead, before)
        changes_digest = fingerprint(json.dumps(expected_changes, sort_keys=True))
        valid = (read.proposal_id == proposal.pk and read.actor_id == reviewer.pk
                 and read.case_version == version and read.proof_id == source_read.proof_id
                 and read.changes_digest == changes_digest and read.purpose == PURPOSE
                 and began <= read.created_at <= ended)
        assert valid
        _assert_delta(before, _state(), additions={read._meta.label: {read.pk}})
        additions[read._meta.label] = {read.pk}
        before, key = _state(), uuid4()

        def call():
            return review_proposal(reviewer, case.pk, proposal.pk, key, version,
                                   "approved", RECTIFICATION_REASON)

        began = timezone.now()
        result = _measure(observed, "rectification_review_new", 0, call,
                          consume=lambda value: value.pk)
        ended = timezone.now()
        review, action = _new(RightsRectificationReview, before), _new(RightsAction, before)
        signature = fingerprint(json.dumps({
            "proposal": proposal.pk, "version": version, "outcome": "approved",
            "reason": RECTIFICATION_REASON,
        }, sort_keys=True))
        _action(action, case, reviewer, key, version, "rectify_review",
                RECTIFICATION_REASON, signature, began, ended)
        valid = (result.pk == review.pk and review.action_id == action.pk
                 and review.proposal_id == proposal.pk and review.proof_id == read.proof_id
                 and review.outcome == "approved" and review.changes_digest == changes_digest
                 and began <= review.created_at <= ended)
        assert valid
        stage_added = {review._meta.label: {review.pk}, action._meta.label: {action.pk}}
        updates = {(case._meta.label, case.pk): {"version": version + 1,
                                               "scope_status": "unverified"}}
        _assert_delta(before, _state(), additions=stage_added, updates=updates)
        additions.update(stage_added)

        def check(value):
            assert value.pk == review.pk

        _replays(observed, "rectification_review_replay", call, check,
                 consume=lambda value: value.pk)
        _assert_delta(before_all, _state(), additions=additions, updates=updates)
        files_after = _files(settings)
        _same(files_before, files_after)
        observed["integrity"] = {"snapshot_before_sha256": _snapshot_digest(before_all),
                                 "snapshot_after_sha256": _snapshot_digest(_state()),
                                 "installed_models": len(before_all),
                                 "files_before": files_before, "files_after": files_after}
        assert len(observed["measurements"]) == 9
        assert len({row["group"] for row in observed["measurements"]}) == 4
        observed.update(oracles_complete=True, groups=4, observations=9,
                        exact_new_source_reads=1, exact_new_proposal_reads=1,
                        exact_new_actions=1, exact_new_reviews=1,
                        profile_publication_unchanged=True, files_unchanged=True)
    finally:
        _publish(record_property, observed)


def test_owned_complaint_normal_reference(request, settings, record_property):
    _owned_serial(request, settings)
    observed = _profile("complaint")
    try:
        complaint, _, target, actor, client, _ = listing_case(request, rejected=False)
        _session(client, actor)
        complaint.refresh_from_db()
        # Native audited evidence/image reads are readiness, never resolve timing.
        response = inspection(client, complaint)
        try:
            assert response.status_code == 200
        finally:
            response.close()
        complaint.refresh_from_db()
        version, original_source = complaint.version, source_version(complaint)
        before_all, files_before = _state(), _files(settings)
        _queues(observed, client, "complaints", [complaint.pk], "complaint_queue_open")
        before, key = _state(), uuid4()

        def call():
            return resolve(actor, complaint.pk, key, version, original_source, "upheld",
                           COMPLAINT_REASON, RESPONSE, True)

        began = timezone.now()
        result = _measure(observed, "complaint_resolve_new", 0, call,
                          consume=lambda value: [value.pk, value.status, value.version])
        ended = timezone.now()
        action, resolution = _new(ComplaintAction, before), _new(ComplaintResolution, before)
        notice = _new(ComplaintNotice, before)
        signature = digest(json.dumps({
            "version": version, "source_version": original_source, "outcome": "upheld",
            "reason": COMPLAINT_REASON, "response": RESPONSE, "redaction_confirmed": True,
        }, sort_keys=True))
        valid = (result.pk == complaint.pk and result.status == "resolved"
                 and result.version == version + 1 and action.key == key
                 and action.complaint_id == complaint.pk and action.actor_id == actor.pk
                 and action.expected_version == version and action.operation == "resolve"
                 and action.payload_digest == signature and began <= action.created_at <= ended
                 and resolution.complaint_id == complaint.pk and resolution.action_id == action.pk
                 and resolution.outcome == "upheld" and began <= resolution.created_at <= ended
                 and notice.resolution_id == resolution.pk and notice.status == "queued"
                 and notice.attempts == 0 and notice.recovery_version == 0
                 and notice.next_attempt_at is None and notice.simulated_at is None
                 and notice.error_code == "" and began <= notice.created_at <= ended)
        assert valid
        _same(unseal(action.encrypted_reason), {"reason": COMPLAINT_REASON})
        _same(unseal(resolution.encrypted_response), {"response": RESPONSE})
        payload = unseal(notice.encrypted_payload)
        _same(payload, {
            "recipient": "own-channel@example.invalid",
            "subject": "Respuesta a reclamación / Review response",
            "body": "Hay una respuesta disponible. Consulta tu enlace privado de seguimiento. / "
                    "A response is available. Consult your private receipt link.",
        })
        additions = {action._meta.label: {action.pk}, resolution._meta.label: {resolution.pk},
                     notice._meta.label: {notice.pk}}
        updates = {(complaint._meta.label, complaint.pk): {"status": "resolved",
                                                         "version": version + 1}}
        _assert_delta(before, _state(), additions=additions, updates=updates)

        def check(value):
            assert value.pk == complaint.pk and value.status == "resolved"
            assert value.version == version + 1

        _replays(observed, "complaint_resolve_replay", call, check,
                 consume=lambda value: [value.pk, value.status, value.version])
        _queues(observed, client, "complaints", [], "complaint_queue_resolved")
        _assert_delta(before_all, _state(), additions=additions, updates=updates)
        # All source decision/revision/listing records are covered by the full snapshot.
        assert target.pk in before_all[target._meta.label]
        files_after = _files(settings)
        _same(files_before, files_after)
        observed["integrity"] = {"snapshot_before_sha256": _snapshot_digest(before_all),
                                 "snapshot_after_sha256": _snapshot_digest(_state()),
                                 "installed_models": len(before_all),
                                 "files_before": files_before, "files_after": files_after}
        assert len(observed["measurements"]) == 31
        assert len({row["group"] for row in observed["measurements"]}) == 6
        observed.update(oracles_complete=True, groups=6, observations=31,
                        exact_new_actions=1, exact_new_resolutions=1, exact_new_notices=1,
                        source_publication_unchanged=True, files_unchanged=True)
    finally:
        _publish(record_property, observed)
