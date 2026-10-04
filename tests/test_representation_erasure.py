from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person, RepresentationAction
from apps.core.verification_services import publication_ready
from apps.safety.erasure_execution import execute

pytestmark = pytest.mark.django_db(transaction=True)


def test_concurrent_representation_erasure_creates_one_revocation(request, settings, monkeypatch):
    from threading import Barrier

    from apps.core.models import User

    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=["representation"]
    )
    data = payload(case) | {"purposes": ["representation"]}
    previous_version = person.manager_version
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            reviewer = User.objects.get(pk=actor.pk)
            barrier.wait(timeout=15)
            return execute(reviewer, case.pk, plan.pk, **data).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(worker) for _ in range(2)]
        assert results[0].result(timeout=30) == results[1].result(timeout=30)
    person.refresh_from_db()
    assert person.manager_version == previous_version + 1
    assert RepresentationAction.objects.filter(person=person, action="revoke").count() == 1


def test_inflight_self_consent_cannot_restore_erased_authorization(request, settings, monkeypatch):
    case, actor, staff, _, _, person, plan, _, _, _ = plan_fixture(
        request,
        settings,
        monkeypatch,
        selected_purposes=["representation"],
        subject_username="fixture-v1-individual",
    )
    client = Client()
    client.force_login(person.subject)
    old_grants = RepresentationAction.objects.filter(person=person, action="grant").count()
    entered, resume = Event(), Event()
    original = Person.objects.select_for_update

    def waiting_lock(*args, **kwargs):
        if current_thread().name.startswith("self_consent"):
            entered.set()
            assert resume.wait(timeout=30)
        return original(*args, **kwargs)

    monkeypatch.setattr(Person.objects, "select_for_update", waiting_lock)

    def callback():
        close_old_connections()
        try:
            return client.post(
                f"/en/person/{person.pk}/consent/",
                {
                    "authorize": "on",
                    "version": "dev-1",
                },
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="self_consent") as pool:
        response = pool.submit(callback)
        try:
            assert entered.wait(timeout=15)
            execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["representation"]}))
        finally:
            resume.set()
        assert response.result(timeout=30) == 409
    person.refresh_from_db()
    assert person.consent_revoked_at and not publication_ready(person)
    assert RepresentationAction.objects.filter(person=person, action="grant").count() == old_grants
    assert RepresentationAction.objects.filter(person=person, action="revoke").count() == 1
    # A new explicit request may authorize the current manager, but does not publish or verify age.
    assert (
        client.post(
            f"/en/person/{person.pk}/consent/",
            {
                "authorize": "on",
                "version": "dev-1",
            },
        ).status_code
        == 302
    )
    person.refresh_from_db()
    assert not person.consent_revoked_at and person.consent_version == person.manager_version
    assert person.age_status == "pending" and not publication_ready(person)
    # The same open request can inspect and verify the remaining scopes afresh.
    import uuid

    from test_rights_verification import read

    from apps.safety.rights_verification import start

    case.refresh_from_db()
    assert case.manager_version == person.manager_version
    read(staff, case)
    proof = start(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Review remaining erasure scopes after the actual authorization withdrawal",
    )
    assert proof.manager_version == person.manager_version


def test_self_consent_cannot_reauthorize_erased_publication(request, settings, monkeypatch):
    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request,
        settings,
        monkeypatch,
        selected_purposes=["publication", "representation"],
        subject_username="fixture-v1-individual",
    )
    client = Client()
    client.force_login(person.subject)
    execute(
        actor,
        case.pk,
        plan.pk,
        **(
            payload(case)
            | {
                "purposes": ["publication", "representation"],
            }
        ),
    )
    assert (
        client.post(
            f"/en/person/{person.pk}/consent/",
            {
                "authorize": "on",
                "version": "dev-1",
            },
        ).status_code
        == 409
    )
    person.refresh_from_db()
    assert person.consent_revoked_at and person.publication_erased_at
