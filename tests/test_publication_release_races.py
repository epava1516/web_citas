"""Fresh authority after an observed PostgreSQL proposal-lock wait."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.models import PrivacyHoldReleaseProposal, RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("scenario", ["permission", "proof", "session", "source"])
def test_release_refreshes_permission_after_proposal_wait(request, settings, monkeypatch, scenario):
    import apps.safety.publication_purpose_release as module
    import apps.safety.publication_purpose_views as views

    original = module.execute
    checked = []

    def with_wait(user, case_id, hold_id, proposal_id, key, version, reason):
        proposal = PrivacyHoldReleaseProposal.objects.select_related("response", "hold").get(
            pk=proposal_id
        )
        if not checked and hasattr(proposal.response, "receipt_acknowledgement"):
            checked.append(True)
            pending_key = uuid4()
            pids = Queue()
            count = RightsAction.objects.filter(request_id=case_id).count()
            permission = Permission.objects.get(codename="release_purpose_restriction")
            case = proposal.action.request
            proof = case.proofs.order_by("-created_at", "-pk").first()
            listing = proposal.hold.person.listing
            revision = listing.approved_revision
            proof_status = proof.status
            session_version = user.session_version
            edit_version = revision.edit_version
            before = (listing.status, listing.lifecycle_version, case.version, case.scope_status)

            def attempt():
                connections.close_all()
                try:
                    actor = User.objects.get(pk=user.pk)
                    assert actor.has_perm("safety.release_purpose_restriction")
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_backend_pid()")
                        pids.put(cursor.fetchone()[0])
                    try:
                        original(actor, case_id, hold_id, proposal_id, pending_key, version, reason)
                    except (PermissionDenied, ValidationError):
                        return "denied"
                    return "released"
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=1) as pool:
                with transaction.atomic():
                    PrivacyHoldReleaseProposal.objects.select_for_update().get(pk=proposal_id)
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_backend_pid()")
                        holder = cursor.fetchone()[0]
                    future = pool.submit(attempt)
                    observe_blocked(pids.get(timeout=5), holder)
                    assert not future.done()
                    if scenario == "permission":
                        user.user_permissions.remove(permission)
                    elif scenario == "proof":
                        proof.status = "failed"
                        proof.save(update_fields=["status"])
                    elif scenario == "session":
                        User.objects.filter(pk=user.pk).update(session_version=session_version + 1)
                    else:
                        revision.edit_version += 1
                        revision.save(update_fields=["edit_version"])
                assert future.result(timeout=20) == "denied"
            proposal.refresh_from_db()
            proposal.hold.refresh_from_db()
            assert proposal.hold.active and proposal.released_at is None
            assert RightsAction.objects.filter(request_id=case_id).count() == count
            assert not RightsAction.objects.filter(key=pending_key).exists()
            listing.refresh_from_db()
            case.refresh_from_db()
            assert (
                listing.status,
                listing.lifecycle_version,
                case.version,
                case.scope_status,
            ) == before
            if scenario == "permission":
                user.user_permissions.add(permission)
            elif scenario == "proof":
                proof.status = proof_status
                proof.save(update_fields=["status"])
            elif scenario == "session":
                User.objects.filter(pk=user.pk).update(session_version=session_version)
            else:
                revision.edit_version = edit_version
                revision.save(update_fields=["edit_version"])
        return original(user, case_id, hold_id, proposal_id, key, version, reason)

    monkeypatch.setattr(module, "execute", with_wait)
    monkeypatch.setattr(views, "execute", with_wait)
    run_flow(request, settings, monkeypatch, "restrict", mixed=False)
    assert checked == [True]
