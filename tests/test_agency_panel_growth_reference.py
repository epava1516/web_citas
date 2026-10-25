"""Instrument the unchanged agency panel at declared synthetic cardinalities."""

import json
import time

import pytest
from django.db import connection
from django.test import Client
from django.utils import timezone
from test_verification import account, ready_accounts  # noqa: F401

from apps.core.models import Agency, AgencyMember, Person, User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("size", [1, 10, 100])
@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.usefixtures("ready_accounts")
def test_agency_panel_growth_reference(size, language, record_property):
    owner, owner_client = account("panel-owner", agency=True)
    editor, editor_client = account("panel-editor", agency=True)
    agency = Agency.objects.create(owner=owner, name="Synthetic panel")
    people = Person.objects.bulk_create([
        Person(agency=agency, assigned_editor=editor if i == 0 else None,
               alias=f"Synthetic person {i}") for i in range(size)
    ])
    users = [editor, *User.objects.bulk_create([
        User(username=f"panel-member-{i}", email=f"member-{i}@example.invalid",
             email_verified_at=timezone.now()) for i in range(1, size)
    ])]
    AgencyMember.objects.bulk_create([AgencyMember(agency=agency, user=u) for u in users])
    inactive = User.objects.create(username="inactive-editor", email="inactive@example.invalid")
    AgencyMember.objects.create(agency=agency, user=inactive, active=False)
    other_owner, _ = account("other-panel-owner", agency=True)
    other_agency = Agency.objects.create(owner=other_owner, name="Other synthetic panel")
    Person.objects.create(agency=other_agency, alias="Foreign private person")
    outsider, outsider_client = account("panel-outsider", agency=True)
    samples = []
    path = f"/{language}/agency/{agency.pk}/"
    for actor, client in [("owner", owner_client), ("editor", editor_client)]:
        for ordinal in range(6):
            totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

            def observe(execute, sql, params, many, context):
                totals["sql_queries"] += 1
                started = time.perf_counter()
                try:
                    return execute(sql, params, many, context)
                finally:
                    totals["sql_execute_seconds"] += time.perf_counter() - started

            cpu_start = time.process_time()
            started = time.perf_counter()
            with connection.execute_wrapper(observe):
                response = client.get(path)
            elapsed = time.perf_counter() - started
            cpu = time.process_time() - cpu_start
            assert response.status_code == 200
            expected = people if actor == "owner" else people[:1]
            assert {p.pk for p in response.context["people"]} == {p.pk for p in expected}
            assert "Foreign private person" not in response.content.decode()
            if actor == "owner":
                assert {m.user_id for m in response.context["members"]} == {u.pk for u in users}
                assert all(u.email.encode() in response.content for u in users)
                assert inactive.email.encode() not in response.content
            else:
                assert not response.context["members"]
                assert b"member-" not in response.content
            samples.append({"actor": actor, "ordinal": ordinal,
                            "wall_seconds": elapsed, "cpu_seconds": cpu,
                            "response_bytes": len(response.content),
                            "people_order": [people.index(p) for p in response.context["people"]],
                            "member_order": [[u.pk for u in users].index(m.user_id) for m in response.context["members"]]
                            if actor == "owner" else [], **totals})
    assert outsider_client.get(path).status_code == 403
    assert Client().get(path).status_code == 302
    AgencyMember.objects.filter(agency=agency, user=editor).update(active=False)
    assert editor_client.get(path).status_code == 403
    assert owner_client.get(path).status_code == 200
    assert not AgencyMember.objects.filter(agency=agency, user=outsider).exists()
    record_property("agency_panel_samples", json.dumps({
        "size": size, "language": language, "samples": samples,
        "scope": "Synthetic Client.request wall/CPU/connection SQL; first separate plus five later; no p95/load/provider"
    }, sort_keys=True))
