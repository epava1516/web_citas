import base64
import json
from io import StringIO
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from django.core.management import call_command
from django.core.management.base import CommandError
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Favorite
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryOutbox
from scripts.recovery_ledger import ZERO, Checkpoint, RecoveryLedger
from scripts.recovery_store import RecoveryStore

pytestmark = pytest.mark.django_db(transaction=True)


def test_preflight_checks_real_receipt_without_applying_effects(
    request, settings, monkeypatch, tmp_path
):
    case, actor, staff, client, receipt, person, plan, stored, image, outsider = plan_fixture(
        request, settings, monkeypatch
    )
    execution = execute(actor, case.pk, plan.pk, **payload(case))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    encryption, signing = Fernet.generate_key(), b"c" * 32
    monkeypatch.setenv("RECOVERY_ENCRYPTION_KEY", encryption.decode())
    monkeypatch.setenv("RECOVERY_SIGNING_KEY", base64.urlsafe_b64encode(signing).decode())
    records, authority = tmp_path / "records", tmp_path / "authority"
    records.mkdir(mode=0o700)
    authority.mkdir(mode=0o700)
    codec = RecoveryLedger(encryption, signing)
    store = RecoveryStore(records, authority, codec)
    start = Checkpoint(str(uuid4()), 0, ZERO)
    store.initialize(start)
    record, end = codec.append(start, str(uuid4()), event)
    store.append(record)
    arguments = dict(
        records_directory=str(records),
        checkpoint_directory=str(authority),
        backup_ledger=start.ledger,
        backup_sequence=0,
        backup_head=ZERO,
    )
    before = list(Favorite.objects.order_by("pk").values())
    output = StringIO()
    call_command("check_recovery_ledger", stdout=output, **arguments)
    assert json.loads(output.getvalue()) == {
        "preflight_verified": True,
        "events_checked": 1,
        "effects_applied": False,
        "publication_authorized": False,
    }
    assert list(Favorite.objects.order_by("pk").values()) == before
    monkeypatch.delenv("RECOVERY_SIGNING_KEY")
    output = StringIO()
    with pytest.raises(CommandError):
        call_command("check_recovery_ledger", stdout=output, **arguments)
    assert output.getvalue() == ""
