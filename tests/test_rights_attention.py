import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import prepared

from apps.safety.models import RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)
PATH = "/en/moderation/rights/"


def ids(response):
    return {case.pk for case in response.context["cases"]}


def test_overdue_filter_uses_extended_target_without_changing_original_notice_target(request):
    from test_rights_extensions import payload
    from test_rights_extensions import prepared as extension_case

    case, _, staff, _, _ = extension_case(request)
    path, submitted = payload(staff, case)
    assert staff.post(path, submitted).status_code == 302
    original_due = timezone.now() - timedelta(days=1)
    RightsRequest.objects.filter(pk=case.pk).update(initial_due_at=original_due)
    assert not ids(staff.get(PATH, {"attention": "overdue"}))
    assert ids(staff.get(PATH)) == {case.pk}
    assert b"original notice target overdue" in staff.get(PATH).content
    case.refresh_from_db()
    assert case.initial_due_at == original_due and case.effective_due_at > timezone.now()


def test_attention_filters_and_pagination_only_include_authorized_cases(request):
    case, actor, staff = prepared(request)
    original = case.version, case.scope_status, case.status
    now = timezone.now()
    RightsRequest.objects.filter(pk=case.pk).update(initial_due_at=now - timedelta(days=1))
    assert ids(staff.get(PATH, {"attention": "overdue"})) == {case.pk}
    assert not ids(staff.get(PATH, {"attention": "due_soon"}))
    assert ids(staff.get(PATH, {"attention": "priority"})) == {case.pk}
    assert ids(staff.get(PATH, {"attention": "unassigned"})) == {case.pk}
    RightsRequest.objects.filter(pk=case.pk).update(
        initial_due_at=now + timedelta(days=3),
        assigned_to=actor,
    )
    assert ids(staff.get(PATH, {"attention": "due_soon"})) == {case.pk}
    assert not ids(staff.get(PATH, {"attention": "unassigned"}))
    assert staff.get(PATH, {"attention": "unknown"}).status_code == 400
    assert staff.get(PATH, {"attention": "media_failed"}).status_code == 403
    case.refresh_from_db()
    assert (case.version, case.scope_status, case.status) == original
    fields = {field.attname: getattr(case, field.attname) for field in case._meta.fields}
    rows = []
    for index in range(52):
        rows.append(
            RightsRequest(
                **(
                    fields
                    | {
                        "id": uuid.uuid4(),
                        "submission_key": uuid.uuid4(),
                        "receipt_digest": f"{index:064x}",
                        "actor_id": actor.pk if index == 51 else None,
                    }
                )
            )
        )
    RightsRequest.objects.bulk_create(rows)
    first = staff.get(PATH)
    second = staff.get(PATH, {"page": 2})
    assert len(ids(first)) == 50 and len(ids(second)) == 2
    assert not ids(first) & ids(second)
    assert rows[-1].pk not in ids(first) | ids(second)
    assert first["Cache-Control"] == "private, no-store"
    assert first["X-Robots-Tag"] == "noindex, nofollow"
    assert b"rights-private@example.invalid" not in first.content


def test_media_attention_survives_case_closure_and_respects_permissions_and_coi(
    request, settings, monkeypatch
):
    from test_media_operations import exhausted

    from apps.mediafiles.models import MediaErasure

    case, actor, person, job = exhausted(request, settings, monkeypatch)
    staff = Client()
    staff.force_login(actor)
    session = staff.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    RightsRequest.objects.filter(pk=case.pk).update(status="resolved")
    assert not ids(staff.get(PATH))
    response = staff.get(PATH, {"attention": "media_failed"})
    assert ids(response) == {case.pk}
    assert b"Review exhausted file deletion" in response.content
    assert job.blob.original.name.encode() not in response.content
    actor.user_permissions.remove(Permission.objects.get(codename="manage_media_erasure"))
    assert staff.get(PATH, {"attention": "media_failed"}).status_code == 403
    owner = person.agency.owner
    owner.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["review_rights_request", "manage_media_erasure"],
        )
    )
    manager = Client()
    manager.force_login(owner)
    session = manager.session
    session["mfa_version"] = owner.mfa_version
    session.save()
    assert not ids(manager.get(PATH, {"attention": "media_failed"}))
    actor.user_permissions.add(Permission.objects.get(codename="manage_media_erasure"))
    MediaErasure.objects.filter(pk=job.pk).update(status="queued", attempts=0)
    assert not ids(staff.get(PATH, {"attention": "media_failed"}))


def test_mobile_attention_filter_preserves_request(live_server, request, tmp_path, settings):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _ = prepared(request)
    RightsRequest.objects.filter(pk=case.pk).update(
        initial_due_at=timezone.now() - timedelta(days=1),
    )
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + PATH)
            page.get_by_label("Needs attention").select_option("overdue")
            page.get_by_role("button", name="Filter requests").click()
            expect(page).to_have_url(live_server.url + PATH + "?attention=overdue")
            expect(page.get_by_role("link", name="Inspect request")).to_have_count(1)
            page.reload()
            expect(page.get_by_label("Needs attention")).to_have_value("overdue")
            page.get_by_role("link", name="Inspect request").click()
            expect(page.get_by_role("heading", name="Private rights inspection")).to_be_visible()
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.status == "received" and case.version == 1
