"""Explicit sparse queue reference; real fixture flows, eager preparation, no capacity claim."""

import json
import os
import time
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.utils import translation
from test_appeals import rejected  # noqa: F401
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import decision, pending  # noqa: F401
from test_match_review import conflict, resolution  # noqa: F401
from test_photo_appeals import photo_case  # noqa: F401
from test_photo_restrictions import restricted  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.listings.models import Appeal
from apps.mediafiles.models import Match

pytestmark = pytest.mark.django_db(transaction=True)


def _case(request, kind):
    """Return independent fixture IDs and actual transition callbacks, outside measurement."""
    if kind == "moderation":
        _, owner, revision, user, client = request.getfixturevalue("pending")

        def finish():
            assert client.post(reverse("moderation_review", args=[revision.pk]),
                               decision(revision)).status_code == 302
            revision.refresh_from_db()
            assert revision.status == "approved"

        return owner, user, client, "revisions", "revision_id", [revision.pk], finish
    if kind == "appeal":
        _, owner, revision, _, user, client = request.getfixturevalue("rejected")
        return owner, user, client, "appeals", "appeal_id", revision, None
    if kind == "match":
        _, _, match, user, client, owner, _ = request.getfixturevalue("conflict")
        # Pair membership is the oracle, independently of the queue's status/history filters.
        reciprocal = Match.objects.get(photo_id=match.candidate_id, candidate_id=match.photo_id)
        pair = [match, reciprocal]
        assert len({row.pk for row in pair}) == 2
        assert pair[0].created_at != pair[1].created_at
        expected = [row.pk for row in sorted(pair, key=lambda row: row.created_at)]

        def finish():
            assert client.post(reverse("match_review", args=[match.pk]),
                               resolution(match)).status_code == 302
            for row in pair:
                row.refresh_from_db()
                assert row.resolved_at and row.decision == "distinct_people"

        return owner, user, client, "matches", "match_id", expected, finish
    values, _, appeal, user, client = request.getfixturevalue("photo_case")
    owner = values[5]

    def finish():
        assert client.post(reverse("photo_appeal_review", args=[appeal.pk]), {
            "result": "upheld", "reason": "Synthetic restriction maintained",
        }).status_code == 302
        appeal.refresh_from_db()
        assert appeal.status == "resolved" and appeal.result == "upheld"

    return owner, user, client, "appeals", "appeal_id", [appeal.pk], finish


def _measure(client, path):
    totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

    def observe(execute, sql, params, many, context):
        totals["sql_queries"] += 1
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            totals["sql_execute_seconds"] += time.perf_counter() - started

    cpu_started = time.process_time()
    started = time.perf_counter()
    with connection.execute_wrapper(observe):
        response = client.get(path)
    totals.update(wall_seconds=time.perf_counter() - started,
                  cpu_seconds=time.process_time() - cpu_started)
    return response, totals


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("kind", ["moderation", "appeal", "match", "photo_appeal"])
def test_listing_review_queue_reference(request, settings, kind, language, record_property):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit owned sparse listing queue diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER"), "Reference requires serial execution"
    assert connection.vendor == "postgresql" and not settings.PRODUCTION
    _owned_database()
    samples, review_samples, controls, known = [], [], [], []
    with translation.override(language):
        owner, user, client, context_key, argument, initial, finish = _case(request, kind)
        # Native fixture requests use /es/ and may change the active translation.
        translation.activate(language)
        path = reverse(kind + "_queue")
        review_route = kind + "_review"

        def links(identifiers):
            return [f'href="{reverse(review_route, kwargs={argument: pk})}"'.encode()
                    for pk in identifiers]

        def phase(state, expected):
            known.extend(pk for pk in expected if pk not in known)
            for ordinal in range(6):
                response, timing = _measure(client, path)
                assert response.status_code == 200
                assert response.wsgi_request.LANGUAGE_CODE == language
                assert response.get("Content-Language") == language
                assert response["Cache-Control"] == "private, no-store"
                assert response.resolver_match.view_name == kind + "_queue"
                shown = [row.pk for row in response.context[context_key]]
                assert shown == expected
                assert len(shown) == len(set(shown))
                assert all(link in response.content for link in links(expected))
                assert all(link not in response.content
                           for link in links([pk for pk in known if pk not in expected]))
                samples.append({"state": state, "ordinal": ordinal, "shown_count": len(shown),
                                "status": response.status_code,
                                "route_name": response.resolver_match.view_name,
                                "response_bytes": len(response.content),
                                "observed_cache_control": response.get("Cache-Control"),
                                "response_language": response.wsgi_request.LANGUAGE_CODE,
                                "content_language": response.get("Content-Language"), **timing})
            if state == "open":
                review_path = reverse(review_route, kwargs={argument: expected[0]})
                object_key = "revision" if kind == "moderation" else "match" if kind == "match" else "appeal"
                for ordinal in range(6):
                    response, timing = _measure(client, review_path)
                    assert response.status_code == 200
                    assert response["Cache-Control"] == "private, no-store"
                    assert response.resolver_match.view_name == review_route
                    assert response.wsgi_request.LANGUAGE_CODE == language
                    assert response.get("Content-Language") == language
                    assert response.context[object_key].pk == expected[0]
                    assert response.context["form"] is not None and b"<form" in response.content
                    review_samples.append({
                        "state": state, "ordinal": ordinal, "status": response.status_code,
                        "route_name": response.resolver_match.view_name,
                        "response_bytes": len(response.content),
                        "observed_cache_control": response.get("Cache-Control"),
                        "response_language": response.wsgi_request.LANGUAGE_CODE,
                        "content_language": response.get("Content-Language"), **timing,
                    })
            denied = owner.get(path)
            anonymous = Client().get(path)
            assert denied.status_code == 403 and anonymous.status_code == 302
            session = client.session
            session["mfa_version"] = 0
            session.save()
            stale = client.get(path)
            assert stale.status_code == 302 and stale.url == reverse("mfa_challenge")
            for label, response in [("no_permission", denied), ("anonymous", anonymous),
                                    ("stale_mfa", stale)]:
                if label != "anonymous":
                    assert response["Cache-Control"] == "private, no-store"
                assert all(link not in response.content for link in links(known))
                controls.append({"state": state, "kind": label, "status": response.status_code,
                                 "observed_cache_control": response.get("Cache-Control")})
            session = client.session
            session["mfa_version"] = user.mfa_version
            session.save()

        if kind == "appeal":
            revision = initial
            phase("before_submit", [])
            assert owner.post(reverse("appeal_submit", args=[revision.decisions.get().pk]), {
                "explanation": "Synthetic decision reconsideration request",
            }).status_code == 302
            appeal = Appeal.objects.get(decision__revision=revision)
            phase("open", [appeal.pk])
            assert client.post(reverse("appeal_review", args=[appeal.pk]), {
                "result": "upheld", "reason": "Synthetic decision maintained",
            }).status_code == 302
            appeal.refresh_from_db()
            revision.refresh_from_db()
            assert appeal.status == "resolved" and appeal.result == "upheld"
            assert revision.status == "rejected"
        else:
            phase("open", initial)
            finish()
        phase("terminal", [])
        user.user_permissions.clear()
        revoked = client.get(path)
        assert revoked.status_code == 403
        assert revoked["Cache-Control"] == "private, no-store"
        assert all(link not in revoked.content for link in links(known))
        controls.append({"state": "terminal", "kind": "permission_revoked", "status": 403,
                         "observed_cache_control": revoked.get("Cache-Control")})
    record_property("listing_review_queue_samples", json.dumps({
        "kind": kind, "language": language, "samples": samples,
        "review_form_samples": review_samples, "authority_controls": controls,
        "scope": "Sparse0/1/2 real fixture queue context/render/authority; first plus5 GETs per state; "
                 "Client wall/processCPU/connectionSQL; eager preparation outside measurements; "
                 "no broker/worker/provider/browser/growth100/p95/capacity credit",
    }, sort_keys=True))
