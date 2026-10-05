"""Security boundaries of subject-account correction, before flow integration."""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.safety.rectification_account import source, validate

pytestmark = pytest.mark.django_db(transaction=True)


def test_account_source_is_subject_scoped_and_binds_credentials(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    with pytest.raises(RuntimeError):
        source(person)
    with transaction.atomic():
        person = Person.objects.select_for_update().get(pk=person.pk)
        before = source(person)
        assert before["subject"] == str(person.subject_id)
        assert before["email"] == person.subject.email
        assert person.agency.owner.email != before["email"]
        assert person.subject.password not in str(before)
        user = person.subject
        user.set_password("Synthetic-changed-password!847")
        user.save(update_fields=["password"])
        assert source(person)["authentication_digest"] != before["authentication_digest"]
        person.subject = None
        with pytest.raises(ValidationError, match="Linked subject"):
            source(person)


def test_account_whitelist_and_uniqueness_do_not_mutate_accounts(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    user = person.subject
    before = user.email, user.first_name, user.password, user.session_version
    with transaction.atomic():
        person = Person.objects.select_for_update().get(pk=person.pk)
        assert validate({"first_name": " Synthetic ", "email": "NEW@EXAMPLE.INVALID"}, person) == {
            "first_name": "Synthetic",
            "email": "new@example.invalid",
        }
        for value in [
            {"role": "agency"},
            {"password": "secret"},
            {"username": "other"},
            {"email": person.agency.owner.email.upper()},
            {"email": "invalid"},
            {"first_name": None},
            {"last_name": "x" * 151},
        ]:
            with pytest.raises(ValidationError):
                validate(value, person)
        user.refresh_from_db()
        assert (user.email, user.first_name, user.password, user.session_version) == before
        user.account_erased_at = timezone.now()
        user.save(update_fields=["account_erased_at"])
        with pytest.raises(ValidationError, match="erased"):
            validate({"first_name": "Synthetic"}, person)


def test_account_proposal_http_is_audited_encrypted_and_rejects_stale_source(
    request, settings, monkeypatch
):
    from uuid import uuid4

    from test_rights_responses import ready

    from apps.safety.crypto import unseal
    from apps.safety.models import RightsRectificationProposal

    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    user = person.subject
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    page = staff.post(
        path,
        initial
        | {
            "operation": "preview",
            "purpose": "Inspect subject account source before proposing correction",
        },
    )
    assert page.status_code == 200
    assert page.context["source_fields"]["account"]["email"] == user.email
    assert page.context["form"].initial["account_email"] == user.email
    assert user.password.encode() not in page.content
    original = user.first_name
    revisions_before = person.listing.revisions.count()
    data = initial | {
        "key": uuid4(),
        "operation": "propose",
        "fields": ["account"],
        "account_first_name": "Synthetic account correction",
        "account_last_name": "Synthetic surname",
        "account_email": "new-subject@example.invalid",
        "reason": "Private scoped account correction justification",
    }
    user.first_name = "Changed source while preparing proposal"
    user.save(update_fields=["first_name"])
    assert staff.post(path, data).status_code == 409
    assert not RightsRectificationProposal.objects.exists()
    user.first_name = original
    user.save(update_fields=["first_name"])
    assert staff.post(path, data).status_code == 302
    proposal = RightsRectificationProposal.objects.get()
    assert unseal(proposal.encrypted_changes)["account"] == {
        "first_name": data["account_first_name"],
        "last_name": data["account_last_name"],
        "email": data["account_email"],
    }
    assert data["account_email"] not in proposal.encrypted_changes
    user.refresh_from_db()
    assert user.first_name == original and user.email != data["account_email"]
    assert person.listing.revisions.count() == revisions_before
    assert staff.get(path).context["source_fields"] is None


def test_account_wait_precedes_revision_and_blob_locks_and_refreshes_credentials(
    request, settings, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue

    from django.db import connection, connections
    from test_photo_reuse_races import observe_blocked
    from test_rights_responses import ready

    from apps.core.accounts import token_user_state
    from apps.core.models import User
    from apps.listings.models import Revision
    from apps.mediafiles.models import Blob
    from apps.safety.rights_rectification import source_snapshot
    from apps.safety.rights_scope import locked_case

    case, _, _, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    blob = revision.photos.first().blob
    pids = Queue()

    def reading():
        connections.close_all()
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pids.put(cursor.fetchone()[0])
                locked_request, locked_person, listing = locked_case(case.pk, lock_listing=True)
                return source_snapshot(locked_request, locked_person, listing)[1]["account"]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=person.subject_id)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(reading)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            # These rows must remain available while the snapshot waits for User.
            Revision.objects.select_for_update(nowait=True).get(pk=revision.pk)
            Blob.objects.select_for_update(nowait=True).get(pk=blob.pk)
            user.set_password("Synthetic-password-changed-during-wait!847")
            user.save(update_fields=["password"])
            expected_digest = token_user_state(user)
        result = future.result(timeout=10)
    assert result["authentication_digest"] == expected_digest
    assert user.password not in str(result)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_account_proposal_login_mfa_audited_source_and_reload(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright
    from test_rights_responses import ready

    from apps.safety.crypto import unseal
    from apps.safety.models import RightsRectificationProposal

    settings.DEBUG = True
    case, _, _, _, _, person = ready(request, settings, monkeypatch, "rectify")
    before = person.subject.email, person.subject.first_name, person.subject.session_version
    revisions = person.listing.revisions.count()
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    path = f"/{language}/moderation/rights/{case.pk}/rectification/"
    labels = {
        "account": "Your account" if language == "en" else "Tu cuenta",
        "inspect": "Private rights inspection"
        if language == "en"
        else "Consulta privada de derechos",
        "submit": "Record correction action"
        if language == "en"
        else "Registrar acción de rectificación",
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
            page.goto(live_server.url + path)
            expect(page.locator("[name=account_email]")).to_have_value("")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Inspect scoped subject account fields before mobile correction proposal"
            )
            page.get_by_role("button", name=labels["submit"], exact=True).click()
            expect(page.locator("[name=account_email]")).to_have_value(before[0])
            page.locator("[name=fields][value=account]").check()
            page.locator("[name=account_first_name]").fill("Mobile proposed account name")
            page.locator("[name=account_last_name]").fill("Mobile proposed surname")
            page.locator("[name=account_email]").fill("mobile-proposed@example.invalid")
            page.locator("[name=operation]").select_option("propose")
            page.locator("[name=reason]").fill(
                "Independent scoped correction requested through mobile form"
            )
            page.get_by_role("button", name=labels["submit"], exact=True).click()
            expect(page.get_by_role("heading", name=labels["inspect"], exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role("heading", name=labels["inspect"], exact=True)).to_be_visible()
            page.goto(live_server.url + path)
            expect(page.locator("[name=account_email]")).to_have_value("")
            assert "mobile-proposed@example.invalid" not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    person.subject.refresh_from_db()
    proposal = RightsRectificationProposal.objects.get()
    assert unseal(proposal.encrypted_changes) == {
        "account": {
            "first_name": "Mobile proposed account name",
            "last_name": "Mobile proposed surname",
            "email": "mobile-proposed@example.invalid",
        }
    }
    assert "mobile-proposed@example.invalid" not in proposal.encrypted_changes
    assert (
        person.subject.email,
        person.subject.first_name,
        person.subject.session_version,
    ) == before
    assert person.listing.revisions.count() == revisions
