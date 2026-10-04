"""Scoped reuse evidence invalidates an erasure plan before any deletion."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from test_erasure_execution import payload
from test_photo_reuse_races import setup_review
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety import models
from apps.safety.crypto import seal, unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import canonical, prepare, source_manifest
from apps.safety.erasure_plans import record
from apps.safety.photo_reintroduction_review import decide, inspect
from apps.safety.rights import fingerprint

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("changed", ["version", "reason", "read"])
def test_reuse_evidence_changes_invalidate_erasure_before_mutation(
    request, settings, monkeypatch, changed
):
    case, actor, person, old_plan, shared, peer, _, candidate, read = setup_review(
        request, settings, monkeypatch
    )
    private_reason = "Independent synthetic current image permission evidence assessed"
    decision = decide(
        actor, candidate.pk, read.pk, uuid4(), 1, "authorize", private_reason, "private-reuse-ref"
    )
    inventory = prepare(
        actor,
        case.pk,
        uuid4(),
        case.version,
        "Review reuse decision dependencies before scoped erasure execution",
    )
    plan = record(
        actor,
        case.pk,
        inventory.pk,
        uuid4(),
        case.version,
        unseal(old_plan.encrypted_decisions)["decisions"],
    )
    manifest = source_manifest(person)
    serialized = canonical(manifest)
    assert private_reason not in serialized and decision.encrypted_reason not in serialized
    peer_person = peer.revision.listing.person
    peer_person.alias = "Changed unrelated synthetic peer alias"
    peer_person.save(update_fields=["alias"])
    assert fingerprint(canonical(source_manifest(person))) == inventory.source_digest
    candidate.refresh_from_db()
    if changed == "version":
        # Isolate mutable version from new decision rows, which also invalidate the plan.
        models.RightsPhotoReintroduction.objects.filter(pk=candidate.pk).update(
            review_version=candidate.review_version + 1
        )
    elif changed == "reason":
        models.RightsPhotoReintroductionDecision.objects.filter(pk=decision.pk).update(
            encrypted_reason=seal({"reason": private_reason + " amended", "reference": "new-ref"})
        )
    else:
        inspect(
            actor,
            candidate.pk,
            uuid4(),
            candidate.review_version,
            "Inspect current reuse evidence after preparing the erasure plan",
        )
    before_status = person.listing.status
    assert fingerprint(canonical(source_manifest(person))) != inventory.source_digest
    with pytest.raises(ValidationError, match="Resources changed"):
        execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    assert not models.ErasureExecution.objects.filter(plan=plan).exists()
    person.listing.refresh_from_db()
    assert person.listing.status == before_status
    shared.refresh_from_db()
    assert shared.status == "ready" and shared.derivative.storage.exists(shared.derivative.name)
    assert candidate.photo.removed_at is None
