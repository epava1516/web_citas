"""Fresh operator state and final-domain-lock variants of native moderation POSTs."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Group, Permission
from django.db import connection, connections, transaction
from django.utils import timezone
from test_moderation_authority_wait import (  # noqa: F401
    conflict,
    decision,
    pending,
    photo_environment,
    prepared,
    published,
    resolution,
    scenario,
)
from test_owned_interactive_rights_profile import _files, _snapshot_digest, _state
from test_photo_reuse_races import observe_blocked

from apps.core.models import Person, User
from apps.listings import match_views, moderation_views
from apps.listings.models import Revision
from apps.listings.profile_contract import CURRENT_CONTRACT
from apps.mediafiles.models import Match

pytestmark = pytest.mark.django_db(transaction=True)
CASES = [(surface, mode) for surface in ["listing", "match"]
         for mode in ["group_permission", "account_epoch", "mfa_epoch", "inactive", "erased", "final_target_permission"]]
CASES.append(("listing", "pending_sibling_permission"))


@pytest.mark.parametrize("surface,mode", CASES)
def test_native_review_fresh_operator_and_final_wait(
    request, settings, monkeypatch, record_property, surface, mode
):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL moderation variants only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql" and connection.settings_dict["NAME"].startswith("test_")
    _owned_database()
    observed = {"surface": surface, "mode": mode, "actual_wait": False,
                "scope": "Native POST after committed operator-state change while own PostgreSQL resource lock blocks; no new ceremony or app latency"}
    pool, future, runtime = None, None, {}
    try:
        if surface == "listing":
            person, _, target, actor, client = request.getfixturevalue("pending")
            path = f"/es/moderation/listings/{target.pk}/"
            data = decision(target, outcome="approved" if mode == "pending_sibling_permission" else "rejected")
            module, name = moderation_views, "decide"
            holder_model, holder_pk = Person, person.pk
            if mode == "final_target_permission":
                holder_model, holder_pk = Revision, target.pk
            if mode == "pending_sibling_permission":
                sibling = Revision.objects.create(listing=target.listing, manager_version=person.manager_version,
                                                  status="pending", content_contract=CURRENT_CONTRACT)
                holder_model, holder_pk = Revision, sibling.pk
        else:
            _, _, target, actor, client, _, _ = request.getfixturevalue("conflict")
            people = list(Person.objects.filter(pk__in=[target.photo.revision.listing.person_id,
                                                        target.candidate.revision.listing.person_id]).order_by("pk"))
            assert len(people) == 2 and all(p.agency_id is None for p in people)
            holder_model, holder_pk = Person, people[0].pk
            if mode == "final_target_permission":
                holder_model, holder_pk = Match, target.pk
            path = f"/es/moderation/matches/{target.pk}/"
            data = resolution(target, outcome="conflict")
            module, name = match_views, "resolve"
        assert not actor.is_superuser and not actor.groups.exists()
        grant = Permission.objects.get(content_type__app_label="listings", codename="review_listing")
        assert grant.pk in set(actor.user_permissions.values_list("pk", flat=True))
        if mode == "group_permission":
            actor.user_permissions.remove(grant)
            group = Group.objects.create(name="synthetic-moderation-reviewers")
            group.permissions.add(grant)
            actor.groups.add(group)
            assert not actor.user_permissions.filter(pk=grant.pk).exists()
        assert User.objects.get(pk=actor.pk).has_perm("listings.review_listing")
        session = client.session
        session["account_version"], session["mfa_version"] = actor.session_version, actor.mfa_version
        session.save()
        files_before = _files(settings)
        original = getattr(module, name)
        pids = Queue()

        def forward(user, *args, **kwargs):
            observed["initial_permission"] = user.has_perm("listings.review_listing")
            observed["permission_cache_warmed"] = "listings.review_listing" in getattr(user, "_perm_cache", set())
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            return original(user, *args, **kwargs)

        def worker():
            connections.close_all()
            response = None
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout TO '10s'")
                    runtime["raw"] = connection.connection
                response = client.post(path, data)
                return response.status_code
            finally:
                if response is not None:
                    response.close()
                connections.close_all()
                observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

        pool = ThreadPoolExecutor(max_workers=1)
        with monkeypatch.context() as patch:
            patch.setattr(module, name, forward)
            with transaction.atomic():
                holder_model.objects.select_for_update().get(pk=holder_pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                future = pool.submit(worker)
                pid = pids.get(timeout=8)
                assert pid != holder
                observe_blocked(pid, holder)
                assert not future.done()
                observed["actual_wait"] = True
                assert observed["initial_permission"] and observed["permission_cache_warmed"]
                if mode == "group_permission":
                    group.permissions.remove(grant)
                elif mode == "account_epoch":
                    User.objects.filter(pk=actor.pk).update(session_version=actor.session_version + 1)
                elif mode == "mfa_epoch":
                    User.objects.filter(pk=actor.pk).update(mfa_version=actor.mfa_version + 1)
                elif mode == "inactive":
                    User.objects.filter(pk=actor.pk).update(is_active=False)
                elif mode == "erased":
                    User.objects.filter(pk=actor.pk).update(account_erased_at=timezone.now())
                else:
                    actor.user_permissions.remove(grant)
                fresh = User.objects.get(pk=actor.pk)
                observed["intervention_verified"] = (
                    not fresh.has_perm("listings.review_listing") if mode in ["group_permission", "inactive", "final_target_permission", "pending_sibling_permission"]
                    else fresh.session_version == actor.session_version + 1 if mode == "account_epoch"
                    else fresh.mfa_version == actor.mfa_version + 1 if mode == "mfa_epoch"
                    else fresh.account_erased_at is not None
                )
                assert observed["intervention_verified"]
                before = _state()
            code = future.result(timeout=15)
        after = _state()
        observed.update(http_status=code, installed_models=len(before), all_rows_unchanged=_snapshot_digest(before) == _snapshot_digest(after),
                        files_unchanged=files_before == _files(settings), holder_kind=holder_model._meta.label)
        assert observed["all_rows_unchanged"] and observed["files_unchanged"] and observed["worker_connections_closed"]
        assert code == 403
    finally:
        if future is not None and not future.done() and runtime.get("raw") is not None:
            runtime["raw"].cancel()
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
        record_property("n11c_native_review_authority_variants", json.dumps(observed, sort_keys=True))
