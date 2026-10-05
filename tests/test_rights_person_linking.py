"""Audited profile reference before a listing exists; linking grants no identity proof."""

import pytest
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import action
from test_rights_linking import ready

from apps.core.models import Person, User
from apps.safety.models import RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


def profile():
    subject = User.objects.create_user(
        username="synthetic-without-listing", email="no-listing@example.invalid", role="individual"
    )
    return Person.objects.create(
        alias="Synthetic person without listing", subject=subject, individual=subject
    )


def test_profile_without_listing_is_linked_audited_and_unverified(request):
    case, _, staff = ready(request)
    person = profile()
    path, data = action(staff, case, "link")
    data["link_person_id"] = str(person.pk)
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    before = case.encrypted_payload, case.received_at, case.initial_due_at
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    case.refresh_from_db()
    assert case.person_id == person.pk and case.reported_subject_id == person.subject_id
    assert case.reported_individual_id == person.individual_id
    assert case.manager_version == person.manager_version
    assert case.referenced_revision_id is None and case.scope_status == "unverified"
    assert (case.encrypted_payload, case.received_at, case.initial_due_at) == before
    assert RightsAction.objects.filter(operation="link").count() == 1
    assert not case.proofs.exists()


def test_profile_link_does_not_bypass_listing_history_or_conflicts(request):
    case, actor, staff = ready(request)
    with_listing = Person.objects.get(subject__username="fixture-v1-model-a")
    path, data = action(staff, case, "link")
    assert staff.post(path, data | {"link_person_id": str(with_listing.pk)}).status_code == 409
    person = profile()
    assert (
        staff.post(
            path,
            data
            | {"link_person_id": str(person.pk), "link_listing_id": str(with_listing.listing.pk)},
        ).status_code
        == 409
    )
    Person.objects.filter(pk=person.pk).update(individual=actor)
    assert staff.post(path, data | {"link_person_id": str(person.pk)}).status_code == 403
    case.refresh_from_db()
    assert case.person_id is None
    assert not RightsAction.objects.filter(operation="link").exists()


@pytest.mark.parametrize("agency", [False, True])
def test_name_rectification_without_listing_has_complete_received_execution(
    request, settings, monkeypatch, agency
):
    from uuid import uuid4

    import test_rights_exports
    from test_account_execution_races import execution_ready
    from test_rectification_review import REASON

    from apps.listings.models import Listing
    from apps.safety.rectification_execution import execute

    request.getfixturevalue("directory")
    person = profile()
    if agency:
        from apps.core.models import Agency

        person.individual = None
        person.agency = Agency.objects.first()
        person.save(update_fields=["individual", "agency"])

    def link_profile(staff, case, selected):
        assert selected.pk == person.pk
        path, data = action(staff, case, "link")
        return path, data | {"link_person_id": str(person.pk)}

    monkeypatch.setattr(test_rights_exports, "link", link_profile)
    case, actor, linked_person, proposal = execution_ready(
        request, settings, monkeypatch, subject_username=person.subject.username
    )
    assert linked_person.pk == person.pk and proposal.source_revision_id is None
    before = person.subject.email, person.subject.session_version
    result = execute(actor, case.pk, proposal.pk, uuid4(), case.version, REASON)
    person.subject.refresh_from_db()
    case.refresh_from_db()
    assert person.subject.first_name == "Concurrent synthetic correction"
    assert (person.subject.email, person.subject.session_version) == before
    assert result.corrected_revision_id is None
    assert not Listing.objects.filter(person=person).exists()
    assert case.status == "reviewing" and case.person_id == person.pk


@pytest.mark.parametrize("mutation", ["manager", "listing"])
def test_link_person_rechecks_after_observed_profile_lock(request, mutation):
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue
    from uuid import uuid4

    from django.core.exceptions import ValidationError
    from django.db import connection, connections, transaction
    from test_photo_reuse_races import observe_blocked

    from apps.listings.models import Listing
    from apps.safety.rights_actions import act

    case, actor, _ = ready(request)
    case.refresh_from_db()
    person = profile()
    pids = Queue()
    key, version = uuid4(), case.version

    def linking():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                act(
                    User.objects.get(pk=actor.pk),
                    case.pk,
                    key,
                    version,
                    "link",
                    "Inspect independently identified synthetic profile",
                    link_person_id=person.pk,
                )
            except ValidationError:
                return "denied"
            return "linked"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            locked_person = Person.objects.select_for_update().get(pk=person.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(linking)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            if mutation == "manager":
                locked_person.manager_version += 1
                locked_person.save(update_fields=["manager_version"])
            else:
                Listing.objects.create(person=locked_person)
        assert future.result(timeout=10) == "denied"
    case.refresh_from_db()
    assert case.person_id is None and case.version == version
    assert not RightsAction.objects.filter(key=key).exists()


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_profile_linking_login_mfa_and_reload(
    live_server, request, settings, tmp_path, language
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _ = ready(request)
    person = profile()
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    labels = {
        "account": "Your account" if language == "en" else "Tu cuenta",
        "inspection": "Private rights inspection"
        if language == "en"
        else "Consulta privada de derechos",
        "submit": "Record assignment action"
        if language == "en"
        else "Registrar acción de asignación",
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(moderator["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(moderator["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            expect(page.get_by_role("heading", name=labels["account"], exact=True)).to_be_visible()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/action/")
            page.locator("[name=operation]").select_option("link")
            page.locator("[name=link_person_id]").fill(str(person.pk))
            page.locator("[name=reason]").fill(
                "Private independently inspected synthetic profile without listing"
            )
            page.get_by_role("button", name=labels["submit"], exact=True).click()
            expect(
                page.get_by_role("heading", name=labels["inspection"], exact=True)
            ).to_be_visible()
            page.reload()
            expect(
                page.get_by_role("heading", name=labels["inspection"], exact=True)
            ).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.person_id == person.pk and case.scope_status == "unverified"
    assert case.referenced_revision_id is None
    assert RightsAction.objects.filter(request=case, operation="link").count() == 1
