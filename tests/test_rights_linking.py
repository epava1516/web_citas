import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import action, prepared

from apps.core.models import AgencyMember, Person, User
from apps.safety.models import RightsAccess, RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


def ready(request):
    case, user, staff = prepared(request)
    path, claim = action(staff, case, "claim")
    assert staff.post(path, claim).status_code == 302
    assert (
        staff.post(
            f"/en/moderation/rights/{case.pk}/",
            {"purpose": "Inspect the reference before proposing a linked profile"},
        ).status_code
        == 200
    )
    return case, user, staff


def link(staff, case, person):
    path, data = action(staff, case, "link")
    data["link_listing_id"] = person.listing.pk
    return path, data


def test_link_is_audited_and_preserves_unverified_scope_dates_and_payload(request):
    case, _, staff = ready(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    original = case.encrypted_payload, case.received_at, case.initial_due_at
    path, data = link(staff, case, person)
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    case.refresh_from_db()
    assert case.person_id == person.pk and case.reported_subject_id == person.subject_id
    assert case.reported_individual_id == person.individual_id
    assert case.manager_version == person.manager_version
    assert case.referenced_revision_id == person.listing.approved_revision_id
    assert case.scope_status == "unverified" and case.version == 3
    assert (case.encrypted_payload, case.received_at, case.initial_due_at) == original
    assert RightsAction.objects.filter(operation="link").count() == 1
    assert (
        b"Identity and scope remain unverified"
        in staff.get(f"/en/moderation/rights/{case.pk}/").content
    )
    other = Person.objects.get(subject__username="fixture-v1-model-a")
    path, data = link(staff, case, other)
    assert staff.post(path, data).status_code == 409


def test_linking_own_profile_denies_and_rolls_back(request):
    case, reviewer, staff = ready(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    Person.objects.filter(pk=person.pk).update(individual=reviewer)
    path, data = link(staff, case, person)
    assert staff.post(path, data).status_code == 403
    case.refresh_from_db()
    assert case.person_id is None and case.version == 2
    assert RightsAction.objects.count() == 1


def test_scope_can_reference_unpublished_data_without_verification(request):
    case, _, staff = ready(request)
    person = Person.objects.get(subject__username="fixture-v1-model-b")
    assert not person.listing.approved_revision_id
    path, data = link(staff, case, person)
    assert staff.post(path, data).status_code == 302
    case.refresh_from_db()
    assert case.person_id == person.pk and case.referenced_revision_id is None
    assert case.scope_status == "unverified"
    assert person.listing.status == "pending"


def test_original_agency_editor_cannot_inspect_after_transfer_or_revoke(request):
    case, _, staff = ready(request)
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    agency = person.agency
    path, data = link(staff, case, person)
    assert staff.post(path, data).status_code == 302
    person.agency = None
    person.individual = person.subject
    person.assigned_editor = None
    person.manager_version += 1
    person.save()
    AgencyMember.objects.filter(agency=agency).update(active=False)
    editor = User.objects.get(username="fixture-v1-editor")
    editor.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    client = Client()
    client.force_login(editor)
    session = client.session
    session["mfa_version"] = editor.mfa_version
    session.save()
    assert client.get(f"/en/moderation/rights/{case.pk}/").status_code == 403
    assert (
        client.post(
            f"/en/moderation/rights/{case.pk}/",
            {"purpose": "Inspect reference following changed representation"},
        ).status_code
        == 403
    )
    assert not client.get("/en/moderation/rights/").context["cases"]
    assert RightsAccess.objects.count() == 1


def test_concurrent_links_keep_one_profile_and_one_scope_snapshot(request):
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.core.exceptions import ValidationError
    from django.db import close_old_connections, connections

    from apps.safety.rights_actions import act

    case, user, _ = ready(request)
    targets = [
        Person.objects.get(subject__username=name).listing.pk
        for name in ["fixture-v1-individual", "fixture-v1-model-a"]
    ]
    barrier = Barrier(2)

    def propose(listing_id):
        close_old_connections()
        try:
            reviewer = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                result = act(
                    reviewer,
                    case.pk,
                    uuid.uuid4(),
                    2,
                    "link",
                    "Reference matches this synthetic profile",
                    link_listing_id=listing_id,
                )
                return result.person_id
            except ValidationError:
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(propose, targets))
    case.refresh_from_db()
    assert outcomes.count(None) == 1
    assert case.person_id in [value for value in outcomes if value]
    assert case.reported_subject_id == case.person.subject_id
    assert case.manager_version == case.person.manager_version
    assert case.scope_status == "unverified" and case.version == 3
    assert RightsAction.objects.filter(operation="link").count() == 1


def test_mobile_link_stays_unverified_and_get_hides_request_data(
    live_server, request, settings, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _ = ready(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    listing_id = str(person.listing.pk)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    path = f"/en/moderation/rights/{case.pk}/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            page.goto(live_server.url + path)
            page.get_by_role("link", name="Request actions", exact=True).click()
            page.locator("[name=operation]").select_option("link")
            page.locator("[name=link_listing_id]").fill(listing_id)
            page.locator("[name=reason]").fill(
                "Manual request reference identifies this synthetic profile"
            )
            page.get_by_role("button", name="Record assignment action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            expect(
                page.get_by_text("Identity and scope remain unverified.", exact=False)
            ).to_be_visible()
            page.reload()
            assert "rights-private@example.invalid" not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.person_id == person.pk and case.scope_status == "unverified"


def test_management_version_change_between_snapshot_and_lock_prevents_read(request, monkeypatch):
    case, _, staff = ready(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    path, data = link(staff, case, person)
    assert staff.post(path, data).status_code == 302
    original = Person.objects.select_for_update
    changed = False

    def interleaved_lock(*args, **kwargs):
        nonlocal changed
        if not changed:
            changed = True
            Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version + 1)
        return original(*args, **kwargs)

    monkeypatch.setattr(Person.objects, "select_for_update", interleaved_lock)
    response = staff.post(
        f"/en/moderation/rights/{case.pk}/",
        {"purpose": "Read scoped request during management transition"},
    )
    assert response.status_code == 409
    assert b"rights-private@example.invalid" not in response.content
    assert RightsAccess.objects.count() == 1
