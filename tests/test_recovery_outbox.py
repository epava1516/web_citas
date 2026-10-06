from uuid import uuid4

import pytest
from test_account_erasure_execution import prepared_erasure
from test_erasure_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AccountToken
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import ErasureExecution, RecoveryOutbox

pytestmark = pytest.mark.django_db(transaction=True)


def test_outbox_atomic_rollback_and_replay(request, settings, monkeypatch):
    case, actor, staff, subject, public, receipt, plan, purposes, copy, acceptance = (
        prepared_erasure(request, settings, monkeypatch, agency=True)
    )
    key, version = uuid4(), case.version
    tokens = AccountToken.objects.filter(user=subject).count()
    with monkeypatch.context() as patch:

        def fail(*args, **kwargs):
            raise RuntimeError("Synthetic outbox storage failure")

        patch.setattr(RecoveryOutbox.objects, "create", fail)
        with pytest.raises(RuntimeError):
            execute(actor, case.pk, plan.pk, key, version, purposes, REASON, True)
    assert not ErasureExecution.objects.filter(plan=plan).exists()
    assert not RecoveryOutbox.objects.exists()
    assert AccountToken.objects.filter(user=subject).count() == tokens
    case.refresh_from_db()
    assert case.version == version
    execution = execute(actor, case.pk, plan.pk, key, version, purposes, REASON, True)
    event = RecoveryOutbox.objects.get(execution=execution)
    payload = unseal(event.encrypted_event)
    assert payload["scope"] == "account"
    assert payload["subject"] == str(subject.pk)
    assert payload["purposes"] == sorted(purposes)
    assert len(payload["references"]["resources"]["tokens"]) == tokens
    subject.refresh_from_db()
    assert payload["references"]["account"]["minimum_session_version"] == subject.session_version
    assert payload["references"]["account"]["minimum_mfa_version"] == subject.mfa_version
    assert "reason" not in payload and "email" not in payload
    assert event.exported_at is None
    assert execute(actor, case.pk, plan.pk, key, version, purposes, REASON, True).pk == execution.pk
    assert RecoveryOutbox.objects.count() == 1

    from copy import copy as clone

    from django.db import transaction

    from apps.safety.account_erasure_inventory import source

    def snapshot(scope):
        with transaction.atomic():
            return source(scope)

    current = {row["model"]: row for row in snapshot(case)["entries"]}
    assert current["safety.RecoveryOutbox"]["count"] == 0
    other = clone(case)
    other.pk = uuid4()
    previous = snapshot(other)
    row = next(row for row in previous["entries"] if row["model"] == "safety.RecoveryOutbox")
    assert row["count"] == 1
    assert event.encrypted_event not in str(previous)
    event.encrypted_event = "Synthetic damaged encrypted event"
    event.save(update_fields=["encrypted_event"])
    changed = snapshot(other)
    changed_row = next(row for row in changed["entries"] if row["model"] == "safety.RecoveryOutbox")
    assert row["state_digest"] != changed_row["state_digest"]
    assert event.encrypted_event not in str(changed)


def test_profile_receipt_is_scoped_and_opaque(request, settings, monkeypatch):
    from django.db import transaction
    from test_erasure_execution import payload, plan_fixture

    from apps.core.models import Person
    from apps.safety.erasure_inventory import source_manifest

    case, actor, staff, client, receipt, person, plan, stored, image, outsider = plan_fixture(
        request, settings, monkeypatch
    )
    execution = execute(actor, case.pk, plan.pk, **payload(case))
    event = RecoveryOutbox.objects.get(execution=execution)
    body = unseal(event.encrypted_event)
    assert body["scope"] == "person" and body["subject"] == str(person.pk)
    assert body["references"]["resources"]["exports"] == [str(stored.pk)]
    assert len(body["references"]["resources"]["favorites"]) == 1
    from apps.listings.models import Favorite

    assert Favorite.objects.filter(user=outsider, listing=person.listing).exists()

    def snapshot(target):
        with transaction.atomic():
            locked = Person.objects.select_for_update().get(pk=target.pk)
            return source_manifest(locked)

    current = snapshot(person)
    row = next(row for row in current["entries"] if row["model"] == "safety.RecoveryOutbox")
    assert row["count"] == 1 and row["purpose"] == "dependent_evidence"
    assert event.encrypted_event not in str(current)
    other = Person.objects.exclude(pk=person.pk).first()
    assert other is not None
    other_manifest = snapshot(other)
    other_row = next(
        row for row in other_manifest["entries"] if row["model"] == "safety.RecoveryOutbox"
    )
    assert other_row["count"] == 0
    event.encrypted_event = "Synthetic invalid opaque ciphertext"
    event.save(update_fields=["encrypted_event"])
    changed = snapshot(person)
    changed_row = next(row for row in changed["entries"] if row["model"] == "safety.RecoveryOutbox")
    assert changed_row["state_digest"] != row["state_digest"]
    assert event.encrypted_event not in str(changed)
    assert snapshot(other) == other_manifest


def test_media_receipt_keeps_recovery_paths_after_physical_deletion(request, settings, monkeypatch):
    from test_erasure_execution import payload
    from test_media_erasure import setup

    from apps.mediafiles.erasure import erase_due_media
    from apps.mediafiles.models import MediaErasure

    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    paths = {"original": blob.original.name, "derivative": blob.derivative.name}
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    event = RecoveryOutbox.objects.get(execution=execution)
    refs = unseal(event.encrypted_event)["references"]
    job = MediaErasure.objects.get(execution=execution, blob=blob)
    item = next(item for item in refs["media_jobs"] if item["blob"] == str(blob.pk))
    assert item == {"job": str(job.pk), "blob": str(blob.pk), "paths": paths}
    assert refs["resources"]["media_operation"] == "erase_exclusive"
    assert all(not photo["shared"] for photo in refs["resources"]["photos"])
    assert paths["original"] not in event.encrypted_event
    assert erase_due_media() >= 1
    job.refresh_from_db()
    assert job.status == "completed" and not job.encrypted_paths
    event.refresh_from_db()
    assert unseal(event.encrypted_event)["references"]["media_jobs"] == refs["media_jobs"]
    assert not blob.original.storage.exists(paths["original"])
    assert not blob.derivative.storage.exists(paths["derivative"])
