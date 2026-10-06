from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.test import Client
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AccountToken, RecoveryCode
from apps.listings.models import Favorite
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryApplication, RecoveryMediaJob, RecoveryOutbox
from apps.safety.recovery_apply import reconcile
from scripts.recovery_ledger import ZERO, Checkpoint, LedgerIntegrityError, RecoveryLedger
from scripts.recovery_store import RecoveryStore

pytestmark = pytest.mark.django_db(transaction=True)


def stored_receipt(tmp_path, receipt):
    records, checkpoints = tmp_path / "records", tmp_path / "checkpoints"
    records.mkdir(mode=0o700)
    checkpoints.mkdir(mode=0o700)
    codec = RecoveryLedger(Fernet.generate_key(), b"a" * 32)
    store = RecoveryStore(records, checkpoints, codec)
    start = Checkpoint(str(uuid4()), 0, ZERO)
    store.initialize(start)
    record, _ = codec.append(start, str(uuid4()), receipt)
    store.append(record)
    return store, start


def test_reintroduced_credentials_preferences_and_copy_removed_with_replay(
    request, settings, monkeypatch, tmp_path
):
    case, actor, staff, client, receipt, person, plan, export, image, outsider = plan_fixture(
        request, settings, monkeypatch
    )
    subject = person.subject
    tokens = list(AccountToken.objects.filter(user=subject))
    codes = list(RecoveryCode.objects.filter(user=subject))
    favorites = list(Favorite.objects.filter(user=subject))
    epochs = subject.session_version, subject.mfa_version
    old_content = export.encrypted_payload
    execution = execute(actor, case.pk, plan.pk, **payload(case))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    AccountToken.objects.bulk_create(tokens)
    RecoveryCode.objects.bulk_create(codes)
    Favorite.objects.bulk_create(favorites)
    type(subject).objects.filter(pk=subject.pk).update(
        session_version=epochs[0], mfa_version=epochs[1]
    )
    type(export).objects.filter(pk=export.pk).update(encrypted_payload=old_content, purged_at=None)
    assert AccountToken.objects.filter(user=subject).exists()
    store, start = stored_receipt(tmp_path, event)
    with pytest.raises(RuntimeError):
        reconcile(store, start)
    assert RecoveryApplication.objects.count() == 0
    settings.RECOVERY_MODE = True
    for path in ["/health/", "/en/", "/admin/"]:
        response = Client().get(path)
        assert response.status_code == 503 and response["Cache-Control"] == "no-store"
    result = reconcile(store, start)
    assert result == {"applied": 1, "pending_media_jobs": 0, "publication_authorized": False}
    assert not AccountToken.objects.filter(user=subject).exists()
    assert not RecoveryCode.objects.filter(user=subject).exists()
    assert not Favorite.objects.filter(user=subject).exists()
    assert Favorite.objects.filter(user=outsider, listing=person.listing).exists()
    export.refresh_from_db()
    subject.refresh_from_db()
    assert not export.encrypted_payload and export.purged_at
    assert subject.session_version >= event["references"]["account"]["minimum_session_version"]
    after = subject.session_version, subject.mfa_version
    assert reconcile(store, start)["applied"] == 0
    subject.refresh_from_db()
    assert (subject.session_version, subject.mfa_version) == after
    assert RecoveryApplication.objects.count() == 1
    application = RecoveryApplication.objects.get()
    application.encrypted_receipt = "Synthetic damaged recovery audit"
    application.save(update_fields=["encrypted_receipt"])
    with pytest.raises(LedgerIntegrityError):
        reconcile(store, start)
    subject.refresh_from_db()
    assert (subject.session_version, subject.mfa_version) == after


def test_foreign_scope_rolls_back_whole_application(request, settings, monkeypatch, tmp_path):
    case, actor, staff, client, receipt, person, plan, export, image, outsider = plan_fixture(
        request, settings, monkeypatch
    )
    execution = execute(actor, case.pk, plan.pk, **payload(case))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    event["references"]["resources"]["favorites"] = [
        str(Favorite.objects.get(user=outsider, listing=person.listing).pk)
    ]
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    before = list(Favorite.objects.values())
    with pytest.raises(LedgerIntegrityError):
        reconcile(store, start)
    assert not RecoveryApplication.objects.exists() and list(Favorite.objects.values()) == before


def test_media_recovery_requeues_even_if_old_job_claims_completed(
    request, settings, monkeypatch, tmp_path
):
    from test_media_erasure import setup

    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    assert reconcile(store, start)["pending_media_jobs"] >= 1
    job = RecoveryMediaJob.objects.get(blob=blob)
    job.status = "completed"
    job.encrypted_paths = ""
    job.save(update_fields=["status", "encrypted_paths"])
    assert blob.original.storage.exists(blob.original.name)
    assert reconcile(store, start)["applied"] == 0
    job.refresh_from_db()
    assert job.status == "queued" and unseal(job.encrypted_paths)["original"] == blob.original.name


def test_restored_contact_and_consent_are_revoked_without_changing_peer(
    request, settings, monkeypatch, tmp_path
):
    from test_contact_erasure import SELECTED, prepared

    from apps.core.models import Person, PhoneChallenge, RepresentationInvitation
    from apps.listings.models import Listing, Revision

    case, actor, _, person, plan, challenge, invitation, _, _ = prepared(
        request, settings, monkeypatch
    )
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    peer_person = Person.objects.filter(pk=peer.pk).values().get()
    peer_revisions = list(Revision.objects.filter(listing__person=peer).values())
    restored_person = {
        name: getattr(person, name)
        for name in [
            "phone_claim_id",
            "consent_revoked_at",
            "age_status",
            "consent_version",
            "manager_version",
            "rights_version",
        ]
    }
    restored_listing = (
        Listing.objects.filter(person=person)
        .values("status", "available_until", "lifecycle_version")
        .get()
    )
    restored_revisions = list(
        Revision.objects.filter(listing__person=person).values(
            "pk", "phone", "whatsapp", "edit_version", "updated_at"
        )
    )
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": SELECTED}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    # Recreate the exact pre-erasure fields/resources, as an old backup would.
    Person.objects.filter(pk=person.pk).update(**restored_person)
    Listing.objects.filter(person=person).update(**restored_listing)
    for row in restored_revisions:
        Revision.objects.filter(pk=row["pk"]).update(**{k: v for k, v in row.items() if k != "pk"})
    PhoneChallenge.objects.bulk_create([challenge])
    RepresentationInvitation.objects.bulk_create([invitation])
    person.refresh_from_db()
    assert person.phone_claim_id and not person.consent_revoked_at
    assert person.consent_version == person.manager_version
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    assert reconcile(store, start)["applied"] == 1
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert not PhoneChallenge.objects.filter(person=person).exists()
    assert not RepresentationInvitation.objects.filter(person=person).exists()
    assert person.phone_claim_id is None and person.consent_revoked_at
    assert person.age_status == "pending" and person.consent_version != person.manager_version
    assert person.listing.status == "paused"
    assert all(not row.phone and not row.whatsapp for row in person.listing.revisions.all())
    assert Person.objects.filter(pk=peer.pk).values().get() == peer_person
    assert list(Revision.objects.filter(listing__person=peer).values()) == peer_revisions
    versions = person.manager_version, person.rights_version, person.listing.lifecycle_version
    assert reconcile(store, start)["applied"] == 0
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert versions == (
        person.manager_version,
        person.rights_version,
        person.listing.lifecycle_version,
    )


@pytest.mark.parametrize("agency", [False, True])
def test_restored_account_erasure_obeys_selected_scope(
    request, settings, monkeypatch, tmp_path, agency
):
    from test_account_erasure_execution import prepared_erasure

    from apps.core.models import Agency, Person, User
    from apps.listings.models import Listing

    case, actor, _, subject, _, _, plan, purposes, copy, acceptance = prepared_erasure(
        request, settings, monkeypatch, agency
    )
    account_before = User.objects.filter(pk=subject.pk).values().get()
    people_before = list(Person.objects.values())
    listings_before = list(Listing.objects.values())
    agencies_before = list(Agency.objects.values())
    tokens = list(AccountToken.objects.filter(user=subject))
    codes = list(RecoveryCode.objects.filter(user=subject))
    favorites = list(Favorite.objects.filter(user=subject))
    old_copy = copy.encrypted_payload
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": purposes}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    User.objects.filter(pk=subject.pk).update(
        **{key: value for key, value in account_before.items() if key != "id"}
    )
    AccountToken.objects.bulk_create(tokens)
    RecoveryCode.objects.bulk_create(codes)
    Favorite.objects.bulk_create(favorites)
    type(copy).objects.filter(pk=copy.pk).update(encrypted_payload=old_copy, purged_at=None)
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    assert reconcile(store, start)["applied"] == 1
    subject.refresh_from_db()
    copy.refresh_from_db()
    assert not AccountToken.objects.filter(user=subject).exists()
    assert not RecoveryCode.objects.filter(user=subject).exists()
    assert not Favorite.objects.filter(user=subject).exists()
    assert not copy.encrypted_payload and copy.purged_at
    assert type(acceptance).objects.filter(pk=acceptance.pk).exists()
    assert list(Person.objects.values()) == people_before
    assert list(Listing.objects.values()) == listings_before
    assert list(Agency.objects.values()) == agencies_before
    if agency:
        assert subject.is_active == account_before["is_active"]
        assert subject.username == account_before["username"]
        assert subject.email == account_before["email"]
        assert subject.password == account_before["password"]
        assert subject.account_erased_at == account_before["account_erased_at"]
    else:
        assert not subject.is_active and not subject.has_usable_password()
        assert subject.account_erased_at and subject.username.startswith("erased-")
        assert subject.email.endswith("@example.invalid") and not subject.mfa_enabled
    after = User.objects.filter(pk=subject.pk).values().get()
    assert reconcile(store, start)["applied"] == 0
    assert User.objects.filter(pk=subject.pk).values().get() == after
