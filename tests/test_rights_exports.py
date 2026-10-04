import json
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import action
from test_rights_intake import data
from test_rights_linking import link
from test_rights_messages import clarification
from test_rights_verification import read

from apps.core.models import Person, User
from apps.safety.models import (
    RightsExport,
    RightsExportDownload,
    RightsExportPreview,
    RightsRequest,
)
from apps.safety.rights_exports import generate, preview
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, subject_username="fixture-v1-model-a"):
    request.getfixturevalue("directory")
    settings.RIGHTS_VERIFICATION_BACKEND = "simulator"
    client = Client()
    receipt = client.post("/en/safety/rights/", data(client, kind="access")).url
    case = RightsRequest.objects.get()
    user, staff = reviewer()
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_rights_request", "execute_rights_request"])
    )
    path, claim = action(staff, case, "claim")
    assert staff.post(path, claim).status_code == 302
    read(staff, case)
    person = Person.objects.get(subject__username=subject_username)
    path, linked = link(staff, case, person)
    assert staff.post(path, linked).status_code == 302
    read(staff, case)
    case.refresh_from_db()
    user = User.objects.get(pk=user.pk)
    proof = start(user, case.pk, uuid.uuid4(), case.version, "Synthetic profile access procedure")
    case.refresh_from_db()
    verifier = User.objects.get(username="fixture-v1-visitor")
    verifier.mfa_enabled = True
    verifier.save(update_fields=["mfa_enabled"])
    verifier.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_rights_request", "verify_rights_scope"])
    )
    other = Client()
    other.force_login(verifier)
    session = other.session
    session["mfa_version"] = verifier.mfa_version
    session.save()
    read(other, case)
    receive_event(
        verifier,
        simulate_event(
            proof.pk,
            uuid.uuid4(),
            case.version,
            "passed",
            "Independent synthetic profile scope assessment",
        ),
    )
    case.refresh_from_db()
    read(staff, case)
    return case, user, staff, client, receipt, person


def make_copy(case, user):
    source = preview(user, case.pk, case.version, "Review profile copy and redact third-party text")
    source["profile"]["alias"] = "Reviewed synthetic profile"
    source["revisions"][0]["description"] = "Reviewed description with third-party details removed"
    key = uuid.uuid4()
    export = generate(
        user, case.pk, key, case.version, "Release reviewed partial profile copy", source
    )
    assert (
        generate(
            user, case.pk, key, case.version, "Release reviewed partial profile copy", source
        ).pk
        == export.pk
    )
    return export


def url(receipt, export):
    return receipt + f"export/{export.pk}/"


def test_encrypted_reviewed_copy_download_without_account_excludes_other_data(request, settings):
    case, user, _, client, receipt, person = prepared(request, settings)
    export = make_copy(case, user)
    assert "Reviewed description" not in export.encrypted_payload
    assert RightsExport.objects.count() == RightsExportPreview.objects.count() == 1
    page = client.get(receipt)
    assert len(page.context["exports"]) == 1
    assert b"Reviewed description" not in page.content and b"Download private copy" in page.content
    path = url(receipt, export)
    assert client.get(path).status_code == 405
    payload = {"key": uuid.uuid4()}
    response = client.post(path, payload)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert "attachment" in response["Content-Disposition"]
    copy = response.json()
    assert copy["partial"] is True and copy["simulation"] is True
    assert copy["profile"]["alias"] == "Reviewed synthetic profile"
    assert set(item["revision"] for item in copy["revisions"]) == set(
        str(pk) for pk in person.listing.revisions.values_list("pk", flat=True)
    )
    other = Person.objects.get(subject__username="fixture-v1-model-b")
    serialized = json.dumps(copy)
    assert str(other.pk) not in serialized
    assert "rights-private@example.invalid" not in serialized
    assert "payload_digest" not in serialized
    assert all(item["contacts"]["phone"] == "" for item in copy["revisions"])
    assert copy["subject_account"]["email"] == person.subject.email
    assert person.agency.owner.email not in serialized
    assert other.subject.email not in serialized
    assert "Independent synthetic" not in serialized
    assert client.post(path, payload).status_code == 200
    assert RightsExportDownload.objects.count() == 1
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    bad = receipt.rstrip("/").rsplit("/", 1)[0] + "/" + "a" * 43 + f"/export/{export.pk}/"
    assert client.post(bad, payload).status_code == 404
    case.refresh_from_db()
    assert case.status == "reviewing" and case.version == 6


def test_new_clarification_or_manager_change_revokes_download(request, settings):
    case, user, _, client, receipt, person = prepared(request, settings)
    export = make_copy(case, user)
    path = url(receipt, export)
    Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version + 1)
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 404
    Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version)
    assert client.post(receipt, clarification(client, receipt)).status_code == 302
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 404
    assert not client.get(receipt).context["exports"]
    assert not RightsExportDownload.objects.exists()


def test_source_drift_extra_fields_foreign_revision_and_expiry_blocked(request, settings):
    from django.core.exceptions import ValidationError

    case, user, _, client, receipt, person = prepared(request, settings)
    source = preview(
        user, case.pk, case.version, "Review current profile copy and third-party data"
    )
    with pytest.raises(ValidationError):
        generate(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "Release current reviewed copy",
            {**source, "foreign_account": "injected"},
        )
    foreign = json.loads(json.dumps(source))
    foreign["revisions"][0]["revision"] = str(
        Person.objects.get(subject__username="fixture-v1-model-b").listing.revisions.first().pk
    )
    with pytest.raises(ValidationError):
        generate(
            user, case.pk, uuid.uuid4(), case.version, "Release current reviewed copy", foreign
        )
    revision = person.listing.revisions.first()
    revision.title = "Source changed after preview"
    revision.save(update_fields=["title"])
    with pytest.raises(ValidationError):
        generate(user, case.pk, uuid.uuid4(), case.version, "Release current reviewed copy", source)
    export = make_copy(case, user)
    path = url(receipt, export)
    settings.PRODUCTION = True
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 404
    settings.PRODUCTION = False
    RightsExport.objects.filter(pk=export.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 404
    assert not RightsExportDownload.objects.exists()


def test_mobile_audited_preview_generate_and_anonymous_download(
    live_server, request, settings, tmp_path
):
    import shutil
    from pathlib import Path

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, receipt, _ = prepared(request, settings)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
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
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/")
            page.get_by_role("link", name="Prepare private copy", exact=True).click()
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill("Review export texts before private copy release")
            page.get_by_role("button", name="Record copy action", exact=True).click()
            expect(page.locator("[name=copy]")).not_to_have_value("")
            page.locator("[name=reason]").fill("Release reviewed synthetic private profile copy")
            page.get_by_role("button", name="Record copy action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt)
            with anonymous.expect_download() as item:
                anonymous.get_by_role("button", name="Download private copy", exact=True).click()
            copied = json.loads(Path(item.value.path()).read_text())
            assert copied["partial"] is True and copied["simulation"] is True
            anonymous.reload()
            assert b"rights-private@example.invalid".decode() not in anonymous.content()
        finally:
            browser.close()
    assert RightsExportDownload.objects.count() == 1


def test_concurrent_generation_is_one_encrypted_copy_and_one_case_version(request, settings):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    case, user, _, client, receipt, _ = prepared(request, settings)
    source = preview(user, case.pk, case.version, "Review source for concurrent export retry")
    barrier = Barrier(2)
    key = uuid.uuid4()

    def create(_):
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            return generate(
                actor,
                case.pk,
                key,
                case.version,
                "Release reviewed partial copy concurrently",
                source,
            ).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        ids = list(executor.map(create, range(2)))
    assert ids[0] == ids[1] and RightsExport.objects.count() == 1
    case.refresh_from_db()
    assert case.version == 6
    export = RightsExport.objects.get()
    export.proof.scope = "representation"
    export.proof.save(update_fields=["scope"])
    assert client.post(url(receipt, export), {"key": uuid.uuid4()}).status_code == 404
    assert not RightsExportDownload.objects.exists()
