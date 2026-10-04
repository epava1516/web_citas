import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import requires_mfa
from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import Complaint, ComplaintAccess, Report, Restriction

pytestmark = pytest.mark.django_db(transaction=True)


def payload(client, **changes):
    form = client.get("/en/safety/complaints/").context["form"]
    return form.initial | {
        "relationship": "represented",
        "reference": "Synthetic decision reference",
        "explanation": "Private review request by represented person without an agency login.",
        "email": "own-channel@example.invalid",
        **changes,
    }


def moderator():
    user = User.objects.get(username="fixture-v1-moderator")
    user.user_permissions.add(Permission.objects.get(codename="review_complaint"))
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    return user, client


def test_anonymous_encrypted_intake_minimal_receipt_replay_and_no_automatic_change(request):
    request.getfixturevalue("directory")
    client = Client()
    data = payload(client)
    response = client.post("/en/safety/complaints/", data)
    assert response.status_code == 302
    case = Complaint.objects.get()
    assert case.actor_id is None and case.status == "received" and case.version == 1
    assert "own-channel" not in case.encrypted_payload
    assert unseal(case.encrypted_payload)["relationship"] == "represented"
    receipt = client.get(response.url)
    assert receipt.status_code == 200 and b"Review request received" in receipt.content
    assert (
        b"own-channel" not in receipt.content and b"Private review request" not in receipt.content
    )
    assert (
        receipt["Cache-Control"] == "private, no-store"
        and receipt["X-Robots-Tag"] == "noindex, nofollow"
    )
    assert client.post("/en/safety/complaints/", data).url == response.url
    assert Complaint.objects.count() == 1
    assert (
        client.post(
            "/en/safety/complaints/",
            data | {"explanation": "A different request using the same submission key."},
        ).status_code
        == 409
    )
    assert not Report.objects.exists() and not Restriction.objects.exists()


def test_invalid_secret_expiry_csrf_and_rate_limit(request, caplog):
    request.getfixturevalue("directory")
    client = Client(enforce_csrf_checks=True)
    data = payload(client)
    assert client.post("/en/safety/complaints/", data).status_code == 403
    data["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
    response = client.post("/en/safety/complaints/", data)
    assert response.status_code == 302
    assert client.get(response.url.rsplit("/", 2)[0] + "/" + "x" * 43 + "/").status_code == 404
    Complaint.objects.update(receipt_expires_at=timezone.now() - timedelta(seconds=1))
    assert client.get(response.url).status_code == 404
    assert data["receipt_secret"] not in caplog.text and data["email"] not in caplog.text
    for _ in range(9):
        assert (
            client.post("/en/safety/complaints/", data | {"relationship": "unknown"}).status_code
            == 400
        )
    assert client.post("/en/safety/complaints/", data).status_code == 429


def test_audited_triage_separate_permission_mfa_and_own_case_exclusion(request):
    request.getfixturevalue("directory")
    visitor = Client()
    receipt = visitor.post("/en/safety/complaints/", payload(visitor)).url
    case = Complaint.objects.get()
    user, staff = moderator()
    path = f"/en/moderation/complaints/{case.pk}/"
    assert len(staff.get("/en/moderation/complaints/").context["complaints"]) == 1
    assert b"own-channel" not in staff.get(path).content and not ComplaintAccess.objects.exists()
    assert staff.post(path, {"purpose": "short"}).status_code == 400
    response = staff.post(path, {"purpose": "Triage privately submitted review reference"})
    assert response.status_code == 200 and b"own-channel@example.invalid" in response.content
    access = ComplaintAccess.objects.get()
    assert access.actor_id == user.pk and access.case_version == case.version
    assert (
        b"own-channel" not in staff.get(path).content
        and b"own-channel" not in visitor.get(receipt).content
    )
    assert Client().get(path).status_code == 302
    Complaint.objects.filter(pk=case.pk).update(actor=user)
    assert (
        staff.post(path, {"purpose": "Inspect my own request with staff role"}).status_code == 403
    )
    assert not staff.get("/en/moderation/complaints/").context["complaints"]
    assert ComplaintAccess.objects.count() == 1
    user.user_permissions.remove(Permission.objects.get(codename="review_complaint"))
    user.user_permissions.add(Permission.objects.get(codename="review_report"))
    assert staff.get("/en/moderation/complaints/").status_code == 403


def test_public_entry_bypasses_outdated_account_gate_and_nonstaff_review_requires_mfa(request):
    request.getfixturevalue("directory")
    user = User.objects.get(username="fixture-v1-visitor")
    user.email_verified_at = None
    user.save(update_fields=["email_verified_at"])
    user.user_permissions.add(Permission.objects.get(codename="review_complaint"))
    assert not user.is_staff and not user.mfa_enabled and requires_mfa(user)
    client = Client()
    client.force_login(user)
    data = payload(client)
    response = client.post("/en/safety/complaints/", data)
    assert response.status_code == 302 and client.get(response.url).status_code == 200
    assert Complaint.objects.get().actor_id == user.pk
    assert client.get("/en/moderation/complaints/").status_code == 302
    assert not ComplaintAccess.objects.exists()


def test_concurrent_intake_is_one_case_and_one_receipt(request):
    request.getfixturevalue("directory")
    data = payload(Client())
    barrier = Barrier(2)

    def submit():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = Client().post("/en/safety/complaints/", data)
            assert response.status_code == 302
            return response.url
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(submit) for _ in range(2)]
        assert len({future.result() for future in futures}) == 1
    assert Complaint.objects.count() == 1


def test_actor_replay_foreign_receipt_and_escaped_reference_do_not_confer_access(request):
    request.getfixturevalue("directory")
    client = Client()
    text = "<script>window.complaintLeak=true</script> Synthetic private review request"
    data = payload(client, explanation=text, reference="/en/moderation/reports/unknown-case/")
    response = client.post("/en/safety/complaints/", data)
    first = Complaint.objects.get()
    other = client.post("/en/safety/complaints/", payload(client, relationship="advertiser"))
    second = Complaint.objects.exclude(pk=first.pk).get()
    assert client.get(response.url.replace(str(first.pk), str(second.pk))).status_code == 404
    assert client.get(other.url).status_code == 200
    client.force_login(User.objects.get(username="fixture-v1-visitor"))
    assert client.post("/en/safety/complaints/", data).status_code == 409
    assert Complaint.objects.count() == 2
    assert not Report.objects.exists()
    _, staff = moderator()
    path = f"/en/moderation/complaints/{first.pk}/"
    viewed = staff.post(
        path, {"purpose": "Inspect declared reference without following a remote URL"}
    )
    assert viewed.status_code == 200
    assert (
        b"&lt;script&gt;" in viewed.content
        and b"<script>window.complaintLeak" not in viewed.content
    )
    assert b"complaintLeak" not in Client().get(response.url).content
    assert ComplaintAccess.objects.get().complaint_id == first.pk


@pytest.mark.parametrize(
    "method,path,status",
    [
        (
            "post",
            "/en/safety/complaints/00000000-0000-0000-0000-000000000000/" + "x" * 43 + "/",
            405,
        ),
        (
            "get",
            "/en/safety/complaints/00000000-0000-0000-0000-000000000000/" + "x" * 43 + "/",
            404,
        ),
        ("delete", "/en/safety/complaints/", 405),
        ("get", "/en/safety/complaints/not-a-valid-case-id/", 404),
    ],
)
def test_channel_errors_keep_privacy_headers(request, method, path, status):
    request.getfixturevalue("directory")
    response = getattr(Client(), method)(path)
    assert response.status_code == status
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert response["Referrer-Policy"] == "same-origin"


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_intake_without_agency_login_and_receipt_reload(
    live_server, request, settings, language
):
    settings.DEBUG = True
    request.getfixturevalue("directory")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/")
            page.get_by_role(
                "link",
                name="Request decision review"
                if language == "en"
                else "Solicitar revisión de decisión",
                exact=True,
            ).click()
            page.locator("[name=relationship]").select_option("represented")
            page.locator("[name=reference]").fill("Synthetic public decision reference")
            page.locator("[name=explanation]").fill(
                "Request review of a decision using my own channel, without agency credentials."
            )
            page.locator("[name=email]").fill("mobile-own@example.invalid")
            page.get_by_role(
                "button",
                name="Send review request" if language == "en" else "Enviar reclamación",
                exact=True,
            ).click()
            heading = "Review request received" if language == "en" else "Reclamación recibida"
            expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible()
            assert (
                "/account/" not in page.url and "mobile-own@example.invalid" not in page.content()
            )
        finally:
            browser.close()


def test_mobile_reviewer_login_mfa_and_audited_delivery_then_reload_hides(
    live_server, request, settings, tmp_path
):
    settings.DEBUG = True
    request.getfixturevalue("directory")
    client = Client()
    response = client.post("/en/safety/complaints/", payload(client))
    assert response.status_code == 302
    case = Complaint.objects.get()
    moderator()
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
            expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            page.get_by_role("link", name="Private review requests", exact=True).click()
            page.get_by_role("link", name="Inspect review request", exact=True).click()
            assert "own-channel@example.invalid" not in page.content()
            page.locator("[name=purpose]").fill(
                "Triage represented person's independent review request"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(
                page.get_by_role("heading", name="Restricted information", exact=True)
            ).to_be_visible()
            assert "own-channel@example.invalid" in page.content()
            # GET after POST hides the evidence again; only the POST is audited.
            page.goto(live_server.url + f"/en/moderation/complaints/{case.pk}/")
            assert "own-channel@example.invalid" not in page.content()
        finally:
            browser.close()
    assert ComplaintAccess.objects.filter(complaint=case).count() == 1
