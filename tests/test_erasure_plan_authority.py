"""A stale planner must lose authority after an observed PostgreSQL lock wait."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection, connections, transaction
from test_erasure_plans import prepared
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.erasure_plans import record
from apps.safety.models import ErasurePlan, RetentionReview, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("revoked", ["execute", "review", "session", "mfa", "active"])
@pytest.mark.parametrize("replay", [False, True])
def test_plan_new_and_replay_recheck_authority_after_wait(
    request, settings, monkeypatch, revoked, replay
):
    case, user, _, _, _, _, inventory, decisions = prepared(request, settings, monkeypatch)
    key = uuid4()
    if replay:
        record(user, case.pk, inventory.pk, key, case.version, decisions)
    before = ErasurePlan.objects.count(), RetentionReview.objects.count()
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            actor = User.objects.get(pk=user.pk)
            assert actor.has_perm("safety.execute_rights_request")
            assert actor.has_perm("safety.review_rights_request")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                record(actor, case.pk, inventory.pk, key, case.version, decisions)
            except PermissionDenied:
                return "denied"
            return "accepted"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            if revoked in {"execute", "review"}:
                codename = (
                    "execute_rights_request" if revoked == "execute" else "review_rights_request"
                )
                user.user_permissions.remove(Permission.objects.get(codename=codename))
            elif revoked == "session":
                User.objects.filter(pk=user.pk).update(session_version=user.session_version + 1)
            elif revoked == "mfa":
                User.objects.filter(pk=user.pk).update(mfa_version=user.mfa_version + 1)
            else:
                User.objects.filter(pk=user.pk).update(is_active=False)
        assert future.result(timeout=20) == "denied"
    assert (ErasurePlan.objects.count(), RetentionReview.objects.count()) == before
