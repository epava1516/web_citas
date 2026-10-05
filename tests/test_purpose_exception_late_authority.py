"""Observed waits after preliminary validation must re-read consumer authority."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_photo_reuse_races import observe_blocked
from test_purpose_exception_consumption import approved, payload
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.listings.models import Favorite
from apps.safety import purpose_exceptions
from apps.safety.erasure_execution import execute
from apps.safety.models import (
    ErasureExecution,
    PurposeExceptionReview,
    PurposeRestriction,
    RightsAction,
    RightsProof,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "change", ["approver_permission", "actor_mfa", "proof", "exception_expiry"]
)
def test_authority_invalidated_while_waiting_on_approval_denies_without_effects(
    request, settings, monkeypatch, change
):
    case, actor, _, plan, favorite, proposal, reviewer, _ = approved(request, settings, monkeypatch)
    values = payload(case, proposal)
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                execute(user, case.pk, plan.pk, **values)
                return "executed"
            except (PermissionDenied, ValidationError):
                return "denied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            review = PurposeExceptionReview.objects.select_for_update().get(proposal=proposal)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if change == "approver_permission":
                reviewer.user_permissions.remove(
                    Permission.objects.get(codename="review_purpose_exception")
                )
            elif change == "actor_mfa":
                # Authentication version state changes; no MFA recovery flow is simulated.
                User.objects.filter(pk=actor.pk).update(mfa_version=actor.mfa_version + 1)
            elif change == "proof":
                # Late stored-proof invalidation; not evidence of an external provider callback.
                RightsProof.objects.filter(pk=proposal.proof_id).update(status="failed")
            else:
                # Only the exception clock advances; proof/plan clocks remain unchanged.
                monkeypatch.setattr(
                    purpose_exceptions,
                    "timezone",
                    SimpleNamespace(now=lambda: proposal.expires_at + timedelta(seconds=1)),
                )
        assert future.result(timeout=30) == "denied"
    review.refresh_from_db()
    case.refresh_from_db()
    assert review.consumed_action_id is None and case.version == values["version"]
    assert not ErasureExecution.objects.exists()
    assert not RightsAction.objects.filter(request=case, operation="erasure_execute").exists()
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeRestriction.objects.get().active
