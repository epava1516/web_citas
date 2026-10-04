import uuid

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import User
from apps.safety.models import RightsRectificationNotification, RightsRectificationReview
from apps.safety.rights_actions import act
from apps.safety.rights_rectification import preview, propose

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independent synthetic correction assessment with minimized internal grounds"
EXACT_DESCRIPTION = "  Corrected synthetic description.\n\nSecond paragraph.  "


def independent_case(
    request,
    settings,
    monkeypatch,
    *,
    with_receipt=False,
    changes=None,
    subject_username="fixture-v1-model-a",
    correct_location=False,
    correct_catalog=False,
    correct_rates=False,
    clear_rates=False,
    correct_contacts=False,
    clear_contacts=False,
    correct_details=False,
    clear_details=False,
    correct_photos=False,
    clear_photos=False,
    replacement_photo=False,
):
    case, original, staff, client, receipt, person = ready(
        request, settings, monkeypatch, "rectify", subject_username=subject_username
    )
    assert person.subject.username == subject_username
    if correct_location:
        from apps.catalog.models import Municipality, PostalCode, Zone

        source = person.listing.approved_revision
        assert source and source.municipality_id
        city = Municipality.objects.filter(active=True).exclude(pk=source.municipality_id).first()
        assert city is not None
        postal = PostalCode.objects.create(code="99981", source=city.source, public_safe=True)
        postal.municipalities.add(city)
        zone = Zone.objects.create(
            code="synthetic-correction-area",
            name="Synthetic correction area",
            municipality=city,
            source=city.source,
        )
        changes = {
            **(changes or {"alias": "Synthetic reviewed correction"}),
            "location": {
                "municipality": city.pk,
                "postal_code": postal.pk,
                "zone": zone.pk,
            },
        }
    if correct_catalog:
        from apps.catalog.models import Category, Service

        category = Category.objects.create(
            slug="synthetic-corrected-category",
            name_es="Synthetic corrected category",
            name_en="Synthetic corrected category",
        )
        service = Service.objects.create(
            slug="synthetic-corrected-service",
            category=category,
            name_es="Synthetic corrected service",
            name_en="Synthetic corrected service",
        )
        changes = {
            **(changes or {"alias": "Synthetic reviewed correction"}),
            "catalog": {"categories": [category.pk], "services": [service.pk]},
        }
    if correct_rates:
        changes = {
            **(changes or {"alias": "Synthetic reviewed correction"}),
            "rates": [
                {
                    "concept": "Synthetic corrected consult",
                    "mode": "consult",
                    "amount": None,
                    "currency": "EUR",
                    "duration_minutes": None,
                },
                {
                    "concept": "Synthetic corrected fixed",
                    "mode": "fixed",
                    "amount": "90.00",
                    "currency": "EUR",
                    "duration_minutes": 60,
                },
            ],
        }
    if clear_rates:
        assert correct_rates
        changes["rates"] = []
    if correct_contacts:
        from django.utils import timezone

        from apps.core.models import PhoneClaim

        # Synthetic verification record, not evidence of delivery of a real SMS.
        replacement = PhoneClaim.objects.create(
            phone="+34600000991",
            individual_id=person.individual_id,
            agency_id=person.agency_id,
            verified_at=timezone.now(),
            verification_procedure="simulator-v1",
        )
        changes = {
            **(changes or {"alias": "Synthetic reviewed correction"}),
            "contacts": {
                "phone": "" if clear_contacts else replacement.phone,
                "whatsapp": not clear_contacts,
                "telegram": "" if clear_contacts else "synthetic_contact",
            },
        }
    if correct_details:
        from apps.catalog.models import Municipality

        travel_city = (
            Municipality.objects.filter(active=True)
            .exclude(pk=person.listing.approved_revision.municipality_id)
            .first()
        )
        assert travel_city
        changes = {
            **(changes or {"alias": "Synthetic reviewed correction"}),
            "details": {
                "content_language": "en",
                "profile_type": "other",
                "spoken_languages": ["en", "fr"],
                "days": ["2", "5"],
                "time_slot": "evening",
                "reception": True,
                "travel": True,
                "travel_areas": [travel_city.pk],
            },
        }
    if clear_details:
        assert correct_details
        changes["details"].update(
            spoken_languages=[],
            days=[],
            time_slot="",
            reception=False,
            travel=False,
            travel_areas=[],
        )
    if correct_photos:
        from test_rectification_photos import add_source_photo

        from apps.safety.rectification_photos import source as photo_source

        source = person.listing.approved_revision
        add_source_photo(source)
        changes = {
            **(changes or {"alias": "Synthetic reviewed correction"}),
            "photos": [] if clear_photos else list(reversed(photo_source(source))),
        }
    original.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["manage_rights_assignment", "verify_rights_scope", "review_rectification"]
        )
    )
    original = User.objects.get(pk=original.pk)
    if changes:
        source = person.listing.approved_revision
        assert source is not None and source.municipality_id
        # Include a synthetic travel area before proposal, so every relation copy is exercised.
        source.travel_areas.add(source.municipality)
    preview(
        original, case.pk, case.version, "Inspect scoped current fields for correction proposal"
    )
    if replacement_photo:
        source = person.listing.approved_revision
        from django.core.files.uploadedfile import SimpleUploadedFile
        from test_photos import raw_image

        from apps.safety.rectification_uploads import upload

        item = upload(
            original,
            case.pk,
            uuid.uuid4(),
            case.version,
            SimpleUploadedFile(
                "synthetic-replacement.jpg", raw_image(947), content_type="image/jpeg"
            ),
            REASON,
        )
        if not clear_photos:
            changes["photos"] = [
                str(item.photo_id),
                str(source.photos.filter(removed_at__isnull=True).first().pk),
            ]
        preview(
            original,
            case.pk,
            case.version,
            "Inspect source and processed replacement before proposed correction",
        )
    proposal = propose(
        original,
        case.pk,
        uuid.uuid4(),
        case.version,
        changes or {"alias": "Synthetic reviewed correction"},
        REASON,
    )
    path = f"/en/moderation/rights/{case.pk}/rectification/{proposal.pk}/review/"
    assert staff.get(path).status_code == 403
    case.refresh_from_db()
    act(original, case.pk, uuid.uuid4(), case.version, "unassign", REASON)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["review_rights_request", "execute_rights_request", "review_rectification"]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    case.refresh_from_db()
    act(reviewer, case.pk, uuid.uuid4(), case.version, "claim", REASON)
    fresh(case, reviewer, other, original, staff)
    result = case, reviewer, other, person, proposal, path
    return (*result, client, receipt) if with_receipt else result


@pytest.mark.parametrize("outcome", ["approved", "rejected"])
def test_independent_audited_review_needs_fresh_source_and_preserves_publication(
    request, settings, monkeypatch, outcome
):
    case, reviewer, other, person, _, path = independent_case(request, settings, monkeypatch)
    data = {
        "key": uuid.uuid4(),
        "version": case.version,
        "operation": "review",
        "outcome": outcome,
        "reason": REASON,
    }
    assert other.post(path, data).status_code == 409
    preview(
        reviewer, case.pk, case.version, "Read unchanged current correction source independently"
    )
    assert other.post(path, data).status_code == 409
    inspected = other.post(
        path,
        {
            "key": uuid.uuid4(),
            "version": case.version,
            "operation": "inspect",
            "purpose": "Read proposed changes before independent correction review",
        },
    )
    assert inspected.status_code == 200 and inspected.context["changes"] == {
        "alias": "Synthetic reviewed correction"
    }
    assert other.get(path).context["changes"] is None
    before = person.alias, person.listing.status, person.listing.lifecycle_version
    assert other.post(path, data).status_code == 302
    assert other.post(path, data).status_code == 302
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert (person.alias, person.listing.status, person.listing.lifecycle_version) == before
    assert RightsRectificationReview.objects.get().outcome == outcome
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    reviewer.user_permissions.remove(Permission.objects.get(codename="review_rectification"))
    assert other.post(path, data).status_code == 403


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_independent_source_and_proposal_review(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    labels = {
        "Your account": "Tu cuenta",
        "Independent correction review": "Revisión independiente de rectificación",
        "Record correction action": "Registrar acción de rectificación",
        "Review correction proposal": "Revisar propuesta de rectificación",
        "Record review action": "Registrar acción de revisión",
        "Private rights inspection": "Consulta privada de derechos",
        "Private correction notices": "Avisos privados de rectificación",
        "Confirm receipt": "Confirmar recepción",
        "Receipt recorded": "Recepción registrada",
        "Review recipient history": "Revisar historial de destinatarios",
        "Correction recipient history": "Historial de destinatarios de rectificación",
        "Record access and review history": "Registrar consulta y revisar historial",
        "Audited historical summary": "Resumen histórico consultado",
        "Assess recipients and gaps": "Evaluar destinatarios y lagunas",
        "Propose recipient assessment": "Proponer evaluación de destinatarios",
        "Record assessment action": "Registrar acción de evaluación",
        "Review recipient assessment": "Revisar evaluación de destinatarios",
        "Independent recipient assessment review": "Revisión independiente de destinatarios",
        "Record independent review action": "Registrar acción de revisión independiente",
        "Audited proposed decisions": "Decisiones propuestas consultadas",
    }

    def label(value):
        return labels[value] if language == "es" else value

    settings.DEBUG = True
    case, reviewer, other, person, proposal, path, client, receipt = independent_case(
        request,
        settings,
        monkeypatch,
        with_receipt=True,
        correct_location=True,
        correct_catalog=True,
        correct_rates=True,
        correct_contacts=True,
        correct_details=True,
        correct_photos=True,
        replacement_photo=True,
    )
    historic_photo_ids = list(person.listing.approved_revision.photos.values_list("pk", flat=True))
    path = path.replace("/en/", f"/{language}/")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "respond_rights_request",
                "manage_rights_assignment",
                "review_recipient_assessment",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    from apps.core.mfa import encrypt

    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.save(update_fields=["mfa_secret_encrypted"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["visitor"]
    manager = person.agency.owner
    manager_secret = pyotp.random_base32()
    manager.mfa_enabled = True
    manager.mfa_secret_encrypted = encrypt(manager_secret)
    manager.save(update_fields=["mfa_enabled", "mfa_secret_encrypted"])
    manager_account = credentials["accounts"]["agency"]
    independent = proposal.action.actor
    independent.user_permissions.add(Permission.objects.get(codename="review_recipient_assessment"))
    independent_secret = pyotp.random_base32()
    independent.mfa_secret_encrypted = encrypt(independent_secret)
    independent.save(update_fields=["mfa_secret_encrypted"])
    independent_account = credentials["accounts"]["moderator"]
    alias_before = person.alias
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_role("heading", name=label("Your account"), exact=True)
            ).to_be_visible()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/rectification/")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Read current fields before independent proposed correction review"
            )
            page.get_by_role("button", name=label("Record correction action"), exact=True).click()
            page.get_by_role("link", name=label("Review correction proposal"), exact=True).click()
            expect(page).to_have_url(live_server.url + path)
            expect(
                page.get_by_role("heading", name=label("Independent correction review"), exact=True)
            ).to_be_visible()
            page.locator("[name=purpose]").fill(
                "Read proposed changes before independent correction decision"
            )
            page.get_by_role("button", name=label("Record review action"), exact=True).click()
            expect(
                page.get_by_text(
                    ("Nombre del perfil" if language == "es" else "Profile name")
                    + ": Synthetic reviewed correction",
                    exact=False,
                )
            ).to_be_visible()
            expect(page.get_by_text("Synthetic correction area", exact=False)).to_be_visible()
            expect(page.get_by_text("Synthetic corrected category", exact=False)).to_be_visible()
            expect(page.get_by_text("Synthetic corrected service", exact=False)).to_be_visible()
            expect(page.get_by_text("Synthetic corrected consult", exact=False)).to_be_visible()
            expect(page.get_by_text("90.00 EUR", exact=False)).to_be_visible()
            expect(page.get_by_text("synthetic_contact", exact=False)).to_be_visible()
            expect(page.get_by_text("Tipo de perfil / Profile type", exact=False)).to_be_visible()
            expect(page.get_by_text("Otro / Other", exact=False)).to_be_visible()
            proposed_photo_label = (
                "Fotografía propuesta 1" if language == "es" else "Proposed photo 1"
            )
            expect(page.get_by_alt_text(proposed_photo_label, exact=True)).to_be_visible()
            expect(page.locator("figure img")).to_have_count(2)
            assert page.locator("figure img").evaluate_all(
                "images => Promise.all(images.map(image => image.decode().then(() => image.naturalWidth > 0))).then(results => results.every(Boolean))"
            )
            assert "'spoken_languages':" not in page.locator("main").inner_text()
            assert "'municipality':" not in page.locator("main").inner_text()
            page.locator("[name=operation]").select_option("review")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name=label("Record review action"), exact=True).click()
            expect(
                page.get_by_role("heading", name=label("Private rights inspection"), exact=True)
            ).to_be_visible()
            # Synthetic identity provider only; actual PG proof/read guards and browser MFA.
            from concurrent.futures import ThreadPoolExecutor

            def refresh_verification(confirm=False, recipient_handoff=False):
                from django.db import close_old_connections, connections

                close_old_connections()
                try:
                    original = proposal.action.actor
                    staff = Client()
                    staff.force_login(original)
                    session = staff.session
                    session["mfa_version"] = original.mfa_version
                    session.save()
                    if confirm:
                        notification = RightsRectificationNotification.objects.get()
                        assert (
                            client.post(
                                receipt + f"response/{notification.response_id}/acknowledge/",
                                {"received": "yes"},
                            ).status_code
                            == 302
                        )
                    case.refresh_from_db()
                    if recipient_handoff:
                        from test_rights_verification import read

                        read(other, case)
                        act(reviewer, case.pk, uuid.uuid4(), case.version, "unassign", REASON)
                        case.refresh_from_db()
                        act(original, case.pk, uuid.uuid4(), case.version, "claim", REASON)
                        fresh(case, original, staff, reviewer, other)
                    else:
                        fresh(case, reviewer, other, original, staff)
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(refresh_verification).result(timeout=30)
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/rectification/")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Read current source before communicating approved correction"
            )
            page.get_by_role("button", name=label("Record correction action"), exact=True).click()
            page.get_by_role("link", name=label("Review correction proposal"), exact=True).click()
            page.locator("[name=purpose]").fill("Read approved changes before prior communication")
            page.get_by_role("button", name=label("Record review action"), exact=True).click()
            page.locator("[name=operation]").select_option("notify")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name=label("Record review action"), exact=True).click()
            expect(
                page.get_by_role("heading", name=label("Private rights inspection"), exact=True)
            ).to_be_visible()
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(refresh_verification, True).result(timeout=30)
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/rectification/")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Read current received source before executing correction"
            )
            page.get_by_role("button", name=label("Record correction action"), exact=True).click()
            page.get_by_role("link", name=label("Review correction proposal"), exact=True).click()
            page.locator("[name=purpose]").fill(
                "Read approved received changes before correction execution"
            )
            page.get_by_role("button", name=label("Record review action"), exact=True).click()
            page.locator("[name=operation]").select_option("execute")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name=label("Record review action"), exact=True).click()
            expect(
                page.get_by_role("heading", name=label("Private rights inspection"), exact=True)
            ).to_be_visible()
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(refresh_verification).result(timeout=30)
            page.goto(live_server.url + path)
            page.get_by_role("link", name=label("Review recipient history"), exact=True).click()
            expect(
                page.get_by_role("heading", name=label("Correction recipient history"), exact=True)
            ).to_be_visible()
            page.locator("[name=purpose]").fill(
                "Assess historical recipients after applied correction"
            )
            page.get_by_role(
                "button", name=label("Record access and review history"), exact=True
            ).click()
            expect(
                page.get_by_role("heading", name=label("Audited historical summary"), exact=True)
            ).to_be_visible()
            assert ("Incompleto:" if language == "es" else "Incomplete:") in page.content()
            recipient_history_url = page.url
            page.get_by_role("link", name=label("Assess recipients and gaps"), exact=True).click()
            expect(
                page.get_by_role("heading", name=label("Propose recipient assessment"), exact=True)
            ).to_be_visible()
            assessment_url = page.url
            page.locator("[name=purpose]").fill(
                "Read recipient and gap fields before motivated decisions"
            )
            page.get_by_role("button", name=label("Record assessment action"), exact=True).click()
            assert page.locator("fieldset").count() > 0
            for textarea in page.locator("textarea[name$='-reason']").all():
                textarea.fill(REASON)
            for textarea in page.locator("textarea[name$='-evidence']").all():
                textarea.fill("Synthetic source evidence awaiting independent review")
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.get_by_role("button", name=label("Record assessment action"), exact=True).click()
            expect(
                page.get_by_role("heading", name=label("Private rights inspection"), exact=True)
            ).to_be_visible()
            page.goto(assessment_url)
            assert page.locator("fieldset").count() == 0
            page.goto(recipient_history_url)  # Explicit GET to the original inventory.
            assert (
                page.get_by_role(
                    "heading", name=label("Audited historical summary"), exact=True
                ).count()
                == 0
            )
            page.goto(live_server.url + path)
            assert "Synthetic reviewed correction" not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(refresh_verification, False, True).result(timeout=30)
            review_page = browser.new_page(viewport={"width": 390, "height": 844})
            review_page.goto(live_server.url + f"/{language}/account/login/")
            review_page.locator("[name=email]").fill(independent_account["email"])
            review_page.locator("[name=password]").fill(credentials["password"])
            review_page.locator("button[type=submit]").click()
            review_page.locator("[name=code]").fill(pyotp.TOTP(independent_secret).now())
            review_page.locator("button[type=submit]").click()
            expect(
                review_page.get_by_role("heading", name=label("Your account"), exact=True)
            ).to_be_visible()
            review_page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            review_page.get_by_role(
                "link", name=label("Review recipient assessment"), exact=True
            ).click()
            review_url = review_page.url
            expect(
                review_page.get_by_role(
                    "heading", name=label("Independent recipient assessment review"), exact=True
                )
            ).to_be_visible()
            review_page.locator("[name=purpose]").fill(
                "Read proposed recipient decisions and evidence independently"
            )
            review_page.get_by_role(
                "button", name=label("Record independent review action"), exact=True
            ).click()
            expect(
                review_page.get_by_role(
                    "heading", name=label("Audited proposed decisions"), exact=True
                )
            ).to_be_visible()
            assert "Synthetic source evidence awaiting independent review" in review_page.content()
            assert review_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            review_page.locator("[name=operation]").select_option("review")
            review_page.locator("[name=outcome]").select_option("accepted")
            review_page.locator("[name=reason]").fill(REASON)
            review_page.get_by_role(
                "button", name=label("Record independent review action"), exact=True
            ).click()
            expect(
                review_page.get_by_role(
                    "heading", name=label("Private rights inspection"), exact=True
                )
            ).to_be_visible()
            review_page.goto(review_url)
            assert (
                review_page.get_by_role(
                    "heading", name=label("Audited proposed decisions"), exact=True
                ).count()
                == 0
            )
            manager_page = browser.new_page(viewport={"width": 390, "height": 844})
            manager_page.goto(live_server.url + f"/{language}/account/login/")
            manager_page.locator("[name=email]").fill(manager_account["email"])
            manager_page.locator("[name=password]").fill(credentials["password"])
            manager_page.locator("button[type=submit]").click()
            manager_page.locator("[name=code]").fill(pyotp.TOTP(manager_secret).now())
            manager_page.locator("button[type=submit]").click()
            expect(
                manager_page.get_by_role("heading", name=label("Your account"), exact=True)
            ).to_be_visible()
            manager_page.get_by_role(
                "link", name=label("Private correction notices"), exact=True
            ).click()
            expect(
                manager_page.get_by_role(
                    "heading", name=label("Private correction notices"), exact=True
                )
            ).to_be_visible()
            assert REASON not in manager_page.content()
            manager_page.get_by_role("button", name=label("Confirm receipt"), exact=True).click()
            expect(manager_page.get_by_text(label("Receipt recorded"), exact=False)).to_be_visible()
            manager_page.reload()
            assert (
                manager_page.get_by_role(
                    "button", name=label("Confirm receipt"), exact=True
                ).count()
                == 0
            )
            assert manager_page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            for photo_id in historic_photo_ids:
                response = manager_page.goto(
                    live_server.url + f"/{language}/photos/{photo_id}/private/"
                )
                assert response.status == 404
        finally:
            browser.close()
    assert RightsRectificationReview.objects.get().outcome == "approved"
    person.refresh_from_db()
    assert person.alias != alias_before
    assert person.alias == "Synthetic reviewed correction"
    person.listing.refresh_from_db()
    assert person.listing.status != "published"
    assert RightsRectificationNotification.objects.count() == 1


def test_proposal_history_pages_do_not_reveal_proposed_text(request, settings, monkeypatch):
    from apps.safety.crypto import seal
    from apps.safety.models import RightsAction, RightsRectificationProposal

    case, user, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    proof = case.proofs.latest("created_at")
    for _ in range(51):
        # Historical metadata fixtures, not approved or executed correction decisions.
        action = RightsAction.objects.create(
            key=uuid.uuid4(),
            request=case,
            actor=user,
            expected_version=case.version,
            operation="rectify_plan",
            payload_digest="f" * 64,
            encrypted_reason=seal({"reason": "Synthetic history fixture"}),
        )
        RightsRectificationProposal.objects.create(
            action=action,
            proof=proof,
            person=person,
            source_digest="e" * 64,
            encrypted_changes=seal({"alias": "Private historical correction"}),
        )
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    first = staff.get(path)
    second = staff.get(path, {"proposals_page": 2})
    assert first.status_code == second.status_code == 200
    assert len(first.context["proposals"]) == 50 and len(second.context["proposals"]) == 1
    assert first.context["proposals"].has_next() and second.context["proposals"].has_previous()
    assert set(item.pk for item in first.context["proposals"]).isdisjoint(
        item.pk for item in second.context["proposals"]
    )
    assert b"Private historical correction" not in first.content + second.content
    assert "encrypted_changes" in first.context["proposals"][0].get_deferred_fields()


@pytest.mark.parametrize(
    "outcome,subject_username,recipient_outcome,clear_rates",
    [
        ("approved", "fixture-v1-model-a", "accepted", False),
        ("approved", "fixture-v1-model-a", "rejected", False),
        ("rejected", "fixture-v1-model-a", "accepted", False),
        ("approved", "fixture-v1-individual", "accepted", False),
        ("approved", "fixture-v1-individual", "accepted", True),
        ("approved", "fixture-v1-model-a", "accepted", True),
    ],
)
def test_reviewed_correction_communication_requires_new_proof_and_is_idempotent(
    request, settings, monkeypatch, outcome, subject_username, recipient_outcome, clear_rates
):
    from django.core.exceptions import ValidationError

    from apps.safety.rectification_execution import notify
    from apps.safety.rectification_review import inspect, review

    case, reviewer, other, person, proposal, path, client, receipt = independent_case(
        request,
        settings,
        monkeypatch,
        with_receipt=True,
        subject_username=subject_username,
        clear_rates=clear_rates,
        clear_contacts=clear_rates,
        clear_details=clear_rates,
        clear_photos=clear_rates,
        correct_location=True,
        correct_catalog=True,
        correct_rates=True,
        correct_contacts=True,
        correct_details=True,
        correct_photos=True,
        replacement_photo=True,
        changes={
            "alias": "Synthetic reviewed correction",
            "title": "Corrected synthetic title",
            "description": EXACT_DESCRIPTION,
        },
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    preview(reviewer, case.pk, case.version, "Read current source before independent review")
    inspect(reviewer, case.pk, proposal.pk, case.version, "Read proposed changes independently")
    review(reviewer, case.pk, proposal.pk, uuid.uuid4(), case.version, outcome, REASON)
    case.refresh_from_db()
    key = uuid.uuid4()
    with pytest.raises(ValidationError):
        notify(reviewer, case.pk, proposal.pk, key, case.version, REASON)
    original = proposal.action.actor
    staff = Client()
    staff.force_login(original)
    session = staff.session
    session["mfa_version"] = original.mfa_version
    session.save()
    fresh(case, reviewer, other, original, staff)
    preview(reviewer, case.pk, case.version, "Read unchanged current source before communication")
    inspect(
        reviewer,
        case.pk,
        proposal.pk,
        case.version,
        "Read approved correction before communication",
    )
    version = case.version
    before = person.alias, person.listing.status, person.listing.lifecycle_version
    data = {"key": key, "version": version, "operation": "notify", "reason": REASON}
    if outcome == "rejected":
        assert other.post(path, data).status_code == 409
        assert not RightsRectificationNotification.objects.exists()
        return
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    assert other.post(path, {**data, "version": version - 1}).status_code == 409
    # Writer changes source without touching case.version: source HMAC must catch it.
    old_alias = person.alias
    type(person).objects.filter(pk=person.pk).update(alias="Changed synthetic current source")
    responses_before = case.responses.count()
    assert other.post(path, data).status_code == 409
    assert not RightsRectificationNotification.objects.exists()
    assert case.responses.count() == responses_before
    type(person).objects.filter(pk=person.pk).update(alias=old_alias)
    assert other.post(path, data).status_code == 302
    result = RightsRectificationNotification.objects.get()
    assert other.post(path, data).status_code == 302
    assert RightsRectificationNotification.objects.count() == 1
    assert other.post(path, {**data, "reason": REASON + " changed"}).status_code == 409
    reviewer.user_permissions.remove(Permission.objects.get(codename="respond_rights_request"))
    assert other.post(path, data).status_code == 403
    received = client.get(receipt)
    assert received.status_code == 200
    assert b"No changes have been applied yet" in received.content
    assert REASON.encode() not in received.content
    assert b"Synthetic reviewed correction" not in received.content
    acknowledgement = receipt + f"response/{result.response_id}/acknowledge/"
    assert (
        Client(enforce_csrf_checks=True).post(acknowledgement, {"received": "yes"}).status_code
        == 403
    )
    assert client.post(acknowledgement, {"received": "yes"}).status_code == 302
    assert client.post(acknowledgement, {"received": "yes"}).status_code == 302
    assert result.response.receipt_acknowledgement.channel_digest == case.receipt_digest
    assert result.response.kind == "progress"
    assert result.review.outcome == "approved"
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert (person.alias, person.listing.status, person.listing.lifecycle_version) == before

    from apps.safety.crypto import unseal
    from apps.safety.rectification_execution import execute

    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    case.refresh_from_db()
    execution_key = uuid.uuid4()
    with pytest.raises(ValidationError):
        execute(reviewer, case.pk, proposal.pk, execution_key, case.version, REASON)
    reviewer = User.objects.get(pk=reviewer.pk)
    fresh(case, reviewer, other, original, staff)
    preview(reviewer, case.pk, case.version, "Read received correction source before execution")
    inspect(
        reviewer,
        case.pk,
        proposal.pk,
        case.version,
        "Read received approved changes before execution",
    )
    old_revision = person.listing.approved_revision
    assert old_revision is not None
    old_title = old_revision.title
    from apps.safety.rectification_location import source as location_source

    old_location = location_source(old_revision)
    from apps.safety.rectification_catalog import source as catalog_source

    old_catalog = catalog_source(old_revision)
    from apps.safety.rectification_rates import source as rates_source

    old_rate_values = rates_source(old_revision)
    old_description = old_revision.description
    old_rates = list(
        old_revision.rates.values_list("concept", "mode", "amount", "currency", "duration_minutes")
    )
    old_photos = list(
        old_revision.photos.filter(removed_at__isnull=True).values_list("blob_id", "position")
    )
    from apps.safety.rectification_photos import source as photo_source

    old_photo_ids = photo_source(old_revision)
    selected_photo_ids = unseal(proposal.encrypted_changes)["photos"]
    from apps.mediafiles.models import Photo

    selected_rows = {
        str(photo.pk): photo for photo in Photo.objects.filter(pk__in=selected_photo_ids)
    }
    expected_photos = [
        (selected_rows[identifier].blob_id, index)
        for index, identifier in enumerate(selected_photo_ids)
    ]
    old_relations = {
        field.name: set(getattr(old_revision, field.name).values_list("pk", flat=True))
        for field in old_revision._meta.many_to_many
    }
    from apps.core.models import Person, PhoneClaim
    from apps.safety.rectification_contacts import binding
    from apps.safety.rectification_contacts import source as contact_source
    from apps.safety.rectification_details import source as details_source

    old_details = details_source(old_revision)
    old_identity = person.subject_id, person.age_status, person.consent_version
    old_contacts = contact_source(old_revision)
    old_binding = binding(person)
    original_claim = person.phone_claim
    other_shared = list(
        Person.objects.filter(phone_claim=original_claim)
        .exclude(pk=person.pk)
        .values_list("pk", "phone_claim_id")
    )
    if person.agency_id:
        assert other_shared
    from datetime import timedelta

    from django.utils import timezone
    from django.utils.crypto import salted_hmac

    from apps.core.models import PhoneChallenge

    stale_phone = PhoneChallenge.objects.create(
        person=person,
        manager_version=person.manager_version,
        person_rights_version=person.rights_version,
        phone=original_claim.phone,
        digest=salted_hmac("phone-otp", "654321", algorithm="sha256").hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    old_rights_version = person.rights_version
    execution_version = case.version
    payload = {
        "key": execution_key,
        "version": execution_version,
        "operation": "execute",
        "reason": REASON,
    }
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    from apps.listings.models import Revision
    from apps.mediafiles.tasks import process_blob

    assert old_rates and old_photos and all(old_relations.values())
    rate = old_revision.rates.first()
    original_concept = rate.concept
    rate.concept = "Changed synthetic source rate"
    rate.save(update_fields=["concept"])
    assert other.post(path, payload).status_code == 409
    rate.concept = original_concept
    rate.save(update_fields=["concept"])
    from apps.catalog.models import PostalCode

    destination_postal = PostalCode.objects.get(
        pk=unseal(proposal.encrypted_changes)["location"]["postal_code"]
    )
    destination_postal.public_safe = False
    destination_postal.save(update_fields=["public_safe"])
    assert other.post(path, payload).status_code == 409
    destination_postal.public_safe = True
    destination_postal.save(update_fields=["public_safe"])
    from apps.catalog.models import Service

    destination_service = Service.objects.get(
        pk=unseal(proposal.encrypted_changes)["catalog"]["services"][0]
    )
    destination_service.active = False
    destination_service.save(update_fields=["active"])
    assert other.post(path, payload).status_code == 409
    destination_service.active = True
    destination_service.save(update_fields=["active"])
    target_phone = unseal(proposal.encrypted_changes)["contacts"]["phone"]
    if target_phone:
        target_claim = PhoneClaim.objects.get(phone=target_phone)
        original_verification = target_claim.verified_at
        target_claim.verified_at = None
        target_claim.save(update_fields=["verified_at"])
        assert other.post(path, payload).status_code == 409
        target_claim.verified_at = original_verification
        target_claim.save(update_fields=["verified_at"])
    from apps.catalog.models import Municipality

    travel_destinations = unseal(proposal.encrypted_changes)["details"]["travel_areas"]
    if travel_destinations:
        target_city = Municipality.objects.get(pk=travel_destinations[0])
        target_city.active = False
        target_city.save(update_fields=["active"])
        assert other.post(path, payload).status_code == 409
        target_city.active = True
        target_city.save(update_fields=["active"])
    replacement_binding = PhoneClaim.objects.get(phone="+34600000991")
    Person.objects.filter(pk=person.pk).update(phone_claim=replacement_binding)
    assert other.post(path, payload).status_code == 409
    Person.objects.filter(pk=person.pk).update(phone_claim=original_claim)
    from apps.mediafiles.models import Blob

    copied_blob = old_revision.photos.filter(removed_at__isnull=True).first().blob
    original_derivative = copied_blob.derivative.name
    Blob.objects.filter(pk=copied_blob.pk).update(derivative="derivatives/synthetic-changed.webp")
    assert other.post(path, payload).status_code == 409
    Blob.objects.filter(pk=copied_blob.pk).update(derivative=original_derivative)
    ongoing = Revision.objects.create(
        listing=person.listing, manager_version=person.manager_version
    )
    assert other.post(path, payload).status_code == 409
    ongoing.delete()  # Test-only competing draft, no user content.
    dispatched = []
    original_delay = process_blob.delay

    def record_dispatch(blob_id):
        dispatched.append(blob_id)
        return original_delay(blob_id)

    monkeypatch.setattr(process_blob, "delay", record_dispatch)
    from apps.safety import rectification_execution
    from apps.safety.models import RightsAction, RightsRectificationExecution

    historical = Revision.objects.create(
        listing=person.listing,
        manager_version=person.manager_version,
        status="rejected",
        title=old_title,
        description=old_description,
    )
    historical_photo = Photo.objects.create(
        revision=historical,
        blob=old_revision.photos.first().blob,
        comparison_complete=True,
    )
    revision_count = person.listing.revisions.count()
    response_count = case.responses.count()

    def fail_response(*args, **kwargs):
        raise ValidationError("Synthetic response transaction failure")

    with monkeypatch.context() as patch:
        patch.setattr(rectification_execution, "issue", fail_response)
        assert other.post(path, payload).status_code == 409
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert person.alias == before[0] and person.rights_version == old_rights_version
    assert person.phone_claim_id == original_claim.pk
    assert person.listing.lifecycle_version == before[2]
    assert person.listing.revisions.count() == revision_count
    assert case.responses.count() == response_count
    assert not RightsAction.objects.filter(key=execution_key).exists()
    assert not RightsRectificationExecution.objects.exists()
    from apps.safety.models import RightsRectificationManagerNotice

    assert not RightsRectificationManagerNotice.objects.exists()
    assert dispatched == []
    assert other.post(path, payload).status_code == 302
    assert set(dispatched) == {str(blob_id) for blob_id, _ in expected_photos}
    applied = RightsRectificationExecution.objects.get()
    assert (
        execute(reviewer, case.pk, proposal.pk, execution_key, execution_version, REASON).pk
        == applied.pk
    )
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert applied.response is not None and applied.response.kind == "progress"
    receipt_page = client.get(receipt)
    assert b"The request remains open" in receipt_page.content
    assert REASON.encode() not in receipt_page.content
    case.refresh_from_db()
    assert case.status == "reviewing"
    assert person.alias == "Synthetic reviewed correction"
    assert person.rights_version == old_rights_version + 1
    assert person.listing.status != "published"
    assert person.listing.available_until is None
    assert unseal(applied.encrypted_previous_values)["alias"] == before[0]
    if old_revision:
        old_revision.refresh_from_db()
        assert old_revision.title == old_title
        assert old_revision.description == old_description
        corrected = applied.corrected_revision
        assert location_source(old_revision) == old_location
        assert location_source(corrected) == unseal(proposal.encrypted_changes)["location"]
        assert unseal(applied.encrypted_previous_values)["location"] == old_location
        assert location_source(corrected) != old_location
        assert catalog_source(old_revision) == old_catalog
        assert catalog_source(corrected) == unseal(proposal.encrypted_changes)["catalog"]
        assert unseal(applied.encrypted_previous_values)["catalog"] == old_catalog
        assert catalog_source(corrected) != old_catalog
        assert details_source(old_revision) == old_details
        assert details_source(corrected) == unseal(proposal.encrypted_changes)["details"]
        assert unseal(applied.encrypted_previous_values)["details"] == old_details
        assert (person.subject_id, person.age_status, person.consent_version) == old_identity
        assert contact_source(old_revision) == old_contacts
        assert contact_source(corrected) == unseal(proposal.encrypted_changes)["contacts"]
        assert unseal(applied.encrypted_previous_values)["contacts"] == old_contacts
        assert unseal(applied.encrypted_previous_values)["phone_binding"] == old_binding
        assert (person.phone_claim.phone if person.phone_claim else "") == corrected.phone
        original_claim.refresh_from_db()
        assert original_claim.phone == old_binding["phone"] and original_claim.verified_at
        assert list(
            Person.objects.filter(pk__in=[pk for pk, _ in other_shared])
            .order_by("pk")
            .values_list("pk", "phone_claim_id")
        ) == sorted(other_shared)
        assert corrected.title == "Corrected synthetic title"
        assert corrected.description == EXACT_DESCRIPTION
        assert rates_source(corrected) == unseal(proposal.encrypted_changes)["rates"]
        assert rates_source(old_revision) == old_rate_values
        assert unseal(applied.encrypted_previous_values)["rates"] == old_rate_values
        assert rates_source(corrected) != old_rate_values
        assert set(corrected.photos.values_list("blob_id", "position")) == set(expected_photos)
        assert photo_source(old_revision) == old_photo_ids
        assert set(old_revision.photos.values_list("blob_id", "position")) == set(old_photos)
        assert unseal(applied.encrypted_previous_values)["photos"] == old_photo_ids
        assert not corrected.photos.filter(approved=True).exists()
        # Local eager processing may already have completed comparisons; dispatch is asserted above.
        for field, ids in old_relations.items():
            expected = (
                set(unseal(proposal.encrypted_changes)["catalog"][field])
                if field in {"categories", "services"}
                else (
                    set(unseal(proposal.encrypted_changes)["details"]["travel_areas"])
                    if field == "travel_areas"
                    else ids
                )
            )
            assert set(getattr(corrected, field).values_list("pk", flat=True)) == expected
            assert set(getattr(old_revision, field).values_list("pk", flat=True)) == ids
        assert person.listing.approved_revision_id == old_revision.pk
        assert applied.corrected_revision.source_revision_id == old_revision.pk
        assert applied.corrected_revision.status == "draft"
        assert not applied.corrected_revision.publisher_acceptance_id
        assert not applied.corrected_revision.contact_exposure_accepted
        from apps.listings.submissions import validate_submission

        with pytest.raises(ValidationError, match="Corrected historical version"):
            validate_submission(old_revision, person)

    from apps.safety.crypto import unseal
    from apps.safety.rectification_recipients import prepare as prepare_recipients

    case.refresh_from_db()
    recipient_key = uuid.uuid4()
    with pytest.raises(ValidationError):
        prepare_recipients(
            reviewer,
            case.pk,
            applied.pk,
            recipient_key,
            case.version,
            "Assess historical recipients after correction",
        )
    fresh(case, reviewer, other, original, staff)
    recipients = prepare_recipients(
        reviewer,
        case.pk,
        applied.pk,
        recipient_key,
        case.version,
        "Assess historical recipients after correction",
    )
    assert (
        prepare_recipients(
            reviewer,
            case.pk,
            applied.pk,
            recipient_key,
            case.version,
            "Assess historical recipients after correction",
        ).pk
        == recipients.pk
    )
    recipients_path = (
        f"/en/moderation/rights/{case.pk}/rectification-execution/{applied.pk}/recipients/"
    )
    assert other.get(recipients_path).context["inventory"] is None
    assert Client(enforce_csrf_checks=True).post(recipients_path).status_code == 403
    page = other.post(
        recipients_path,
        {
            "key": recipient_key,
            "version": case.version,
            "purpose": "Assess historical recipients after correction",
        },
    )
    assert page.status_code == 200
    from datetime import timedelta

    from django.utils import timezone

    proof = recipients.proof
    expires_at = proof.expires_at
    proof.expires_at = timezone.now() - timedelta(seconds=1)
    proof.save(update_fields=["expires_at"])
    assert (
        other.post(
            recipients_path,
            {
                "key": recipient_key,
                "version": case.version,
                "purpose": "Assess historical recipients after correction",
            },
        ).status_code
        == 409
    )
    proof.expires_at = expires_at
    proof.save(update_fields=["expires_at"])
    assert b"Incomplete:" in page.content
    assert b"Corrected synthetic description" not in page.content
    assert other.get(recipients_path).context["inventory"] is None
    recipient_data = unseal(recipients.encrypted_inventory)
    assert recipient_data["complete"] is False and recipient_data["pending"]
    expected_kind = "agency" if person.agency_id else "individual"
    assert any(
        row["kind"] == expected_kind
        and row["reference"] == str(person.agency_id or person.individual_id)
        for row in recipient_data["candidates"]
    )
    assert "Corrected synthetic description" not in recipients.encrypted_inventory
    assert all(
        set(row) == {"kind", "reference", "evidence"} for row in recipient_data["candidates"]
    )
    with pytest.raises(ValidationError):
        prepare_recipients(
            reviewer,
            case.pk,
            applied.pk,
            recipient_key,
            case.version,
            "Different historical recipients access purpose",
        )

    from apps.safety.models import RightsRectificationManagerNotice

    notices = RightsRectificationManagerNotice.objects.filter(execution=applied)
    assert notices.count() == (2 if person.agency_id else 1)
    # Every notice is attributable to its concrete account, including editors
    # without publishing/representation actions. A notice is not disclosure proof.
    for recorded_notice in notices:
        candidate = next(
            row
            for row in recipient_data["candidates"]
            if row["kind"] == "account" and row["reference"] == str(recorded_notice.recipient_id)
        )
        assert {
            "basis": "internal_correction_notice",
            "record": str(recorded_notice.pk),
        } in candidate["evidence"]
    manager = person.agency.owner if person.agency_id else person.individual
    manager.mfa_enabled = True
    manager.save(update_fields=["mfa_enabled"])
    manager_client = Client()
    manager_client.force_login(manager)
    session = manager_client.session
    session["mfa_version"] = manager.mfa_version
    session.save()
    for historic_photo in old_revision.photos.all():
        assert manager_client.get(f"/en/photos/{historic_photo.pk}/private/").status_code == 404
        assert historic_photo.blob.original.storage.exists(historic_photo.blob.original.name)
    assert manager_client.get(f"/en/photos/{historical_photo.pk}/private/").status_code == 404
    assert manager_client.get(f"/en/draft/{historical.pk}/status/").status_code == 404
    assert manager_client.get(f"/en/draft/{old_revision.pk}/status/").status_code == 404
    assert manager_client.get(f"/en/draft/{old_revision.pk}/1/").status_code == 404
    assert manager_client.get(f"/en/draft/{corrected.pk}/status/").status_code == 200
    for current_photo in corrected.photos.all():
        image = manager_client.get(f"/en/photos/{current_photo.pk}/private/")
        assert image.status_code == 200 and b"".join(image.streaming_content)
        image.close()
    # Previously created matches remain as evidence, but are absent from
    # ordinary review and cannot block an unrelated current publication.
    from apps.core.models import Person
    from apps.listings.match_review import resolve
    from apps.listings.moderation import unresolved_matches
    from apps.mediafiles.models import Match
    from apps.mediafiles.services import process

    peer = Person.objects.exclude(pk=person.pk).get(subject__username="fixture-v1-model-b")
    peer_photo, _ = Photo.objects.get_or_create(
        revision=peer.listing.revisions.first(),
        blob=historical_photo.blob,
    )
    old_match, _ = Match.objects.get_or_create(
        photo=historical_photo,
        candidate=peer_photo,
        defaults={"method": "sha256"},
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="review_listing"))
    reviewer = User.objects.get(pk=reviewer.pk)
    for side in ["photo", "candidate"]:
        assert other.get(f"/en/moderation/matches/{old_match.pk}/{side}/image/").status_code == 403
    assert other.get(f"/en/moderation/matches/{old_match.pk}/").status_code == 403
    queue = other.get("/en/moderation/matches/")
    assert queue.status_code == 200
    assert old_match.pk not in [row.pk for row in queue.context["matches"]]
    assert not unresolved_matches(peer_photo.revision).filter(pk=old_match.pk).exists()
    with pytest.raises(ValidationError, match="Correction history"):
        resolve(
            reviewer, old_match.pk, old_match.review_version, "conflict", REASON, "Synthetic case"
        )
    from apps.core.models import LegalDocument
    from apps.listings.models import Appeal, ModerationDecision, Submission
    from apps.mediafiles.models import MatchResolution, PhotoAppeal, PhotoRestriction

    assert other.get(f"/en/moderation/listings/{old_revision.pk}/").status_code == 404
    assert other.get(f"/en/moderation/photos/{old_revision.photos.first().pk}/").status_code == 404
    Revision.objects.filter(pk=historical.pk).update(status="pending")
    from apps.listings.moderation import decide

    Submission.objects.create(
        revision=historical,
        actor=manager,
        document=LegalDocument.objects.first(),
        approved_base=corrected,
    )
    historical.refresh_from_db()
    assert historical.status == "pending" and historical.submission.pk
    for outcome in ["approved", "rejected"]:
        with pytest.raises(ValidationError, match="Review changed"):
            decide(reviewer, historical.pk, historical.edit_version, outcome, REASON)
    assert not historical.decisions.exists()
    queue = other.get("/en/moderation/listings/")
    assert historical.pk not in [row.pk for row in queue.context["revisions"]]
    Revision.objects.filter(pk=historical.pk).update(status="rejected")
    old_decision = ModerationDecision.objects.create(
        revision=historical,
        reviewer=original,
        outcome="rejected",
        reason=REASON,
    )
    old_appeal = Appeal.objects.create(decision=old_decision, actor=manager, explanation=REASON)
    assert manager_client.get(f"/en/draft/decisions/{old_decision.pk}/appeal/").status_code == 404
    assert other.get(f"/en/moderation/appeals/{old_appeal.pk}/").status_code == 404
    queue = other.get("/en/moderation/appeals/")
    assert old_appeal.pk not in [row.pk for row in queue.context["appeals"]]
    old_resolution = MatchResolution.objects.create(
        match=old_match,
        reviewer=original,
        outcome="conflict",
        reason=REASON,
        evidence_reference="Synthetic stored historical decision",
    )
    old_restriction = PhotoRestriction.objects.create(
        person=person,
        manager_version=person.manager_version,
        photo=historical_photo,
        decision=old_resolution,
    )
    old_photo_appeal = PhotoAppeal.objects.create(
        restriction=old_restriction,
        actor=manager,
        review_version=old_match.review_version,
        explanation=REASON,
    )
    from django.urls import reverse

    assert (
        manager_client.get(reverse("photo_restriction", args=[old_restriction.pk])).status_code
        == 404
    )
    assert other.get(reverse("photo_appeal_review", args=[old_photo_appeal.pk])).status_code == 404
    queue = other.get(reverse("photo_appeal_queue"))
    assert old_photo_appeal.pk not in [row.pk for row in queue.context["appeals"]]
    count = Match.objects.filter(photo=historical_photo).count()
    process(historical_photo.blob_id)
    assert Match.objects.filter(photo=historical_photo).count() == count
    if corrected.photos.filter(blob=historical_photo.blob).exists():
        current_match = Match.objects.get(
            photo__revision=corrected,
            photo__blob=historical_photo.blob,
            candidate=peer_photo,
        )
        image = other.get(f"/en/moderation/matches/{current_match.pk}/photo/image/")
        assert image.status_code == 200 and b"".join(image.streaming_content)
        image.close()
    notice = notices.get(recipient=manager)
    from django.urls import reverse

    assert (
        manager_client.post(
            reverse("phone_confirm", args=[stale_phone.pk]), {"code": "654321"}
        ).status_code
        == 400
    )
    stale_phone.refresh_from_db()
    assert stale_phone.used_at is None and stale_phone.attempts == 0
    person.refresh_from_db()
    assert (person.phone_claim.phone if person.phone_claim else "") == target_phone
    resume = manager_client.post(
        f"/en/listing/{person.listing.pk}/manage/",
        {"key": uuid.uuid4(), "version": person.listing.lifecycle_version, "operation": "resume"},
    )
    assert resume.status_code == 409
    assert b"Corrected historical version" in resume.content
    person.listing.refresh_from_db()
    assert person.listing.status != "published"
    with pytest.raises(
        ValidationError,
        match="Publishing terms updated" if target_phone else "Verify age, authorization and phone",
    ):
        validate_submission(applied.corrected_revision, person)
    inbox = "/en/account/correction-notices/"
    page = manager_client.get(inbox)
    assert page.status_code == 200 and len(page.context["notices"]) == 1
    assert (
        REASON.encode() not in page.content
        and b"Corrected synthetic description" not in page.content
    )
    assert page["Cache-Control"] == "private, no-store" and "noindex" in page["X-Robots-Tag"]
    acknowledge = inbox + f"{notice.pk}/acknowledge/"
    assert Client(enforce_csrf_checks=True).post(acknowledge).status_code == 403
    assert other.post(acknowledge).status_code == 404
    assert manager_client.post(acknowledge).status_code == 302
    notice.refresh_from_db()
    acknowledged_at = notice.acknowledged_at
    assert acknowledged_at is not None
    assert manager_client.post(acknowledge).status_code == 302
    notice.refresh_from_db()
    assert notice.acknowledged_at == acknowledged_at
    if person.agency_id:
        editor_notice = notices.get(recipient=person.assigned_editor)
        editor = person.assigned_editor
        editor.mfa_enabled = True
        editor.save(update_fields=["mfa_enabled"])
        editor_client = Client()
        editor_client.force_login(editor)
        session = editor_client.session
        session["mfa_version"] = editor.mfa_version
        session.save()
        assert len(editor_client.get(inbox).context["notices"]) == 1
        from apps.core.models import AgencyMember

        AgencyMember.objects.filter(agency=person.agency, user=editor).update(active=False)
        assert len(editor_client.get(inbox).context["notices"]) == 0
        assert editor_client.post(inbox + f"{editor_notice.pk}/acknowledge/").status_code == 404
    from apps.safety.recipient_assessments import propose as propose_assessment
    from apps.safety.recipient_assessments import targets

    old_decisions = {
        key: {
            "outcome": "pending",
            "reason": "Synthetic recipient evaluation awaiting independent review",
            "evidence": "Synthetic source records require further scope assessment",
        }
        for key in targets(recipient_data)
    }
    with pytest.raises(ValidationError, match="Recipient history changed"):
        propose_assessment(
            reviewer, case.pk, recipients.pk, uuid.uuid4(), case.version, old_decisions
        )
    updated_inventory = prepare_recipients(
        reviewer,
        case.pk,
        applied.pk,
        uuid.uuid4(),
        case.version,
        "Assess recipient history after recorded acknowledgement",
    )
    updated_data = unseal(updated_inventory.encrypted_inventory)
    values = {
        key: {
            "outcome": "pending",
            "reason": "Synthetic recipient evaluation awaiting independent review",
            "evidence": "Synthetic source records require further scope assessment",
        }
        for key in targets(updated_data)
    }
    from apps.safety.recipient_assessments import validate_decisions

    manager_target = next(
        token
        for token, candidate in targets(updated_data).items()
        if candidate
        and candidate["kind"] == "account"
        and candidate["reference"] == str(manager.pk)
    )
    values[manager_target]["outcome"] = "communicated"
    assert validate_decisions(updated_data, values) == values
    if person.agency_id:
        editor_target = next(
            token
            for token, candidate in targets(updated_data).items()
            if candidate
            and candidate["kind"] == "account"
            and candidate["reference"] == str(editor.pk)
        )
        # Revoked editor has an unacknowledged notice: another account's receipt
        # cannot establish communication to this historical recipient.
        values[editor_target]["outcome"] = "communicated"
        with pytest.raises(ValidationError, match="Recorded recipient receipt required"):
            validate_decisions(updated_data, values)
        values[editor_target]["outcome"] = "pending"
        agency_target = next(
            token
            for token, candidate in targets(updated_data).items()
            if candidate
            and candidate["kind"] == "agency"
            and candidate["reference"] == str(person.agency_id)
        )
        values[agency_target]["outcome"] = "communicated"
        with pytest.raises(ValidationError, match="Recorded recipient receipt required"):
            validate_decisions(updated_data, values)
        values[agency_target]["outcome"] = "pending"
    values["gap:public_audience_and_reuse_without_identified_recipients"]["outcome"] = "impossible"
    assessment_key = uuid.uuid4()
    assessment_version = case.version
    with pytest.raises(ValidationError, match="Read recipient assessment fields first"):
        propose_assessment(
            reviewer, case.pk, updated_inventory.pk, assessment_key, assessment_version, values
        )
    assessment_path = (
        f"/en/moderation/rights/{case.pk}/recipient-inventory/{updated_inventory.pk}/assessment/"
    )
    assert other.get(assessment_path).context["decisions"] is None
    assert Client(enforce_csrf_checks=True).post(assessment_path).status_code == 403
    inspected = other.post(
        assessment_path,
        {
            "key": uuid.uuid4(),
            "version": assessment_version,
            "operation": "inspect",
            "purpose": "Read each recipient and gap before motivated assessment",
        },
    )
    assert inspected.status_code == 200 and len(inspected.context["decisions"].forms) == len(values)
    payload = {
        "key": assessment_key,
        "version": assessment_version,
        "operation": "propose",
        "decisions-TOTAL_FORMS": len(values),
        "decisions-INITIAL_FORMS": len(values),
        "decisions-MIN_NUM_FORMS": 0,
        "decisions-MAX_NUM_FORMS": 1000,
    }
    for index, (token, value) in enumerate(values.items()):
        payload[f"decisions-{index}-target"] = token
        for field, text in value.items():
            payload[f"decisions-{index}-{field}"] = text
    assert other.post(assessment_path, {**payload, "decisions-0-evidence": ""}).status_code == 400
    assert other.post(assessment_path, payload).status_code == 302
    assert other.post(assessment_path, payload).status_code == 302
    from apps.safety.models import RightsRectificationRecipientAssessment

    assessment = RightsRectificationRecipientAssessment.objects.get()
    assert other.get(assessment_path).context["decisions"] is None
    assert (
        propose_assessment(
            reviewer, case.pk, updated_inventory.pk, assessment_key, assessment_version, values
        ).pk
        == assessment.pk
    )
    assert unseal(assessment.encrypted_decisions) == values
    case.refresh_from_db()
    assert case.status == "reviewing" and case.scope_status == "unverified"
    assert case.version == assessment_version + 1
    from django.core.exceptions import PermissionDenied
    from test_rights_verification import read

    from apps.safety.recipient_review import inspect as inspect_review
    from apps.safety.recipient_review import review as review_assessment

    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "manage_rights_assignment",
                "verify_rights_scope",
                "review_recipient_assessment",
            ]
        )
    )
    original.user_permissions.add(Permission.objects.get(codename="review_recipient_assessment"))
    reviewer = User.objects.get(pk=reviewer.pk)
    original = User.objects.get(pk=original.pk)
    with pytest.raises(PermissionDenied):
        inspect_review(
            reviewer,
            case.pk,
            assessment.pk,
            case.version,
            "Attempt own assessment review must be rejected",
        )
    read(other, case)
    act(reviewer, case.pk, uuid.uuid4(), case.version, "unassign", REASON)
    case.refresh_from_db()
    act(original, case.pk, uuid.uuid4(), case.version, "claim", REASON)
    case.refresh_from_db()
    with pytest.raises(ValidationError):
        inspect_review(
            original,
            case.pk,
            assessment.pk,
            case.version,
            "Fresh post-assessment procedure is still required",
        )
    fresh(case, original, staff, reviewer, other)
    review_key = uuid.uuid4()
    review_version = case.version
    with pytest.raises(ValidationError, match="Read assessment"):
        review_assessment(
            original, case.pk, assessment.pk, review_key, review_version, recipient_outcome, REASON
        )
    from apps.safety.models import RightsRectificationManagerNotice

    changed_notice = RightsRectificationManagerNotice.objects.get(
        execution=applied, recipient=manager
    )
    receipt_time = changed_notice.acknowledged_at
    changed_notice.acknowledged_at = None
    changed_notice.save(update_fields=["acknowledged_at"])
    with pytest.raises(ValidationError, match="unchanged recipient history"):
        inspect_review(
            original,
            case.pk,
            assessment.pk,
            review_version,
            "Read modified history must require reassessment",
        )
    changed_notice.acknowledged_at = receipt_time
    changed_notice.save(update_fields=["acknowledged_at"])
    review_path = f"/en/moderation/rights/{case.pk}/recipient-assessment/{assessment.pk}/review/"
    assert other.get(review_path).status_code == 403
    page = staff.get(f"/en/moderation/rights/{case.pk}/")
    assert len(page.context["recipient_assessments"]) == 1
    assert b"Read recipient grounds" not in page.content
    assert staff.get(review_path).context["rows"] is None
    assert Client(enforce_csrf_checks=True).post(review_path).status_code == 403
    inspected = staff.post(
        review_path,
        {
            "key": uuid.uuid4(),
            "version": review_version,
            "operation": "inspect",
            "purpose": "Read recipient grounds and evidence independently",
        },
    )
    assert inspected.status_code == 200 and len(inspected.context["rows"]) == len(values)
    assert staff.get(review_path).context["rows"] is None
    payload = {
        "key": review_key,
        "version": review_version,
        "operation": "review",
        "outcome": recipient_outcome,
        "reason": REASON,
    }
    assert staff.post(review_path, payload).status_code == 302
    assert staff.post(review_path, payload).status_code == 302
    from apps.safety.models import RightsRectificationRecipientReview

    checked = RightsRectificationRecipientReview.objects.get()
    assert (
        review_assessment(
            original, case.pk, assessment.pk, review_key, review_version, recipient_outcome, REASON
        ).pk
        == checked.pk
    )
    assert checked.outcome == recipient_outcome
    original.user_permissions.remove(Permission.objects.get(codename="review_recipient_assessment"))
    original = User.objects.get(pk=original.pk)
    with pytest.raises(PermissionDenied):
        review_assessment(
            original, case.pk, assessment.pk, review_key, review_version, recipient_outcome, REASON
        )
    case.refresh_from_db()
    assert case.status == "reviewing" and case.version == review_version + 1
    assert person.listing.status != "published"
    # If the usable correction is withdrawn, ordinary draft creation must not
    # fall back to cloning the still-preserved historical approved version.
    corrected.status = "withdrawn"
    corrected.save(update_fields=["status"])
    assert manager_client.post(f"/en/person/{person.pk}/listing/start/").status_code == 302
    blank = person.listing.revisions.filter(status="draft").get()
    assert blank.source_revision_id is None
    assert not blank.title and not blank.description and not blank.photos.exists()
    assert not blank.rates.exists() and not blank.categories.exists()
    for language in ["es", "en"]:
        page = manager_client.get(f"/{language}/draft/{blank.pk}/1/")
        assert page.status_code == 200 and page.context["history_excluded"] is True
        text = "This draft started empty" if language == "en" else "Este borrador se inició vacío"
        assert text.encode() in page.content
        assert old_title.encode() not in page.content
    old_revision.refresh_from_db()
    assert old_revision.title == old_title and old_revision.description == old_description
    type(person).objects.filter(pk=person.pk).update(manager_version=person.manager_version + 1)
    assert len(manager_client.get(inbox).context["notices"]) == 0
    assert manager_client.post(acknowledge).status_code == 404
