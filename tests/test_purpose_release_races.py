"""Observed PostgreSQL waits verify proposal idempotency and fresh authority."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_processing_plans import REASON
from test_purpose_release import prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.models import PurposeReleaseProposal, PurposeRestriction, RightsResponse
from apps.safety.purpose_release import inspect, propose

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("revoke", [False, True])
def test_waiting_proposals_recheck_authority_and_do_not_duplicate_notifications(
    request, settings, monkeypatch, revoke
):
    case, _, reviewer, _, _, favorite, restriction = prepared(request, settings, monkeypatch)
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    version, key = case.version, uuid4()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            user = User.objects.get(pk=reviewer.pk)
            assert user.has_perm("safety.release_purpose_restriction")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                return propose(
                    user, case.pk, restriction.pk, key, version, REASON, "restriction_resolved"
                ).pk
            except PermissionDenied:
                return "denied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            PurposeRestriction.objects.select_for_update().get(pk=restriction.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            second = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not first.done() and not second.done()
            if revoke:
                reviewer.user_permissions.remove(
                    Permission.objects.get(codename="release_purpose_restriction")
                )
        results = [first.result(timeout=20), second.result(timeout=20)]
    case.refresh_from_db()
    restriction.refresh_from_db()
    assert restriction.active and favorite.__class__.objects.filter(pk=favorite.pk).exists()
    if revoke:
        assert results == ["denied", "denied"]
        assert case.version == version
        assert not PurposeReleaseProposal.objects.exists() and not RightsResponse.objects.exists()
    else:
        assert results[0] == results[1]
        assert PurposeReleaseProposal.objects.count() == RightsResponse.objects.count() == 1
        assert case.version == version + 1


@pytest.mark.parametrize("revoked_proof", ["none", "initial", "fresh"])
def test_execution_wait_revalidates_proofs_and_same_key_releases_once(
    request, settings, monkeypatch, revoked_proof
):
    from django.core.exceptions import ValidationError
    from django.test import Client
    from test_rights_verification import read

    from apps.safety.models import RightsAction, RightsProof
    from apps.safety.purpose_release import execute as release
    from apps.safety.rights_verification import receive_event, simulate_event, start

    case, creator, reviewer, client, _, favorite, restriction = prepared(
        request, settings, monkeypatch
    )
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    proposal = propose(
        reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON, "restriction_resolved"
    )
    case.refresh_from_db()
    read(client, case)
    assert (
        Client()
        .post(
            case._receipt_path + f"response/{proposal.response_id}/acknowledge/",
            {"received": "yes"},
        )
        .status_code
        == 302
    )
    proof = start(reviewer, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    verifier = Client()
    verifier.force_login(creator)
    session = verifier.session
    session["mfa_version"] = creator.mfa_version
    session.save()
    read(verifier, case)
    receive_event(creator, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(client, case)
    version, key = case.version, uuid4()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                return release(
                    User.objects.get(pk=reviewer.pk),
                    case.pk,
                    restriction.pk,
                    key,
                    version,
                    proposal.pk,
                    REASON,
                ).pk
            except ValidationError:
                return "denied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            PurposeReleaseProposal.objects.select_for_update().get(pk=proposal.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            second = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            if revoked_proof != "none":
                RightsProof.objects.filter(
                    pk=proposal.proof_id if revoked_proof == "initial" else proof.pk
                ).update(status="failed")
        results = [first.result(timeout=20), second.result(timeout=20)]
    case.refresh_from_db()
    restriction.refresh_from_db()
    proposal.refresh_from_db()
    assert favorite.__class__.objects.filter(pk=favorite.pk).exists()
    if revoked_proof == "none":
        assert results == [proposal.pk, proposal.pk]
        assert not restriction.active and proposal.released_at
        assert RightsAction.objects.filter(operation="purpose_rel_execute").count() == 1
        assert case.version == version + 1
    else:
        assert results == ["denied", "denied"]
        assert restriction.active and proposal.released_at is None
        assert not RightsAction.objects.filter(operation="purpose_rel_execute").exists()
        assert case.version == version
