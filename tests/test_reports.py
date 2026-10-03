import shutil
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connections
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.safety.crypto import cipher
from apps.safety.models import Report

pytestmark = pytest.mark.django_db(transaction=True)


def payload(client, **changes):
    form = client.get("/en/safety/report/").context["form"]
    return {
        **form.initial,
        "mode": "general",
        "reason": "nonconsent",
        "reference": "Synthetic profile reference",
        "explanation": "Synthetic private report of unapproved publication.",
        "good_faith": "on",
        **changes,
    }


def test_anonymous_receipt_private_encryption_replay_and_formal_rules(request):
    request.getfixturevalue("directory")
    client = Client()
    data = payload(client, email="private-reporter@example.invalid", name="Private reporter")
    response = client.post("/en/safety/report/", data)
    assert response.status_code == 302
    report = Report.objects.get()
    assert report.priority == 0 and report.actor_id is None
    assert (
        "private-reporter" not in report.encrypted_payload
        and "unapproved" not in report.encrypted_payload
    )
    assert b"private-reporter@example.invalid" in cipher().decrypt(
        report.encrypted_payload.encode()
    )
    receipt = client.get(response.url)
    assert receipt.status_code == 200 and b"Report received" in receipt.content
    assert (
        receipt["Cache-Control"] == "private, no-store"
        and receipt["X-Robots-Tag"] == "noindex, nofollow"
    )
    assert b"Private reporter" not in receipt.content and b"unapproved" not in receipt.content
    assert client.get(response.url.rsplit("/", 2)[0] + "/" + "x" * 43 + "/").status_code == 404
    assert client.post("/en/safety/report/", data).url == response.url
    assert Report.objects.count() == 1
    assert (
        client.post(
            "/en/safety/report/",
            data | {"explanation": "Different private explanation for the same request."},
        ).status_code
        == 409
    )
    formal = payload(client, mode="formal")
    assert client.post("/en/safety/report/", formal).status_code == 400
    assert client.post("/en/safety/report/", formal | {"exception": "on"}).status_code == 302
    assert client.post("/en/safety/report/", payload(client, good_faith="")).status_code == 400


def test_queue_permissions_mfa_coi_and_public_route_account_gate(request):
    request.getfixturevalue("directory")
    client = Client()
    person = Person.objects.get(individual__username="fixture-v1-individual")
    detail = client.get(f"/en/listing/{person.listing.pk}/")
    target = detail.context["report_target"]
    response = client.post("/en/safety/report/", payload(client, target=target))
    assert (
        response.status_code == 302
        and Report.objects.get().revision_id == person.listing.approved_revision_id
    )
    reviewer = Client()
    moderator = User.objects.get(username="fixture-v1-moderator")
    reviewer.force_login(moderator)
    session = reviewer.session
    session["mfa_version"] = moderator.mfa_version
    session.save()
    assert reviewer.get("/en/moderation/reports/").status_code == 403
    moderator.user_permissions.add(Permission.objects.get(codename="review_report"))
    assert len(reviewer.get("/en/moderation/reports/").context["reports"]) == 1
    Report.objects.update(actor=moderator)
    assert len(reviewer.get("/en/moderation/reports/").context["reports"]) == 0
    user = User.objects.get(username="fixture-v1-visitor")
    user.email_verified_at = None
    user.save(update_fields=["email_verified_at"])
    client.force_login(user)
    assert client.get("/en/safety/report/").status_code == 200
    assert client.get(response.url).status_code == 200
    assert client.post("/en/safety/report/", payload(client, target="tampered")).status_code == 400


def test_concurrent_public_report_replay_is_one_case(request):
    request.getfixturevalue("directory")
    data = payload(Client())
    barrier = Barrier(2)

    def submit():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return Client().post("/en/safety/report/", data).url
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(submit) for _ in range(2)]
        assert len({future.result() for future in futures}) == 1
    assert Report.objects.count() == 1


def test_mobile_report_without_account_and_private_receipt_reload(live_server, request, settings):
    settings.DEBUG = True
    request.getfixturevalue("directory")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/")
            page.locator("article.card h2 a").first.click()
            page.get_by_role("link", name="Report content", exact=True).click()
            target = parse_qs(urlsplit(page.url).query)["target"][0]
            assert target
            page.locator("[name=mode]").select_option("general")
            page.locator("[name=reason]").select_option("nonconsent")
            page.locator("[name=email]").fill("mobile-recipient@example.invalid")
            page.locator("[name=explanation]").fill(
                "Synthetic report for a privacy review, without real personal data."
            )
            page.locator("[name=good_faith]").check()
            page.get_by_role("button", name="Send report", exact=True).click()
            expect(page.get_by_role("heading", name="Report received", exact=True)).to_be_visible()
            expect(page.get_by_role("heading", name="Notices", exact=True)).to_be_visible()
            expect(
                page.get_by_text("ack · Queued; delivery not confirmed.", exact=True)
            ).to_be_visible()
            page.reload()
            expect(page.get_by_role("heading", name="Report received", exact=True)).to_be_visible()
            assert "/account/" not in page.url
            assert "mobile-recipient@example.invalid" not in page.content()
        finally:
            browser.close()


def test_expired_receipt_never_logs_secret_or_contact(request, caplog):
    from datetime import timedelta

    from django.utils import timezone

    request.getfixturevalue("directory")
    client = Client()
    data = payload(client, email="confidential@example.invalid")
    response = client.post("/en/safety/report/", data)
    Report.objects.update(receipt_expires_at=timezone.now() - timedelta(seconds=1))
    assert client.get(response.url).status_code == 404
    assert data["receipt_secret"] not in caplog.text
    assert "confidential@example.invalid" not in caplog.text


def test_report_crypto_requires_real_dedicated_key_in_production(settings):
    from cryptography.fernet import Fernet

    from apps.safety.crypto import seal

    settings.PRODUCTION = True
    settings.SAFETY_ENCRYPTION_KEY = ""
    with pytest.raises(ValueError, match="Safety encryption key required"):
        seal({"email": "synthetic@example.invalid"})
    settings.SAFETY_ENCRYPTION_KEY = Fernet.generate_key().decode()
    encrypted = seal({"email": "synthetic@example.invalid"})
    assert b"synthetic@example.invalid" in cipher().decrypt(encrypted.encode())
