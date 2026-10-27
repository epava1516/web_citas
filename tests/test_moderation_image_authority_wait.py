"""Private native image reads while moderator grants are revoked during a real lock."""
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.db import connection, connections, transaction
from test_moderation_authority_wait import (  # noqa: F401
    conflict,
    pending,
    photo_environment,
    prepared,
    published,
    scenario,
)
from test_owned_interactive_rights_profile import _files, _snapshot_digest, _state
from test_photo_reuse_races import observe_blocked

from apps.core.models import Person, User
from apps.listings import match_views, moderation_views

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("surface", ["listing_photo", "match_photo", "match_candidate"])
@pytest.mark.parametrize("revoke", [False, True], ids=["control", "permission_revoked"])
def test_native_image_rechecks_grant_after_person_wait(
    request, settings, monkeypatch, record_property, surface, revoke
):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL private image diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql" and connection.settings_dict["NAME"].startswith("test_")
    _owned_database()
    observed = {"surface": surface, "revoke": revoke, "actual_wait": False,
                "scope": "Native private derivative GET, synthetic admitted session; real Person wait and direct grant removal; no new login or performance claim"}
    pool, future, runtime = None, None, {}
    try:
        if surface == "listing_photo":
            person, _, revision, actor, client = request.getfixturevalue("pending")
            photo = revision.photos.get(removed_at__isnull=True)
            path = f"/es/moderation/photos/{photo.pk}/"
            module = moderation_views
        else:
            _, _, match, actor, client, _, _ = request.getfixturevalue("conflict")
            people = list(Person.objects.filter(pk__in=[
                match.photo.revision.listing.person_id,
                match.candidate.revision.listing.person_id,
            ]).order_by("pk"))
            assert len(people) == 2 and all(p.agency_id is None for p in people)
            person = people[0]
            side = "photo" if surface == "match_photo" else "candidate"
            photo = getattr(match, side)
            path = f"/es/moderation/matches/{match.pk}/{side}/image/"
            module = match_views
        assert person.agency_id is None and not actor.is_superuser and not actor.groups.exists()
        assert actor.is_active and actor.email_verified_at and actor.mfa_enabled
        grant = Permission.objects.get(content_type__app_label="listings", codename="review_listing")
        assert grant.pk in set(actor.user_permissions.values_list("pk", flat=True))
        session = client.session
        session["account_version"], session["mfa_version"] = actor.session_version, actor.mfa_version
        session.save()
        with photo.blob.derivative.open("rb") as source:
            expected = source.read()
        assert len(expected) > 0
        expected_sha256 = hashlib.sha256(expected).hexdigest()
        files_before = _files(settings)
        original = module.reviewer_allowed
        pids = Queue()

        def forward(req):
            allowed = original(req)
            if not runtime.get("initial_observed"):
                runtime["initial_observed"] = True
                observed["initial_allowed"] = allowed
                observed["actor_matches"] = req.user.pk == actor.pk
                observed["request_permission_initial"] = req.user.has_perm("listings.review_listing")
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pids.put(cursor.fetchone()[0])
            return allowed

        def worker():
            connections.close_all()
            response = None
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout TO '10s'")
                    runtime["raw"] = connection.connection
                response = client.get(path)
                body = b"".join(response.streaming_content) if response.streaming else response.content
                observed.update(http_status=response.status_code, streaming=response.streaming,
                                private_no_store=response.get("Cache-Control") == "private, no-store",
                                image_bytes_match=len(body) == len(expected) and hashlib.sha256(body).hexdigest() == expected_sha256,
                                derivative_bytes_returned=len(body) if response.streaming else 0)
                return response.status_code
            finally:
                if response is not None:
                    response.close()
                connections.close_all()
                observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

        pool = ThreadPoolExecutor(max_workers=1)
        with monkeypatch.context() as patch:
            patch.setattr(module, "reviewer_allowed", forward)
            with transaction.atomic():
                Person.objects.select_for_update().get(pk=person.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                future = pool.submit(worker)
                pid = pids.get(timeout=8)
                assert pid != holder
                observe_blocked(pid, holder)
                assert not future.done()
                observed["actual_wait"] = True
                assert all(observed[k] for k in ["initial_allowed", "actor_matches", "request_permission_initial"])
                if revoke:
                    actor.user_permissions.remove(grant)
                assert User.objects.get(pk=actor.pk).has_perm("listings.review_listing") is (not revoke)
                before = _state()
            code = future.result(timeout=15)
        after = _state()
        observed.update(installed_models=len(before), all_rows_unchanged=_snapshot_digest(before) == _snapshot_digest(after),
                        files_unchanged=files_before == _files(settings),
                        effective_permission_after=User.objects.get(pk=actor.pk).has_perm("listings.review_listing"))
        assert observed["all_rows_unchanged"] and observed["files_unchanged"] and observed["worker_connections_closed"]
        assert observed["private_no_store"]
        assert code == (403 if revoke else 200)
        assert not observed["streaming"] and not observed["image_bytes_match"] if revoke else observed["streaming"] and observed["image_bytes_match"]
    finally:
        if future is not None and not future.done() and runtime.get("raw") is not None:
            runtime["raw"].cancel()
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
        record_property("n11b_native_image_authority_wait", json.dumps(observed, sort_keys=True))
