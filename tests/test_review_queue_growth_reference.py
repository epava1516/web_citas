"""Observe existing review queue selection and authority at declared cardinalities."""

import json
import time
from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.utils import timezone, translation
from test_verification import account, ready_accounts  # noqa: F401

from apps.core.models import (
    Agency,
    AgencyAppeal,
    AgencyReview,
    ManagerAppeal,
    ManagerReview,
    Person,
    User,
)

pytestmark = pytest.mark.django_db(transaction=True)


def add_rows(kind, start, count, owner, reviewer, support):
    """Create only synthetic source rows; never timed as application work."""
    if kind in {"organization", "agency_appeal"}:
        owners = User.objects.bulk_create([
            User(username=f"queue-owner-{i}", email=f"queue-owner-{i}@example.invalid")
            for i in range(start, start + count)
        ])
        agencies = Agency.objects.bulk_create([
            Agency(owner=user, name=f"Synthetic organization {i}",
                   verification_status="pending" if kind == "organization" else "failed")
            for i, user in enumerate(owners, start)
        ])
        if kind == "organization":
            return agencies
        decisions = AgencyReview.objects.bulk_create([
            AgencyReview(agency=a, reviewer=reviewer, outcome="failed",
                         reason="Synthetic initial review", evidence_reference=f"queue-{i}",
                         procedure="simulator-v1") for i, a in enumerate(agencies, start)
        ])
        return AgencyAppeal.objects.bulk_create([
            AgencyAppeal(decision=d, actor_id=a.owner_id, review_version=1,
                         explanation="Synthetic appeal") for d, a in zip(decisions, agencies, strict=True)
        ])
    if kind in {"manager", "manager_appeal"}:
        people = Person.objects.bulk_create([
            Person(agency=support, alias=f"Synthetic person {i}",
                   manager_review_status="pending" if kind == "manager" else "failed")
            for i in range(start, start + count)
        ])
        if kind == "manager":
            return people
        decisions = ManagerReview.objects.bulk_create([
            ManagerReview(person=p, reviewer=reviewer, manager_version=1,
                          outcome="failed", reason="Synthetic initial review") for p in people
        ])
        return ManagerAppeal.objects.bulk_create([
            ManagerAppeal(decision=d, actor=owner, explanation="Synthetic appeal")
            for d in decisions
        ])
    raise AssertionError("Unsupported static queue kind")


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("kind", ["organization", "manager", "agency_appeal", "manager_appeal"])
@pytest.mark.usefixtures("ready_accounts")
def test_review_queue_growth_reference(kind, language, record_property):
    owner, outsider = account("queue-owner", agency=True)
    reviewer, client = account("queue-reviewer", agency=True)
    codename = "review_agency" if kind in {"organization", "agency_appeal"} else "review_listing"
    app_label = "core" if kind in {"organization", "agency_appeal"} else "listings"
    reviewer.user_permissions.add(Permission.objects.get(
        codename=codename, content_type__app_label=app_label
    ))
    support = Agency.objects.create(owner=owner, name="Synthetic support", verification_status="passed")
    closed = add_rows(kind, 900, 1, owner, reviewer, support)[0]
    if kind == "organization":
        closed.verification_status = "failed"
        field = "verification_status"
    elif kind == "manager":
        closed.manager_review_status = "approved"
        field = "manager_review_status"
    else:
        closed.status = "resolved"
        field = "status"
    closed.save(update_fields=[field])
    base = timezone.now() - timedelta(days=1)
    type(closed).objects.filter(pk=closed.pk).update(created_at=base - timedelta(days=1))
    records, samples, controls = [], [], []
    key = "agencies" if kind == "organization" else "people" if kind == "manager" else "appeals"
    with translation.override(language):
        path = reverse(kind + "_queue")
        for size in [0, 1, 10, 100, 101]:
            added = add_rows(kind, len(records), size - len(records), owner, reviewer, support)
            for i, row in enumerate(added, len(records)):
                row.created_at = base + timedelta(seconds=i)
            if added:
                type(added[0]).objects.bulk_update(added, ["created_at"])
            records.extend(added)
            expected = [row.pk for row in records[:100]]
            review_route = kind + "_review"
            argument = "agency_id" if kind == "organization" else "person_id" if kind == "manager" else "appeal_id"
            for ordinal in range(6):
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
                elapsed, cpu = time.perf_counter() - started, time.process_time() - cpu_started
                assert response.status_code == 200 and response.resolver_match.view_name == kind + "_queue"
                shown = list(response.context[key])
                assert [row.pk for row in shown] == expected
                assert closed.pk not in {row.pk for row in shown}
                body = response.content.decode()
                assert all(
                    f'href="{reverse(review_route, kwargs={argument: identifier})}"' in body
                    for identifier in expected
                )
                assert f'href="{reverse(review_route, kwargs={argument: closed.pk})}"' not in body
                if size == 101:
                    assert records[-1].pk not in {row.pk for row in shown}
                    assert f'href="{reverse(review_route, kwargs={argument: records[-1].pk})}"' not in body
                samples.append({"size": size, "ordinal": ordinal, "wall_seconds": elapsed,
                                "cpu_seconds": cpu, "response_bytes": len(response.content),
                                "shown_count": len(shown), **totals})
            denied = outsider.get(path)
            anonymous = Client().get(path)
            assert denied.status_code == 403
            assert anonymous.status_code == 302
            controls.extend([{"size": size, "kind": "no_permission", "status": denied.status_code},
                             {"size": size, "kind": "anonymous", "status": anonymous.status_code}])
            session = client.session
            session["mfa_version"] = 0
            session.save()
            stale = client.get(path)
            assert stale.status_code == 302 and stale.url == reverse("mfa_challenge")
            controls.append({"size": size, "kind": "stale_mfa", "status": stale.status_code})
            for rejection in [denied, anonymous, stale]:
                assert all(
                    f'href="{reverse(review_route, kwargs={argument: identifier})}"'.encode()
                    not in rejection.content for identifier in expected
                )
            session = client.session
            session["mfa_version"] = reviewer.mfa_version
            session.save()
        reviewer.user_permissions.clear()
        assert client.get(path).status_code == 403
        controls.append({"size": 101, "kind": "permission_revoked", "status": 403})
    record_property("review_queue_samples", json.dumps({
        "kind": kind, "language": language, "samples": samples, "authority_controls": controls,
        "scope": "Original top100 selection, ascending distinct creation times; synthetic Client wall/CPU/connection SQL, first plus5subsequent per size; not p95/capacity"
    }, sort_keys=True))
