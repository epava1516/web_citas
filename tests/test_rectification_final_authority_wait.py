"""Proposed native final rectification diagnostics; opt-in serial owned PostgreSQL.

Forwarding observers cover only the exact selected private boundary, not all
internal projections. Synthetic verification is not provider/worker evidence.
No execution result is implied by this candidate.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import timedelta
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection, connections, transaction
from django.utils import timezone
from test_operational_recovery_authority_wait import _snapshot
from test_privacy_release import fresh
from test_rectification_authority_wait import _client, _files, _queries, _state
from test_rectification_authority_wait import _prepare as _f_prepare
from test_rectification_review import independent_case
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.models import User
from apps.safety import (
    recipient_assessments,
    recipient_review,
    rectification_account,
    rectification_contacts,
    rectification_execution,
    rectification_final,
    rectification_recipients,
    rectification_review,
    rights_rectification,
)
from apps.safety.models import RightsAction
from apps.safety.rights_actions import act

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independent synthetic final response evidence after an owned row wait"
PURPOSE = "Inspect current synthetic correction and recipient evidence for final response"
TEXT = "La rectificación solicitada ha sido aplicada y revisada. / The requested correction has been applied and reviewed."
FAMILIES = ("prepare_review", "inspect_draft", "review_draft", "close_review",
            "prepare_account_source", "prepare_contact_claim")
ROLES = ("review_rights_request", "execute_rights_request", "review_rectification",
         "respond_rights_request", "manage_rights_assignment", "verify_rights_scope",
         "review_recipient_assessment")


def _owned_serial(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL final rectification diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _roles(user):
    user.user_permissions.add(*Permission.objects.filter(
        content_type__app_label="safety", codename__in=ROLES))
    user = User.objects.get(pk=user.pk)
    assert all(user.has_perm("safety." + role) for role in ROLES)
    assert user.mfa_enabled and user.is_active
    return user


def _changes_read(user, case, proposal):
    rights_rectification.preview(user, case.pk, case.version, PURPOSE)
    result = rectification_review.inspect(user, case.pk, proposal.pk, case.version, PURPOSE)
    assert isinstance(result, dict) and bool(result)


def _executed(request, settings, monkeypatch, family):
    if family not in {"prepare_account_source", "prepare_contact_claim"}:
        return _f_prepare(request, settings, monkeypatch, "recipients")
    options = ({"changes": {"account": {"first_name": "Synthetic corrected given name"}}}
               if family == "prepare_account_source" else {"correct_contacts": True})
    case, user, other, person, proposal, _, recipient, receipt = independent_case(
        request, settings, monkeypatch, with_receipt=True, **options)
    assert case.account_subject_id is None and person.subject_id != user.pk
    user = _roles(user)
    original = _roles(User.objects.get(pk=proposal.action.actor_id))
    staff = _client(original)
    _changes_read(user, case, proposal)
    rectification_review.review(user, case.pk, proposal.pk, uuid4(), case.version,
                                "approved", REASON)
    fresh(case, user, other, original, staff)
    _changes_read(user, case, proposal)
    notification = rectification_execution.notify(user, case.pk, proposal.pk,
                                                   uuid4(), case.version, REASON)
    response = recipient.post(receipt + f"response/{notification.response_id}/acknowledge/",
                              {"received": "yes"})
    assert response.status_code == 302
    assert notification.response.receipt_acknowledgement.channel_digest == case.receipt_digest
    fresh(case, user, other, original, staff)
    _changes_read(user, case, proposal)
    execution = rectification_execution.execute(user, case.pk, proposal.pk,
                                                 uuid4(), case.version, REASON)
    fresh(case, user, other, original, staff)
    person.refresh_from_db()
    return dict(case=case, actor=user, client=other, person=person,
                proposal=proposal, execution=execution)


def _prepare(request, settings, monkeypatch, family):
    p = _executed(request, settings, monkeypatch, family)
    case, person, proposal = p["case"], p["person"], p["proposal"]
    author = _roles(p["actor"])
    author_client = _client(author)
    reviewer = _roles(User.objects.get(pk=proposal.action.actor_id))
    reviewer_client = _client(reviewer)
    assert author.pk != reviewer.pk
    inventory = rectification_recipients.prepare(author, case.pk, p["execution"].pk,
                                                 uuid4(), case.version, PURPOSE)
    data = recipient_assessments.inspect(author, case.pk, inventory.pk, case.version, PURPOSE)
    decisions = {token: {"outcome": "not_disclosed", "reason": REASON, "evidence": REASON}
                 for token in recipient_assessments.targets(data)}
    assessment = recipient_assessments.propose(author, case.pk, inventory.pk,
                                               uuid4(), case.version, decisions)
    case.refresh_from_db()
    act(author, case.pk, uuid4(), case.version, "unassign", REASON)
    case.refresh_from_db()
    act(reviewer, case.pk, uuid4(), case.version, "claim", REASON)
    fresh(case, reviewer, reviewer_client, author, author_client)
    recipient_review.inspect(reviewer, case.pk, assessment.pk, case.version, PURPOSE)
    accepted = recipient_review.review(reviewer, case.pk, assessment.pk, uuid4(),
                                       case.version, "accepted", REASON)
    fresh(case, reviewer, reviewer_client, author, author_client)
    read(author_client, case)
    p.update(actor=reviewer, accepted=accepted,
             held=accepted, target=proposal.encrypted_changes,
             boundary="accepted_recipient_review_before_exact_proposal_checked_body")
    if family == "prepare_account_source":
        p.update(held=person.subject, target=None,
                 boundary="evidence_account_source_subject_User_before_private_return")
    elif family == "prepare_contact_claim":
        person.refresh_from_db()
        assert person.phone_claim_id is not None
        p.update(held=person.phone_claim, target=inventory.encrypted_inventory,
                 boundary="evidence_contacts_claim_PhoneClaim_before_exact_inventory_checked_body")
    elif family in {"inspect_draft", "review_draft", "close_review"}:
        draft = rectification_final.prepare(reviewer, case.pk, case.version, case.response_version,
                                            accepted.pk, uuid4(), REASON, TEXT, True)
        p.update(draft=draft, actor=author, held=draft, target=draft.encrypted_reason,
                 boundary="draft_RightsAction_before_exact_draft_checked_body")
        if family in {"review_draft", "close_review"}:
            audited, body = rectification_final.inspect(author, case.pk, case.version,
                                                        case.response_version, draft.pk, PURPOSE)
            matches = body["text"] == TEXT and body["evidence"]["pending"] is False
            assert matches
            p["audited"] = audited
        if family == "close_review":
            approved = rectification_final.review(author, case.pk, case.version,
                         case.response_version, draft.pk, audited.pk, uuid4(), "approved", REASON)
            p.update(actor=reviewer, approved=approved, held=approved,
                     target=approved.encrypted_reason,
                     boundary="accepted_final_review_RightsAction_before_exact_review_checked_body")
    p["permission"] = "safety.respond_rights_request"
    return p


def _invoke(p, family, actor, key, observed):
    case = p["case"]
    if family.startswith("prepare_"):
        result = rectification_final.prepare(actor, case.pk, case.version, case.response_version,
                                               p["accepted"].pk, key, REASON, TEXT, True)
        assert result.operation == "rectify_final_draft" and result.key == key
        body = rectification_final.checked_body(result.encrypted_reason)
        matches = (body["text"] == TEXT and body["reason"] == REASON
                   and body["evidence"]["pending"] is False
                   and body["evidence"]["recipient_review"] == p["accepted"].pk)
        assert matches
    elif family == "inspect_draft":
        result, body = rectification_final.inspect(actor, case.pk, case.version,
                                  case.response_version, p["draft"].pk, PURPOSE)
        matches = body["text"] == TEXT and body["evidence"]["pending"] is False
        assert matches and result.operation == "rectify_final_read"
    elif family == "review_draft":
        result = rectification_final.review(actor, case.pk, case.version, case.response_version,
                     p["draft"].pk, p["audited"].pk, key, "approved", REASON)
        assert result.key == key and result.operation == "rectify_final_review"
        approval = rectification_final.checked_body(result.encrypted_reason)
        matches = (approval["outcome"] == "approved" and approval["draft"] == p["draft"].pk
                   and approval["read"] == p["audited"].pk)
        assert matches
    else:
        result = rectification_final.close(actor, case.pk, case.version, case.response_version,
                                            p["approved"].pk, key)
        assert result.key == key and result.kind == "rectify_complete"
        body = rectification_final.checked_body(result.encrypted_response)
        matches = body["text"] == TEXT and body["simulation"] is True
        assert matches
        p["draft"].refresh_from_db()
        assert p["draft"].final_response_id == result.pk


def _observe_private(monkeypatch, p, revoked, observed):
    account = p["target"] is None
    original = rectification_account.source if account else rectification_final.checked_body

    def forward(*args, **kwargs):
        # Exact ciphertext stays in memory and never enters assertion representations.
        selected = account or (bool(args) and args[0] == p["target"])
        if selected:
            observed["target_calls"] += 1
            if revoked.is_set():
                observed["target_calls_after_revocation"] += 1
        if account:
            observed["inside_account_source"] = True
            observed["account_source_callback_none"] = kwargs.get("check_authority") is None
        try:
            result = original(*args, **kwargs)
        finally:
            if account:
                observed["inside_account_source"] = False
        if selected:
            observed["target_returns"] += 1
            if revoked.is_set():
                observed["target_returns_after_revocation"] += 1
        return result

    if p["boundary"].startswith("evidence_contacts_claim"):
        original_claim = rectification_contacts.claim

        def forward_claim(*args, **kwargs):
            observed["inside_contacts_claim"] = True
            try:
                return original_claim(*args, **kwargs)
            finally:
                observed["inside_contacts_claim"] = False

        monkeypatch.setattr(rectification_contacts, "claim", forward_claim)
    monkeypatch.setattr(rectification_account if account else rectification_final,
                        "source" if account else "checked_body", forward)


def _positive(p, family, key, before, after, observed):
    operation = ("rectify_final_draft" if family.startswith("prepare_") else
                 {"inspect_draft": "rectify_final_read", "review_draft": "rectify_final_review",
                  "close_review": "rectify_final_close"}[family])
    query = RightsAction.objects.filter(request=p["case"], actor=p["actor"], operation=operation)
    if family != "inspect_draft":
        query = query.filter(key=key)
    assert query.exists()
    assert after["tables"]["safety.RightsAction"]["count"] == before["tables"]["safety.RightsAction"]["count"] + 1
    old, new = observed["minimal_before"], observed["minimal_after"]
    changed = {label for label in before["tables"]
               if before["tables"][label] != after["tables"][label]}
    expected = {"safety.RightsAction"}
    if family == "close_review":
        expected.update({"safety.RightsResponse", "safety.RightsNotice", "safety.RightsRequest"})
    assert changed == expected
    if family == "close_review":
        assert new["case_status"] == "resolved"
        assert new["case_version"] == old["case_version"] + 1
        assert new["response_version"] == old["response_version"] + 1
        assert new["scope_status"] == "unverified"
        case_fields = {"case_version", "response_version", "case_status", "scope_status"}
        assert {name: value for name, value in new.items() if name not in case_fields} == {
            name: value for name, value in old.items() if name not in case_fields}
        for label in ("safety.RightsResponse", "safety.RightsNotice"):
            assert after["tables"][label]["count"] == before["tables"][label]["count"] + 1
    else:
        assert new == old


def _exercise(prepared, family, change, monkeypatch, settings, observed):
    actor, held = prepared["actor"], prepared["held"]
    permission_name = "safety.respond_rights_request"
    permission = Permission.objects.get(
        content_type__app_label="safety", codename=permission_name.split(".")[1],
    )
    assert actor.user_permissions.filter(pk=permission.pk).exists()
    assert User.objects.get(pk=actor.pk).has_perm(permission_name)
    queries = _queries(actor, permission)
    if change == "proof_expiry":
        through = User.user_permissions.through
        queries[through._meta.label] = through.objects.all()
    proof = None
    if change == "proof_expiry":
        assert family == "prepare_review"
        proof = prepared["case"].proofs.order_by("-created_at", "-pk").first()
        assert proof is not None and proof.expires_at > timezone.now()
        original_fields = type(proof).objects.filter(pk=proof.pk).values().get()
        # Short synthetic TTL is a fixture precondition, before admission or worker locks.
        updated = type(proof).objects.filter(pk=proof.pk).update(
            expires_at=timezone.now() + timedelta(seconds=10))
        assert updated == 1
        proof_before = type(proof).objects.filter(pk=proof.pk).values().get()
        observed["other_fields_unchanged"] = (
            {name: value for name, value in original_fields.items() if name != "expires_at"}
            == {name: value for name, value in proof_before.items() if name != "expires_at"})
        assert observed["other_fields_unchanged"]
        observed["fixture_precondition"] = "synthetic_short_proof_TTL_before_admission"
    before, files_before = _snapshot(queries), _files(settings)
    observed.update(domain_before=before, files_before=files_before,
                    minimal_before=_state(prepared["case"], prepared["person"]),
                    boundary=prepared["boundary"], held_model=held._meta.label,
                    permission=permission_name, initial_permission=True)
    observed["domain_admission"] = before
    key, revoked, statement = uuid4(), Event(), Event()
    _observe_private(monkeypatch, prepared, revoked, observed)
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
                observed["first_matching_statement_for_update"] = True
                if family == "prepare_account_source":
                    observed["first_wait_inside_expected_helper"] = observed.get("inside_account_source", False)
                elif family == "prepare_contact_claim":
                    observed["first_wait_inside_expected_helper"] = observed.get("inside_contacts_claim", False)
                else:
                    observed["first_wait_inside_expected_helper"] = True
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
                except ValidationError:
                    if change != "proof_expiry":
                        raise
                    observed["status"] = "ValidationError"
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
                elif change == "proof_expiry":
                    # The persisted deadline stays unchanged while real time passes.
                    assert timezone.now() < proof_before["expires_at"], "Proof expired before confirmed wait"
                    expiry_wait_deadline = time.monotonic() + 12
                    while timezone.now() < proof_before["expires_at"]:
                        assert not future.done(), "Worker finished before proof expiry"
                        assert time.monotonic() < expiry_wait_deadline, "Proof deadline not reached within12s"
                        time.sleep(.02)
                    proof_after = type(proof).objects.filter(pk=proof.pk).values().get()
                    observed["natural_deadline_passed"] = timezone.now() >= proof_before["expires_at"]
                    observed["proof_expired"] = proof_after["expires_at"] <= timezone.now()
                    observed["proof_fields_unchanged_during_wait"] = proof_after == proof_before
                    fresh_actor = User.objects.get(pk=actor.pk)
                    observed["permission_preserved"] = fresh_actor.has_perm(permission_name)
                    observed["all_final_roles_preserved"] = all(
                        fresh_actor.has_perm("safety." + role) for role in ROLES)
                    assert observed["natural_deadline_passed"] and observed["proof_expired"]
                    assert observed["proof_fields_unchanged_during_wait"]
                    assert observed["permission_preserved"] and observed["all_final_roles_preserved"]
                    # Event marks the actual deadline crossing, with no interval database mutation.
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
        assert observed["first_wait_inside_expected_helper"]
        if change in {"permission", "proof_expiry"}:
            expected_status = "ValidationError" if change == "proof_expiry" else "PermissionDenied"
            assert observed["status"] == expected_status
            assert after == before
            assert observed["minimal_after"] == observed["minimal_before"]
            assert observed["files_after"] == files_before
            assert observed["target_returns_after_revocation"] == 0
            if family != "prepare_account_source":
                assert observed["target_calls_after_revocation"] == 0
        else:
            assert observed["status"] == "success"
            _positive(prepared, family, key, before, after, observed)
            assert observed["target_returns"] > 0
            # All image inputs reuse a native prepared ready Blob; no new bytes expected.
            assert observed["files_after"] == files_before
    finally:
        pool.shutdown(wait=future is None or future.done(), cancel_futures=True)
        observed["thread_finished"] = future is None or future.done()
        try:
            observed["domain_after"] = _snapshot(queries)
            observed["files_after"] = _files(settings)
            observed["minimal_after"] = _state(prepared["case"], prepared["person"])
        except Exception as error:
            observed["final_snapshot_exception_type"] = type(error).__name__
    assert observed["thread_finished"] and observed["connections_closed"] and observed["holder_released"]



CASES = tuple((family, change) for change in ("valid", "permission") for family in FAMILIES) + (
    ("prepare_review", "proof_expiry"),
)


@pytest.mark.parametrize("family,change", CASES,
                         ids=[change + "-" + family for family, change in CASES])
def test_native_final_authority_after_owned_wait(
    request, settings, monkeypatch, record_property, family, change,
):
    observed = dict(label=family + ":" + change, status="not_started", actual_wait=False,
                    blocker_pids=[], permission_revoked=False, thread_finished=True,
                    connections_closed=True, holder_released=True,
                    proof_expired=False, natural_deadline_passed=False, other_fields_unchanged=False,
                    permission_preserved=False, intended_mutation="none",
                    event_semantics="permission_revocation_or_real_proof_deadline_crossing",
                    target_calls=0, target_returns=0, target_calls_after_revocation=0,
                    target_returns_after_revocation=0, surface="native_service",
                    projection_oracle="exact selected helper boundary; not exhaustive internal projections",
                    _started=time.monotonic())
    try:
        _owned_serial(request, settings)
        p = _prepare(request, settings, monkeypatch, family)
        _exercise(p, family, change, monkeypatch, settings, observed)
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["elapsed_seconds_including_setup_wait_cleanup"] = time.monotonic() - observed.pop("_started")
        record_property("rectification_final_authority_wait",
                        json.dumps(observed, allow_nan=False, sort_keys=True))
