import json
import uuid

import pytest
from django.core.exceptions import ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared, url

from apps.core.models import LegalAcceptance, Person, PhoneClaim, User
from apps.safety.models import RightsExport
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)


def test_account_projection_is_subject_only_redactable_and_never_contains_secrets(
    request, settings
):
    case, user, _, client, receipt, person = prepared(request, settings)
    subject = person.subject
    subject.first_name, subject.last_name = "Synthetic Given", "Synthetic Family"
    subject.save(update_fields=["first_name", "last_name"])
    source = preview(
        user, case.pk, case.version, "Review subject account and profile data before release"
    )
    assert source["schema"] == "subject-profile-copy-v2"
    assert source["subject_account"]["email"] == subject.email
    assert source["subject_account"]["first_name"] == "Synthetic Given"
    assert len(source["legal_acceptances"]) == LegalAcceptance.objects.filter(user=subject).count()
    forbidden = [
        subject.password,
        person.agency.owner.email,
        "mfa_secret_encrypted",
        "session_version",
        "recovery_digest",
        "token",
        "digest",
    ]
    serialized = json.dumps(source)
    assert all(value not in serialized for value in forbidden)
    foreign = json.loads(serialized)
    foreign["subject_account"]["email"] = person.agency.owner.email
    with pytest.raises(ValidationError):
        generate(user, case.pk, uuid.uuid4(), case.version, "Release scoped account copy", foreign)
    source["subject_account"]["last_name"] = ""
    export = generate(
        user, case.pk, uuid.uuid4(), case.version, "Release redacted subject account copy", source
    )
    copy = client.post(url(receipt, export), {"key": uuid.uuid4()}).json()
    assert copy["subject_account"]["last_name"] == "" and copy["partial"]
    assert person.agency.owner.email not in json.dumps(copy)


def test_subject_account_and_image_inventory_drift_requires_new_preview(request, settings):
    case, user, _, _, _, person = prepared(request, settings)
    source = preview(
        user, case.pk, case.version, "Inspect source before generating a current private copy"
    )
    User.objects.filter(pk=person.subject_id).update(first_name="Account changed after preview")
    with pytest.raises(ValidationError):
        generate(user, case.pk, uuid.uuid4(), case.version, "Release stale account copy", source)
    source = preview(user, case.pk, case.version, "Inspect updated account and image inventory")
    photo = person.listing.revisions.first().photos.first()
    assert photo and source["revisions"][0]["images"]
    assert all(
        not item["content_included"]
        for revision in source["revisions"]
        for item in revision["images"]
    )
    photo.position += 1
    photo.save(update_fields=["position"])
    with pytest.raises(ValidationError):
        generate(
            user, case.pk, uuid.uuid4(), case.version, "Release stale image inventory copy", source
        )
    assert not RightsExport.objects.exists()


def test_shared_contact_is_withheld_and_personal_claim_can_be_redacted(request, settings):
    case, user, _, _, _, person = prepared(request, settings)
    source = preview(
        user, case.pk, case.version, "Inspect shared publication contacts before disclosure"
    )
    assert all(item["contacts"]["phone"] == "" for item in source["revisions"])
    assert all(item["contacts"]["telegram"] == "" for item in source["revisions"])
    revision = person.listing.revisions.first()
    # Scoped synthetic ownership fixture; this is not real telephone verification.
    claim = PhoneClaim.objects.get(phone=revision.phone)
    claim.agency = None
    claim.individual = person.subject
    claim.save()
    person.phone_claim = claim
    person.save(update_fields=["phone_claim"])
    source = preview(
        user, case.pk, case.version, "Inspect explicitly subject-owned contact for private copy"
    )
    assert source["revisions"][0]["contacts"]["phone"] == revision.phone
    source["revisions"][0]["contacts"]["phone"] = ""
    source["revisions"][0]["contacts"]["whatsapp"] = False
    generate(user, case.pk, uuid.uuid4(), case.version, "Release copy with contact removed", source)


def test_missing_subject_never_substitutes_agency_owner_or_requester(request):
    from apps.safety.rights_copy_data import subject_data

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    person.subject = None
    result = subject_data(person)
    assert result["subject_account"] is None and not result["legal_acceptances"]
    assert person.agency.owner.email not in json.dumps(result)
    assert not result["representation"]["verifications"]


def test_favorites_projection_is_own_activity_and_drift_blocks_stale_copy(request, settings):
    from apps.listings.models import Favorite

    case, user, _, client, receipt, person = prepared(request, settings)
    owner = person.agency.owner
    own = Favorite.objects.create(user=person.subject, listing=person.listing)
    Favorite.objects.create(user=owner, listing=person.listing)
    source = preview(
        user, case.pk, case.version, "Inspect subject favorite activity before release"
    )
    assert source["account_activity"]["favorites"] == [
        {"listing_reference": str(own.listing_id), "created_at": own.created_at.isoformat()}
    ]
    assert owner.email not in json.dumps(source["account_activity"])
    own.delete()
    with pytest.raises(ValidationError):
        generate(
            user, case.pk, uuid.uuid4(), case.version, "Release stale subject favorite copy", source
        )
    source = preview(user, case.pk, case.version, "Inspect refreshed subject favorite activity")
    assert source["account_activity"]["favorites"] == []
    export = generate(
        user, case.pk, uuid.uuid4(), case.version, "Release reviewed subject favorite copy", source
    )
    assert (
        client.post(url(receipt, export), {"key": uuid.uuid4()}).json()["account_activity"]
        == source["account_activity"]
    )


def test_copy_account_lock_blocks_concurrent_favorite_removal(request, settings):
    import time
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from django.db import close_old_connections, connection, connections, transaction
    from django.test import Client

    from apps.listings.models import Favorite
    from apps.safety.rights_exports import source_copy

    _, _, _, _, _, person = prepared(request, settings)
    favorite = Favorite.objects.create(user=person.subject, listing=person.listing)
    client = Client()
    client.force_login(person.subject)
    ready = Event()
    backend = {}

    def remove():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend["pid"] = cursor.fetchone()[0]
            ready.set()
            return client.post(f"/en/favorites/{favorite.pk}/remove/").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            copy = source_copy(person, person.listing)
            assert len(copy["account_activity"]["favorites"]) == 1
            future = pool.submit(remove)
            assert ready.wait(timeout=5)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                own_pid = cursor.fetchone()[0]
                deadline = time.monotonic() + 5
                blocked = False
                while time.monotonic() < deadline:
                    cursor.execute("SELECT pg_blocking_pids(%s)", [backend["pid"]])
                    blocked = own_pid in cursor.fetchone()[0]
                    if blocked:
                        break
                    time.sleep(0.02)
            assert blocked and not future.done()
            assert Favorite.objects.filter(pk=favorite.pk).exists()
        assert future.result(timeout=10) == 302
    assert not Favorite.objects.filter(pk=favorite.pk).exists()


def test_representation_history_is_scoped_and_new_action_invalidates_preview(request, settings):
    from apps.core.models import RepresentationAction

    case, user, _, client, receipt, person = prepared(request, settings)
    subject = person.subject
    foreign_person = Person.objects.exclude(pk=person.pk).first()
    RepresentationAction.objects.create(
        person=foreign_person,
        subject=subject,
        manager_version=999,
        action="transfer",
        manager_kind="agency",
        manager_id="foreign-manager-secret",
    )
    RepresentationAction.objects.create(
        person=person,
        subject=person.agency.owner,
        manager_version=998,
        action="revoke",
        manager_kind="agency",
        manager_id="other-subject-secret",
    )
    action = RepresentationAction.objects.create(
        person=person,
        subject=subject,
        manager_version=person.manager_version,
        action="authorize",
        manager_kind="agency",
        manager_id="private-manager-identifier",
    )
    source = preview(
        user, case.pk, case.version, "Inspect own representation history before copy release"
    )
    history = source["representation"]["history"]
    assert any(
        item["created_at"] == action.created_at.isoformat() and item["action"] == "authorize"
        for item in history
    )
    assert not any(item["manager_version"] in {998, 999} for item in history)
    assert all("manager_id" not in item and "subject" not in item for item in history)
    assert "private-manager-identifier" not in json.dumps(source)
    RepresentationAction.objects.create(
        person=person, subject=subject, manager_version=person.manager_version, action="revoke"
    )
    with pytest.raises(ValidationError):
        generate(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "Release outdated representation history copy",
            source,
        )
    fresh = preview(user, case.pk, case.version, "Inspect refreshed own representation history")
    export = generate(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Release reviewed representation history copy",
        fresh,
    )
    copy = client.post(url(receipt, export), {"key": uuid.uuid4()}).json()
    assert copy["representation"]["history"] == fresh["representation"]["history"]
