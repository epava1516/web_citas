import base64
import json
from io import StringIO
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.core.management import call_command
from django.test import Client
from test_erasure_execution import payload
from test_recovery_apply import stored_receipt
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read
from test_shared_media_redaction import prepared

from apps.core.models import User
from apps.mediafiles.models import Blob, Photo
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record
from apps.safety.models import RecoveryApplication, RecoveryOutbox
from apps.safety.recovery_apply import reconcile
from apps.safety.recovery_media import destroy_due
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def test_two_authorized_media_executions_recover_from_before_shared_redaction(
    request, settings, monkeypatch, tmp_path
):
    case, actor, staff, person, plan, shared, peer_photo, exclusive = prepared(
        request, settings, monkeypatch, mixed=True
    )
    before = list(Photo.objects.filter(revision__listing__person=person).values())
    first = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    first_receipt = unseal(RecoveryOutbox.objects.get(execution=first).encrypted_event)
    case.refresh_from_db()
    read(staff, case)
    proof = start(
        actor, case.pk, uuid4(), case.version, "Review remaining exclusive recovery fixture"
    )
    case.refresh_from_db()
    verifier = User.objects.get(username="fixture-v1-visitor")
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
            uuid4(),
            case.version,
            "passed",
            "Independent synthetic remaining-media assessment",
        ),
    )
    case.refresh_from_db()
    read(staff, case)
    snapshot = prepare(actor, case.pk, uuid4(), case.version, "Inventory remaining exclusive files")
    decisions = [
        row | {"operation": "erase"} if row["purpose"] == "media" else row
        for row in unseal(plan.encrypted_decisions)["decisions"]
    ]
    final_plan = record(actor, case.pk, snapshot.pk, uuid4(), case.version, decisions)
    second = execute(actor, case.pk, final_plan.pk, **(payload(case) | {"purposes": ["media"]}))
    second_receipt = unseal(RecoveryOutbox.objects.get(execution=second).encrypted_event)
    # Restore own pre-redaction photo links; files were not physically deleted yet.
    for row in before:
        Photo.objects.filter(pk=row["id"]).update(**{k: v for k, v in row.items() if k != "id"})
    replacements = [
        row["replacement"]
        for row in first_receipt["references"]["resources"]["photos"]
        if row["shared"]
    ]
    Blob.objects.filter(pk__in=replacements).delete()
    encryption, signing = Fernet.generate_key(), b"s" * 32
    store, checkpoint = stored_receipt(
        tmp_path, first_receipt, encryption=encryption, signing=signing
    )
    encoded, _ = store.codec.append(store.checkpoint(), str(uuid4()), second_receipt)
    store.append(encoded)
    monkeypatch.setenv("RECOVERY_ENCRYPTION_KEY", encryption.decode())
    monkeypatch.setenv("RECOVERY_SIGNING_KEY", base64.urlsafe_b64encode(signing).decode())
    output = StringIO()
    call_command(
        "check_recovery_ledger",
        expected_ledger=store.checkpoint().ledger,
        expected_sequence=store.checkpoint().sequence,
        expected_head=store.checkpoint().head,
        records_directory=str(store.records_directory),
        checkpoint_directory=str(store.checkpoint_directory),
        backup_ledger=checkpoint.ledger,
        backup_sequence=0,
        backup_head=checkpoint.head,
        stdout=output,
    )
    assert json.loads(output.getvalue())["events_checked"] == 2
    assert (
        not RecoveryApplication.objects.exists()
        and not Blob.objects.filter(pk__in=replacements).exists()
    )
    settings.RECOVERY_MODE = True
    assert reconcile(store, checkpoint)["applied"] == 2
    assert destroy_due(store, checkpoint) == 1
    peer_photo.refresh_from_db()
    assert peer_photo.blob_id == shared.pk and peer_photo.removed_at is None
    assert shared.original.storage.exists(shared.original.name)
    assert exclusive.original.storage.exists(exclusive.original.name) is False
    assert reconcile(store, checkpoint)["applied"] == 0
    assert RecoveryApplication.objects.count() == 2
