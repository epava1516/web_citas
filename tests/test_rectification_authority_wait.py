"""Opt-in owned PostgreSQL diagnostics. Only source_photo is HTTP.

Forwarding counters observe successful private helper returns, not every internal
projection. Eager callback execution is not broker/worker evidence.
"""
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connection, connections, transaction
from django.test import Client
from test_operational_recovery_authority_wait import _snapshot
from test_photos import raw_image
from test_privacy_release import fresh
from test_rectification_review import independent_case
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import User
from apps.mediafiles.tasks import process_blob
from apps.safety import (
    rectification_account,
    rectification_execution,
    rectification_recipients,
    rectification_review,
    rectification_uploads,
    rights_rectification,
)
from apps.safety.models import (
    RightsAction,
    RightsRectificationExecution,
    RightsRectificationNotification,
    RightsRectificationPhotoUpload,
    RightsRectificationProposal,
    RightsRectificationProposalRead,
    RightsRectificationRecipientInventory,
    RightsRectificationReview,
    RightsRectificationSourceRead,
)

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independent synthetic correction grounds after an owned resource wait"
PURPOSE = "Inspect current synthetic rectification source and proposed changes"
CORRECTION = "Synthetic reviewed correction"
FAMILIES = (
    "preview", "propose", "source_photo", "upload", "discard", "inspect", "review",
    "notify", "execute", "recipients",
)


def _owned_serial(request, settings):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL rectification diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _client(actor):
    client = Client()
    client.force_login(actor)
    session = client.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    return client


def _grant(actor, codename):
    actor.user_permissions.add(Permission.objects.get(
        content_type__app_label="safety", codename=codename,
    ))
    return User.objects.get(pk=actor.pk)


def _source(actor, case):
    value = rights_rectification.preview(actor, case.pk, case.version, PURPOSE)
    assert isinstance(value, dict)


def _read_changes(actor, case, proposal):
    _source(actor, case)
    value = rectification_review.inspect(actor, case.pk, proposal.pk, case.version, PURPOSE)
    matches_expected = value == {"alias": CORRECTION}
    assert matches_expected


def _new_image():
    return SimpleUploadedFile("synthetic-input.jpg", raw_image(991), content_type="image/jpeg")


def _prepare(request, settings, monkeypatch, family):
    if family in {"preview", "propose", "source_photo", "upload", "discard"}:
        case, actor, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
        assert case.kind == "rectify" and person.subject_id != actor.pk
        _source(actor, case)
        prepared = dict(case=case, actor=actor, person=person, client=staff)
        if family in {"source_photo", "upload", "discard"}:
            item = rectification_uploads.upload(
                actor, case.pk, uuid4(), case.version, _new_image(), REASON,
            )
            item.photo.refresh_from_db()
            blob = item.photo.blob
            assert blob.status == "ready" and bool(blob.derivative)
            _source(actor, case)
            prepared.update(item=item, blob=blob)
        if family == "preview":
            held = person.subject
            boundary = "subject_User_in_account_source_before_private_account_return"
        elif family == "propose":
            held, boundary = case, "canonical_RightsRequest_before_validated_changes"
        elif family in {"source_photo", "upload"}:
            held = prepared["blob"]
            boundary = "source_snapshot_Blob_batch_before_snapshot_return"
        else:
            held = prepared["item"]
            boundary = "source_snapshot_active_Upload_batch_before_explicit_discard_lock"
        prepared.update(held=held, boundary=boundary,
                        permission="safety.execute_rights_request")
        return prepared

    case, actor, other, person, proposal, _, recipient, receipt = independent_case(
        request, settings, monkeypatch, with_receipt=True, changes={"alias": CORRECTION},
    )
    assert case.kind == "rectify" and proposal.action.actor_id != actor.pk
    _source(actor, case)
    prepared = dict(case=case, actor=actor, client=other, person=person, proposal=proposal,
                    permission="safety.review_rectification")
    if family in {"inspect", "review"}:
        if family == "review":
            _read_changes(actor, case, proposal)
        prepared.update(held=proposal, boundary="current_Proposal_before_source_and_unseal")
        return prepared
    actor = _grant(actor, "respond_rights_request")
    prepared["actor"] = actor
    _read_changes(actor, case, proposal)
    reviewed = rectification_review.review(
        actor, case.pk, proposal.pk, uuid4(), case.version, "approved", REASON,
    )
    original = User.objects.get(pk=proposal.action.actor_id)
    original_client = _client(original)
    fresh(case, actor, other, original, original_client)
    _read_changes(actor, case, proposal)
    if family == "notify":
        prepared.update(held=reviewed, boundary="Review_after_current_and_unseal_before_issue")
        return prepared
    notified = rectification_execution.notify(
        actor, case.pk, proposal.pk, uuid4(), case.version, REASON,
    )
    response = recipient.post(
        receipt + f"response/{notified.response_id}/acknowledge/", {"received": "yes"},
    )
    assert response.status_code == 302
    assert notified.response.receipt_acknowledgement.channel_digest == case.receipt_digest
    fresh(case, actor, other, original, original_client)
    _read_changes(actor, case, proposal)
    if family == "execute":
        prepared.update(held=notified,
                        boundary="Notification_after_current_before_correction_writes")
        return prepared
    applied = rectification_execution.execute(
        actor, case.pk, proposal.pk, uuid4(), case.version, REASON,
    )
    fresh(case, actor, other, original, original_client)
    prepared.update(execution=applied, held=case,
                    boundary="canonical_RightsRequest_before_executed_scope_and_inventory")
    return prepared


def _queries(actor, permission):
    """All scalar domain/through rows, omitting only the changed permission grant."""
    queries = {}
    for label in ("core", "listings", "mediafiles", "safety"):
        for model in apps.get_app_config(label).get_models(include_auto_created=True):
            query = model.objects.all()
            if model is User.user_permissions.through:
                query = query.exclude(user_id=actor.pk, permission_id=permission.pk)
            queries[model._meta.label] = query
    return queries


def _files(settings):
    root, manifest = Path(settings.MEDIA_ROOT), []
    if root.exists():
        for path in sorted(root.rglob("*")):
            assert not path.is_symlink()
            if path.is_file():
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(65536), b""):
                        digest.update(chunk)
                manifest.append((str(path.relative_to(root)), path.stat().st_size, digest.hexdigest()))
    canonical = json.dumps(manifest, separators=(",", ":")).encode()
    return {"count": len(manifest), "sha256": hashlib.sha256(canonical).hexdigest()}


def _state(case, person):
    case.refresh_from_db()
    person.refresh_from_db()
    listing = person.listing
    listing.refresh_from_db()
    return {
        "case_version": case.version, "response_version": case.response_version,
        "case_status": case.status, "scope_status": case.scope_status,
        "person_rights_version": person.rights_version,
        "listing_status": listing.status, "listing_lifecycle_version": listing.lifecycle_version,
        "approved_revision": str(listing.approved_revision_id),
    }


def _invoke(prepared, family, actor, key, observed):
    case, person = prepared["case"], prepared["person"]
    if family == "preview":
        result = rights_rectification.preview(actor, case.pk, case.version, PURPOSE)
        matches_expected = result["alias"] == person.alias
        assert matches_expected
    elif family == "propose":
        result = rights_rectification.propose(
            actor, case.pk, key, case.version, {"alias": CORRECTION}, REASON,
        )
        assert result.action.key == key
    elif family == "source_photo":
        path = (f"/en/moderation/rights/{case.pk}/rectification/photos/"
                f"{prepared['item'].photo_id}/")
        response = prepared["client"].get(path)
        try:
            observed["http_status"] = response.status_code
            observed["response_private"] = response.get("Cache-Control") == "private, no-store"
            if response.status_code == 200:
                assert response.streaming
                digest = hashlib.sha256()
                for chunk in response.streaming_content:
                    observed["private_stream_bytes"] += len(chunk)
                    assert observed["private_stream_bytes"] <= 8 * 1024 * 1024
                    digest.update(chunk)
                observed["private_stream_sha256"] = digest.hexdigest()
            if response.status_code == 403:
                observed["http_denial_normalized_to_service_exception"] = True
                raise PermissionDenied
            assert response.status_code == 200 and observed["response_private"]
        finally:
            response.close()
            observed["response_closed"] = response.closed
    elif family == "upload":
        item = rectification_uploads.upload(
            actor, case.pk, key, case.version, _new_image(), REASON,
        )
        assert item.action.key == key and item.photo.revision.status == "rights-stage"
    elif family == "discard":
        rectification_uploads.discard(
            actor, case.pk, key, case.version, prepared["item"].photo_id, REASON,
        )
    elif family == "inspect":
        changes = rectification_review.inspect(
            actor, case.pk, prepared["proposal"].pk, case.version, PURPOSE,
        )
        matches_expected = changes == {"alias": CORRECTION}
        assert matches_expected
    elif family == "review":
        result = rectification_review.review(
            actor, case.pk, prepared["proposal"].pk, key, case.version, "approved", REASON,
        )
        assert result.action.key == key and result.outcome == "approved"
    elif family in {"notify", "execute"}:
        result = getattr(rectification_execution, family)(
            actor, case.pk, prepared["proposal"].pk, key, case.version, REASON,
        )
        assert result.action.key == key
    else:
        assert family == "recipients"
        result = rectification_recipients.prepare(
            actor, case.pk, prepared["execution"].pk, key, case.version, PURPOSE,
        )
        assert result.action.key == key and result.execution_id == prepared["execution"].pk


def _observe_helpers(monkeypatch, revoked, observed):
    def observe(label, original):
        def forward(*args, **kwargs):
            observed[label + "_calls"] += 1
            if revoked.is_set():
                observed[label + "_calls_after_revocation"] += 1
            result = original(*args, **kwargs)
            observed[label + "_returns"] += 1
            if revoked.is_set():
                observed[label + "_returns_after_revocation"] += 1
            return result
        return forward

    monkeypatch.setattr(rectification_account, "source", observe(
        "account_source", rectification_account.source,
    ))
    snapshot = observe("source_snapshot", rights_rectification.source_snapshot)
    monkeypatch.setattr(rights_rectification, "source_snapshot", snapshot)
    # current imported an alias; both wrappers forward the same real implementation.
    monkeypatch.setattr(rectification_review, "source_snapshot", snapshot)
    monkeypatch.setattr(process_blob, "delay", observe("process_blob_delay", process_blob.delay))


def _positive_effects(prepared, family, key, before, after, observed):
    case, person = prepared["case"], prepared["person"]
    state_before, state_after = observed["minimal_before"], observed["minimal_after"]
    version_delta = 1 if family in {"propose", "review", "notify", "execute"} else 0
    response_delta = 1 if family in {"notify", "execute"} else 0
    assert state_after["case_version"] == state_before["case_version"] + version_delta
    assert state_after["response_version"] == state_before["response_version"] + response_delta
    if response_delta:
        for label in ("safety.RightsResponse", "safety.RightsNotice"):
            assert after["tables"][label]["count"] == before["tables"][label]["count"] + 1
    models = {
        "preview": RightsRectificationSourceRead, "propose": RightsRectificationProposal,
        "upload": RightsRectificationPhotoUpload, "inspect": RightsRectificationProposalRead,
        "review": RightsRectificationReview, "notify": RightsRectificationNotification,
        "execute": RightsRectificationExecution, "recipients": RightsRectificationRecipientInventory,
    }
    if family in models:
        label = models[family]._meta.label
        assert after["tables"][label]["count"] == before["tables"][label]["count"] + 1
    if family not in {"preview", "source_photo", "inspect"}:
        operations = {
            "propose": "rectify_plan", "upload": "rectify_photo_upload",
            "discard": "rectify_img_discard", "review": "rectify_review",
            "notify": "rectify_notify", "execute": "rectify_execute",
            "recipients": "rectify_recipients",
        }
        assert RightsAction.objects.filter(
            key=key, actor_id=prepared["actor"].pk, request=case,
            operation=operations[family],
        ).count() == 1
    if family == "source_photo":
        assert after == before and state_after == state_before
        assert observed["http_status"] == 200 and observed["private_stream_bytes"] > 0
    elif family == "discard":
        prepared["item"].refresh_from_db()
        assert prepared["item"].discarded_at is not None
    elif family == "execute":
        person.refresh_from_db()
        alias_matches = person.alias == CORRECTION
        assert alias_matches
        assert state_after["person_rights_version"] == state_before["person_rights_version"] + 1
        assert state_after["listing_lifecycle_version"] == state_before["listing_lifecycle_version"] + 1
        assert state_after["listing_status"] == "paused"
    if family in {"upload", "execute"}:
        assert observed["process_blob_delay_returns"] > 0
    else:
        assert observed["process_blob_delay_calls"] == 0


def _exercise(prepared, family, change, monkeypatch, settings, observed):
    actor, held = prepared["actor"], prepared["held"]
    permission_name = prepared["permission"]
    permission = Permission.objects.get(
        content_type__app_label="safety", codename=permission_name.split(".")[1],
    )
    assert actor.user_permissions.filter(pk=permission.pk).exists()
    assert User.objects.get(pk=actor.pk).has_perm(permission_name)
    queries = _queries(actor, permission)
    before, files_before = _snapshot(queries), _files(settings)
    observed.update(domain_before=before, files_before=files_before,
                    minimal_before=_state(prepared["case"], prepared["person"]),
                    boundary=prepared["boundary"], held_model=held._meta.label,
                    permission=permission_name, initial_permission=True)
    key, revoked, statement = uuid4(), Event(), Event()
    _observe_helpers(monkeypatch, revoked, observed)
    runtime = {}
    pool = ThreadPoolExecutor(max_workers=1)
    future = None

    def worker():
        close_old_connections()

        def observe_statement(execute, sql, params, many, context):
            text = str(sql).upper()
            target = 'FROM "' + held._meta.db_table.upper() + '"'
            if "FOR UPDATE" in text and target in text and not statement.is_set():
                raw = context["connection"].connection
                runtime.update(pid=raw.info.backend_pid, raw=raw)
                observed["first_target_statement_seconds"] = time.monotonic() - observed["_started"]
                statement.set()
            return execute(sql, params, many, context)

        try:
            fresh_actor = User.objects.get(pk=actor.pk)
            assert fresh_actor.mfa_enabled and fresh_actor.is_active
            assert fresh_actor.has_perm(permission_name)
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout TO '35s'")
            with connection.execute_wrapper(observe_statement):
                try:
                    _invoke(prepared, family, fresh_actor, key, observed)
                except PermissionDenied:
                    observed["status"] = "PermissionDenied"
                else:
                    observed["status"] = "success"
        except Exception as error:
            observed["status"] = "unexpected:" + type(error).__name__
            raise
        finally:
            connections.close_all()
            observed["connections_closed"] = all(alias.connection is None for alias in connections.all())

    try:
        try:
            with transaction.atomic():
                type(held).objects.select_for_update().get(pk=held.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                observed["holder_pid"] = holder
                future = pool.submit(worker)
                deadline = time.monotonic() + 15
                while True:
                    assert not future.done(), "Operation finished before observed PostgreSQL wait"
                    if statement.is_set():
                        assert runtime["pid"] != holder
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT pg_stat_clear_snapshot()")
                            cursor.execute(
                                "SELECT wait_event_type, pg_blocking_pids(pid) "
                                "FROM pg_stat_activity WHERE pid=%s", [runtime["pid"]],
                            )
                            waiting = cursor.fetchone()
                        if waiting and waiting[0] == "Lock" and holder in waiting[1]:
                            observed.update(actual_wait=True, worker_pid=runtime["pid"],
                                            blocker_pids=list(waiting[1]))
                            break
                    assert time.monotonic() < deadline, "Owned PostgreSQL wait absent after15s"
                    time.sleep(.02)
                if change == "permission":
                    actor.user_permissions.remove(permission)
                    still_allowed = User.objects.get(pk=actor.pk).has_perm(permission_name)
                    assert not still_allowed
                    observed["permission_revoked"] = True
                    # Worker stays blocked until this transaction commits grant removal.
                    revoked.set()
        finally:
            observed["holder_released"] = not connection.in_atomic_block
            if future is not None:
                try:
                    future.result(timeout=45)
                except FutureTimeoutError:
                    observed["worker_timeout"] = True
                    raw = runtime.get("raw")
                    if raw is not None and not raw.closed and raw.info.backend_pid == runtime.get("pid"):
                        raw.cancel()
                    try:
                        future.result(timeout=5)
                    except Exception as error:
                        observed["cleanup_exception_type"] = type(error).__name__
                    raise
        after = _snapshot(queries)
        observed.update(domain_after=after, files_after=_files(settings),
                        minimal_after=_state(prepared["case"], prepared["person"]))
        assert observed["actual_wait"]
        if change == "permission":
            assert observed["status"] == "PermissionDenied"
            assert after == before
            assert observed["minimal_after"] == observed["minimal_before"]
            assert observed["files_after"] == files_before
            assert observed["account_source_returns_after_revocation"] == 0
            assert observed["source_snapshot_returns_after_revocation"] == 0
            assert observed["process_blob_delay_calls"] == 0
            assert observed["private_stream_bytes"] == 0
        else:
            assert observed["status"] == "success"
            _positive_effects(prepared, family, key, before, after, observed)
            # All image inputs reuse a native prepared ready Blob; no new bytes expected.
            assert observed["files_after"] == files_before
    finally:
        pool.shutdown(wait=future is None or future.done(), cancel_futures=True)
        observed["thread_finished"] = future is None or future.done()
        observed["domain_after"] = _snapshot(queries)
        observed["files_after"] = _files(settings)
        observed["minimal_after"] = _state(prepared["case"], prepared["person"])
    assert observed["thread_finished"] and observed["connections_closed"] and observed["holder_released"]
    if family == "source_photo":
        assert observed["response_closed"]


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("change", ["valid", "permission"])
def test_native_rectification_authority_after_owned_wait(
    request, settings, monkeypatch, record_property, family, change,
):
    observed = {
        "label": family + ":" + change, "status": "not_started", "actual_wait": False,
        "blocker_pids": [], "permission_revoked": False, "thread_finished": True,
        "connections_closed": True, "holder_released": True, "response_closed": False,
        "http_denial_normalized_to_service_exception": False,
        "private_stream_bytes": 0, "account_source_calls": 0,
        "account_source_calls_after_revocation": 0, "account_source_returns": 0,
        "account_source_returns_after_revocation": 0, "source_snapshot_calls": 0,
        "source_snapshot_calls_after_revocation": 0, "source_snapshot_returns": 0,
        "source_snapshot_returns_after_revocation": 0, "process_blob_delay_calls": 0,
        "process_blob_delay_calls_after_revocation": 0, "process_blob_delay_returns": 0,
        "process_blob_delay_returns_after_revocation": 0,
        "surface": "HTTP_GET" if family == "source_photo" else "native_service",
        "projection_oracle": "successful helper returns only; internal projections not exhaustively observed",
        "_started": time.monotonic(),
    }
    try:
        _owned_serial(request, settings)
        prepared = _prepare(request, settings, monkeypatch, family)
        _exercise(prepared, family, change, monkeypatch, settings, observed)
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["elapsed_seconds_including_setup_wait_cleanup"] = time.monotonic() - observed.pop("_started")
        record_property("rectification_authority_wait", json.dumps(observed, allow_nan=False, sort_keys=True))
