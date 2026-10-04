"""SQL authority tests with synthetic persisted ledgers, not proof of human approval."""

import shutil
from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.mediafiles.models import Blob, Photo
from apps.safety import models
from apps.safety.crypto import seal
from apps.safety.photo_dispositions import active_withdrawals

pytestmark = pytest.mark.django_db(transaction=True)


def ledger(person):
    now = timezone.now()
    user = person.subject
    case = models.RightsRequest.objects.create(
        submission_key=uuid4(),
        manager_version=person.manager_version,
        person=person,
        kind="rectify",
        encrypted_payload=seal({}),
        received_at=now,
        initial_due_at=now + timedelta(days=30),
        receipt_expires_at=now + timedelta(days=30),
    )
    proof = models.RightsProof.objects.create(
        key=uuid4(),
        request=case,
        person=person,
        initiated_by=user,
        case_version=1,
        manager_version=person.manager_version,
        scope="rectify",
        expires_at=now + timedelta(hours=1),
        encrypted_reason=seal({}),
    )

    def action(operation):
        return models.RightsAction.objects.create(
            key=uuid4(),
            request=case,
            actor=user,
            expected_version=1,
            operation=operation,
            encrypted_reason=seal({}),
        )

    proposal = models.RightsRectificationProposal.objects.create(
        action=action("rectify_propose"),
        proof=proof,
        person=person,
        source_revision=person.listing.approved_revision,
        encrypted_changes=seal({"photos": []}),
    )
    review = models.RightsRectificationReview.objects.create(
        proposal=proposal,
        action=action("rectify_review"),
        proof=proof,
        outcome="approved",
    )
    response = models.RightsResponse.objects.create(
        key=uuid4(),
        request=case,
        actor=user,
        case_version=1,
        response_version=1,
        kind="progress",
        encrypted_reason=seal({}),
        encrypted_response=seal({}),
    )
    notification = models.RightsRectificationNotification.objects.create(
        review=review,
        action=action("rectify_notify"),
        response=response,
        proof=proof,
    )
    return models.RightsRectificationExecution.objects.create(
        notification=notification,
        action=action("rectify_execute"),
        proof=proof,
        encrypted_previous_values=seal({}),
        resulting_rights_version=person.rights_version,
    )


def test_latest_explicit_file_decision_is_scoped_and_survives_unrelated_corrections(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    original = person.listing.approved_revision.photos.first()
    other = Photo.objects.create(
        revision=original.revision,
        blob=Blob.objects.create(sha256="f" * 64),
        position=7,
    )

    def record(execution, photo, outcome):
        return models.RightsRectificationPhotoDisposition.objects.create(
            execution=execution,
            source_photo=photo,
            blob=photo.blob,
            outcome=outcome,
        )

    first = ledger(person)
    a = record(first, original, "withdrawn")
    b = record(first, other, "withdrawn")
    peer_photo, _ = Photo.objects.get_or_create(
        revision=peer.listing.revisions.first(), blob=original.blob
    )
    record(ledger(peer), peer_photo, "retained")  # Same bytes, other person.
    assert set(active_withdrawals(person.pk).values_list("pk", flat=True)) == {a.pk, b.pk}
    retained = record(ledger(person), original, "retained")
    assert set(active_withdrawals(person.pk).values_list("pk", flat=True)) == {b.pk}
    latest = record(ledger(person), original, "withdrawn")
    # Exercise the deterministic tie breaker as well as ordinary chronological order.
    models.RightsRectificationPhotoDisposition.objects.filter(
        pk__in=[a.pk, retained.pk, latest.pk]
    ).update(created_at=timezone.now())
    assert set(active_withdrawals(person.pk).values_list("pk", flat=True)) == {b.pk, latest.pk}
    assert not active_withdrawals(peer.pk).exists()


def test_protected_exact_and_visual_candidates_are_private_and_scoped(request):
    import hashlib
    import io

    from django.core.files.base import ContentFile
    from PIL import Image

    from apps.listings.models import Revision
    from apps.mediafiles.services import process
    from apps.safety.photo_reintroduction import detect

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    original = person.listing.approved_revision.photos.first()
    execution = ledger(person)
    disposition = models.RightsRectificationPhotoDisposition.objects.create(
        execution=execution,
        source_photo=original,
        blob=original.blob,
        outcome="withdrawn",
    )
    revision = Revision.objects.create(
        listing=person.listing,
        manager_version=person.manager_version,
        status="draft",
    )
    photo = Photo.objects.create(revision=revision, blob=original.blob)
    detect(photo.pk)
    detect(photo.pk)
    event = models.RightsPhotoReintroduction.objects.get(photo=photo)
    assert event.disposition_id == disposition.pk and event.method == "sha256"
    assert event.uploaded_blob_id == photo.blob_id
    peer_revision = Revision.objects.create(
        listing=peer.listing,
        manager_version=peer.manager_version,
        status="draft",
    )
    peer_photo = Photo.objects.create(revision=peer_revision, blob=original.blob)
    detect(peer_photo.pk)
    assert not models.RightsPhotoReintroduction.objects.filter(photo=peer_photo).exists()
    with original.blob.derivative.open("rb") as source:
        image = Image.open(source).convert("RGB")
    for cropped in [False, True]:
        variant = image
        if cropped:
            width, height = image.size
            variant = image.crop((width // 10, height // 10, width * 9 // 10, height * 9 // 10))
        output = io.BytesIO()
        variant.save(output, format="JPEG", quality=72)
        raw = output.getvalue()
        blob = Blob.objects.create(sha256=hashlib.sha256(raw).hexdigest())
        blob.original.save(str(uuid4()), ContentFile(raw))
        uploaded = Photo.objects.create(revision=revision, blob=blob, position=2 + int(cropped))
        process(blob.pk)
        candidate = models.RightsPhotoReintroduction.objects.get(photo=uploaded)
        assert candidate.disposition_id == disposition.pk and candidate.method == "regional"
    assert models.RightsPhotoReintroduction.objects.filter(photo=photo).count() == 1
    assert not models.RightsPhotoReintroduction.objects.filter(photo=original).exists()


@pytest.mark.parametrize("language", ["es", "en"])
def test_review_requires_independence_current_audit_and_invalidates_changed_resources(
    request, settings, live_server, language
):
    from django.contrib.auth.models import Permission
    from django.core.exceptions import PermissionDenied, ValidationError

    from apps.core.models import LegalAcceptance, User
    from apps.listings.models import Revision
    from apps.safety.photo_reintroduction import detect
    from apps.safety.photo_reintroduction_review import decide, inspect, publication_pending

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    original = person.listing.approved_revision.photos.first()
    execution = ledger(person)
    execution.proof.status = "passed"  # Synthetic persisted authority, no provider verification.
    execution.proof.save(update_fields=["status"])
    models.RightsRectificationPhotoDisposition.objects.create(
        execution=execution,
        source_photo=original,
        blob=original.blob,
        outcome="withdrawn",
    )
    revision = Revision.objects.create(
        listing=person.listing,
        manager_version=person.manager_version,
        status="draft",
    )
    photo = Photo.objects.create(revision=revision, blob=original.blob)
    detect(photo.pk)
    candidate = models.RightsPhotoReintroduction.objects.get(photo=photo)
    assert publication_pending(revision)
    reviewer = User.objects.create_user(
        username="independent-reuse-reviewer",
        email="reuse-reviewer@example.invalid",
        mfa_enabled=True,
        email_verified_at=timezone.now(),
    )
    perm = Permission.objects.get(codename="review_photo_reintroduction")
    with pytest.raises(PermissionDenied):
        inspect(reviewer, candidate.pk, uuid4(), 1, "Review independently scoped photo use")
    reviewer.user_permissions.add(perm)
    reviewer = User.objects.get(pk=reviewer.pk)
    person.subject.user_permissions.add(perm)
    person.subject.mfa_enabled = True
    person.subject.save(update_fields=["mfa_enabled"])
    with pytest.raises(PermissionDenied):
        inspect(person.subject, candidate.pk, uuid4(), 1, "Review independently scoped photo use")
    with pytest.raises(ValidationError):
        decide(
            reviewer,
            candidate.pk,
            0,
            uuid4(),
            1,
            "authorize",
            "Independent current authorization evidence reviewed",
            "synthetic-ref",
        )
    from django.test import Client

    from apps.listings.submissions import validate_submission

    with pytest.raises(ValidationError, match="private review"):
        validate_submission(revision, person)
    for acceptance in LegalAcceptance.objects.filter(
        user=person.subject, action__in=["account_terms", "privacy_notice"]
    ):
        LegalAcceptance.objects.create(
            user=reviewer, document=acceptance.document, action=acceptance.action
        )
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    path = f"/en/moderation/photo-reuse/{candidate.pk}/"
    page = client.get(path)
    assert page.status_code == 200 and b"<img" not in page.content
    assert client.get(f"{path}reads/999999/uploaded/").status_code == 404
    assert client.get("/en/moderation/photo-reuse/").status_code == 200
    inspected = client.post(
        path,
        {
            "operation": "inspect",
            "key": uuid4(),
            "version": 1,
            "purpose": "Inspect independently authorized scoped images",
        },
    )
    assert inspected.status_code == 200, inspected.content
    browser_read = inspected.context["read"]
    for side in ["uploaded", "withdrawn"]:
        image = client.get(f"{path}reads/{browser_read.pk}/{side}/")
        assert image.status_code == 200 and b"".join(image.streaming_content)
        assert image["Cache-Control"] == "private, no-store"
        image.close()
    owner = Client()
    owner.force_login(person.subject)
    owner_session = owner.session
    owner_session["mfa_version"] = person.subject.mfa_version
    owner_session.save()
    assert owner.get(f"{path}reads/{browser_read.pk}/withdrawn/").status_code == 403
    key = uuid4()
    read = inspect(reviewer, candidate.pk, key, 1, "Review independently scoped photo use")
    assert inspect(reviewer, candidate.pk, key, 1, read.purpose).pk == read.pk
    with pytest.raises(ValidationError):
        decide(
            reviewer,
            candidate.pk,
            read.pk,
            uuid4(),
            1,
            "false_positive",
            "Exact bytes cannot be a visual false positive",
            "synthetic-ref",
        )
    decision_key = uuid4()
    result = decide(
        reviewer,
        candidate.pk,
        read.pk,
        decision_key,
        1,
        "authorize",
        "Independent current authorization evidence reviewed",
        "synthetic-ref",
    )
    assert not publication_pending(revision)
    assert b"Current use authorized" in client.get(path).content
    assert client.get(f"{path}reads/{browser_read.pk}/withdrawn/").status_code == 404
    assert (
        decide(
            reviewer,
            candidate.pk,
            read.pk,
            decision_key,
            1,
            "authorize",
            "Independent current authorization evidence reviewed",
            "synthetic-ref",
        ).pk
        == result.pk
    )
    assert "authorization evidence" not in result.encrypted_reason
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 390, "height": 844})
        context.add_cookies(
            [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": client.session.session_key,
                    "url": live_server.url,
                }
            ]
        )
        page = context.new_page()
        page.goto(f"{live_server.url}/{language}/moderation/photo-reuse/{candidate.pk}/")
        assert page.locator("img").count() == 0
        page.locator('[name="purpose"]').fill("Independent mobile audit of current image authority")
        page.get_by_role(
            "button",
            name="Record access and inspect images"
            if language == "en"
            else "Registrar consulta y revisar imágenes",
            exact=True,
        ).click()
        expect(page.locator("img")).to_have_count(2)
        page.wait_for_load_state("load")
        assert page.locator("img").evaluate_all(
            "images => images.every(image => image.complete && image.naturalWidth > 0)"
        )
        page.locator('[name="outcome"]').select_option("authorize")
        page.locator('[name="reason"]').fill(
            "Independent current permission and image evidence reviewed"
        )
        page.locator('[name="reference"]').fill("synthetic-mobile-ref")
        page.get_by_role(
            "button",
            name="Record independent decision"
            if language == "en"
            else "Registrar decisión independiente",
            exact=True,
        ).click()
        expect(
            page.get_by_text(
                "Current use authorized" if language == "en" else "Uso actual autorizado",
                exact=False,
            )
        ).to_be_visible()
        expect(page.locator('[name="outcome"]')).to_have_count(0)
        page.reload()
        expect(
            page.get_by_text(
                "Current use authorized" if language == "en" else "Uso actual autorizado",
                exact=False,
            )
        ).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        context.close()
        browser.close()
    candidate.refresh_from_db()
    fresh_read = inspect(
        reviewer,
        candidate.pk,
        uuid4(),
        candidate.review_version,
        "Audit current resources before simulated resource change",
    )
    original.blob.signature = {}
    original.blob.save(update_fields=["signature"])
    assert publication_pending(revision)
    changed_page = client.get(path)
    assert changed_page.status_code == 200 and not changed_page.context["decision_current"]
    assert b"previous decision requires a new review" in changed_page.content
    assert client.get(f"{path}reads/{fresh_read.pk}/withdrawn/").status_code == 404
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(reviewer)
    csrf_session = csrf.session
    csrf_session["mfa_version"] = reviewer.mfa_version
    csrf_session.save()
    assert csrf.post(path, {"operation": "inspect"}).status_code == 403
    stale_session = client.session
    stale_session["mfa_version"] = reviewer.mfa_version - 1
    stale_session.save()
    assert client.get(path).status_code in {302, 403}
    with pytest.raises(ValidationError):
        decide(
            reviewer,
            candidate.pk,
            fresh_read.pk,
            uuid4(),
            candidate.review_version,
            "authorize",
            "Independent current authorization evidence reviewed",
            "synthetic-ref",
        )
