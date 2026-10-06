import pytest
from django.db import transaction
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Favorite
from apps.mediafiles.models import Photo
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryOutbox
from apps.safety.recovery_ownership import validate_ownership
from scripts.recovery_ledger import LedgerIntegrityError

pytestmark = pytest.mark.django_db(transaction=True)


def test_foreign_favorite_reference_rejected_without_mutation(request, settings, monkeypatch):
    case, actor, staff, client, receipt, person, plan, stored, image, outsider = plan_fixture(
        request, settings, monkeypatch
    )
    execution = execute(actor, case.pk, plan.pk, **payload(case))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    with pytest.raises(RuntimeError):
        validate_ownership(event)
    with transaction.atomic():
        assert validate_ownership(event) == event
    favorite = Favorite.objects.get(user=outsider, listing=person.listing)
    event["references"]["resources"]["favorites"] = [str(favorite.pk)]
    before = list(Favorite.objects.order_by("pk").values())
    with transaction.atomic(), pytest.raises(LedgerIntegrityError):
        validate_ownership(event)
    assert list(Favorite.objects.order_by("pk").values()) == before


def test_shared_restored_blob_blocks_recovery_without_deleting_file(request, settings, monkeypatch):
    from test_media_erasure import setup

    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    with transaction.atomic():
        assert validate_ownership(event) == event
    peer = Person.objects.exclude(pk=person.pk).first()
    Photo.objects.create(revision=peer.listing.revisions.first(), blob=blob)
    original = blob.original.name
    before = Photo.objects.count()
    with transaction.atomic(), pytest.raises(LedgerIntegrityError):
        validate_ownership(event)
    assert Photo.objects.count() == before and blob.original.storage.exists(original)
