"""Native moderation POSTs with actual PostgreSQL blocking and revoked grants."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.db import connection, connections, transaction
from django.utils import timezone
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import decision, pending  # noqa: F401
from test_match_review import conflict, resolution  # noqa: F401
from test_owned_interactive_rights_profile import _assert_delta, _files, _snapshot_digest, _state
from test_photo_reuse_races import observe_blocked
from test_photos import photo_environment  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import Person, User
from apps.listings import match_views, moderation_views
from apps.listings.models import Listing, ModerationDecision, PublicationState, Revision
from apps.mediafiles.models import Match, MatchResolution, PhotoRestriction

pytestmark = pytest.mark.django_db(transaction=True)


def _exact(before, after, **kwargs):
    try:
        _assert_delta(before, after, **kwargs)
    except AssertionError:
        return False
    return True


@pytest.mark.parametrize("surface", ["listing", "match"])
@pytest.mark.parametrize("revoke", [False, True], ids=["control", "permission_revoked"])
def test_native_review_rechecks_grant_after_person_wait(
    request, settings, monkeypatch, record_property, surface, revoke
):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL moderation diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql" and connection.settings_dict["NAME"].startswith("test_")
    _owned_database()
    observed = {"surface": surface, "revoke": revoke, "actual_wait": False,
                "scope": "Native POST; synthetic admitted session, direct grant removed during actual Person lock wait; no new login/TOTP or performance claim"}
    pool, future, runtime = None, None, {}
    try:
        if surface == "listing":
            person, _, target, actor, client = request.getfixturevalue("pending")
            path = f"/es/moderation/listings/{target.pk}/"
            data = decision(target, outcome="rejected")
            module, name = moderation_views, "decide"
            people = [person]
        else:
            _, _, target, actor, client, _, _ = request.getfixturevalue("conflict")
            path = f"/es/moderation/matches/{target.pk}/"
            data = resolution(target, outcome="conflict")
            module, name = match_views, "resolve"
            people = list(Person.objects.filter(pk__in=[
                target.photo.revision.listing.person_id,
                target.candidate.revision.listing.person_id,
            ]).order_by("pk"))
        person = min(people, key=lambda p: p.pk)
        assert all(p.agency_id is None for p in people)
        grant = Permission.objects.get(content_type__app_label="listings", codename="review_listing")
        assert grant.pk in set(actor.user_permissions.values_list("pk", flat=True))
        assert not actor.is_superuser and not actor.groups.exists()
        assert actor.is_active and actor.email_verified_at and actor.mfa_enabled
        session = client.session
        session["account_version"], session["mfa_version"] = actor.session_version, actor.mfa_version
        session.save()
        before_files = _files(settings)
        pids = Queue()
        original = getattr(module, name)

        def forward(user, *args, **kwargs):
            observed["request_permission_initial"] = user.has_perm("listings.review_listing")
            observed["request_cache_warmed"] = "listings.review_listing" in getattr(user, "_perm_cache", set())
            observed["request_actor_matches"] = user.pk == actor.pk
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
                assert all(observed[k] for k in ["request_permission_initial", "request_cache_warmed", "request_actor_matches"])
                if revoke:
                    actor.user_permissions.remove(grant)
                assert User.objects.get(pk=actor.pk).has_perm("listings.review_listing") is (not revoke)
                before = _state()
                started = timezone.now()
            code = future.result(timeout=15)
        ended = timezone.now()
        after = _state()
        updates, additions = {}, {}
        audit_ok = True
        if surface == "listing":
            label = ModerationDecision._meta.label
            ids = set(after[label]) - set(before[label])
            additions[label] = ids
            rows = list(ModerationDecision.objects.filter(pk__in=ids))
            audit_ok = len(rows) == 1 and all(
                r.revision_id == target.pk and r.reviewer_id == actor.pk and r.outcome == "rejected"
                and r.reason == data["reason"] for r in rows)
            current = Revision.objects.get(pk=target.pk)
            updates[(Revision._meta.label, target.pk)] = {"status": "rejected", "updated_at": current.updated_at}
            audit_ok = audit_ok and started <= current.updated_at <= ended
            listing = Listing.objects.get(pk=target.listing_id)
            old = before[Listing._meta.label][listing.pk]
            if not old["approved_revision_id"]:
                updates[(Listing._meta.label, listing.pk)] = {"status": "rejected", "lifecycle_version": old["lifecycle_version"] + 1}
        else:
            pair = {(target.photo_id, target.candidate_id), (target.candidate_id, target.photo_id)}
            matches = [m for m in Match.objects.all() if (m.photo_id, m.candidate_id) in pair]
            for match in matches:
                old = before[Match._meta.label][match.pk]
                updates[(Match._meta.label, match.pk)] = {"decision": "conflict", "resolved_at": match.resolved_at, "review_version": old["review_version"] + 1}
                audit_ok = audit_ok and match.resolved_at is not None and started <= match.resolved_at <= ended
            ids = set(after[MatchResolution._meta.label]) - set(before[MatchResolution._meta.label])
            additions[MatchResolution._meta.label] = ids
            rows = list(MatchResolution.objects.filter(pk__in=ids))
            audit_ok = audit_ok and len(rows) == len(matches) == 2 and {r.match_id for r in rows} == {m.pk for m in matches}
            audit_ok = audit_ok and all(r.reviewer_id == actor.pk and r.outcome == "conflict" and r.reason == data["reason"] and r.evidence_reference == data["evidence_reference"] for r in rows)
            restriction_ids = set(after[PhotoRestriction._meta.label]) - set(before[PhotoRestriction._meta.label])
            additions[PhotoRestriction._meta.label] = restriction_ids
            restrictions = list(PhotoRestriction.objects.filter(pk__in=restriction_ids))
            current_decision_ids = {r.pk for r in rows if r.match_id == target.pk}
            audit_ok = audit_ok and len(restrictions) == 2 and {r.person_id for r in restrictions} == {p.pk for p in people}
            audit_ok = audit_ok and all(r.decision_id in current_decision_ids and r.manager_version == next(p.manager_version for p in people if p.pk == r.person_id) and r.photo_id in [target.photo_id, target.candidate_id] for r in restrictions)
            for listing in Listing.objects.filter(person__in=people):
                old = before[Listing._meta.label][listing.pk]
                updates[(Listing._meta.label, listing.pk)] = {"status": "paused" if old["status"] == "published" else old["status"], "available_until": None, "lifecycle_version": old["lifecycle_version"] + 1}
        # A confirmed conflict invalidates the previously eligible native projection.
        # Keep every other field/table exact; never exempt the projection model.
        if surface == "match":
            label = PublicationState._meta.label
            for listing in Listing.objects.filter(person__in=people):
                original_state = before[label][listing.pk]
                if original_state["eligible"]:
                    current_state = after[label][listing.pk]
                    audit_ok = audit_ok and started <= current_state["computed_at"] <= ended
                    updates[(label, listing.pk)] = {
                        "eligible": False, "check_age": False, "check_contact": False,
                        "check_agency": False, "computed_at": current_state["computed_at"],
                    }
        observed["changed_model_fields"] = {
            label: sorted({field for pk, row in before[label].items()
                           if pk in after[label] for field in row if row[field] != after[label][pk][field]})
            for label in before if before[label] != after[label]
        }
        none = _exact(before, after)
        effect = audit_ok and _exact(before, after, additions=additions, updates=updates)
        observed.update(http_status=code, installed_models=len(before),
                        before_sha256=_snapshot_digest(before), after_sha256=_snapshot_digest(after),
                        full_snapshot_no_effect=none, exact_native_effect=effect,
                        files_unchanged=before_files == _files(settings),
                        effective_permission_after=User.objects.get(pk=actor.pk).has_perm("listings.review_listing"))
        assert observed["files_unchanged"] and observed["worker_connections_closed"]
        assert code == (403 if revoke else 302)
        assert none if revoke else effect
    finally:
        if future is not None and not future.done() and runtime.get("raw") is not None:
            runtime["raw"].cancel()
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
        record_property("n11a_native_authority_wait", json.dumps(observed, sort_keys=True))
