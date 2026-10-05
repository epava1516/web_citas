"""Purpose preparation must not mutate processing or imply completed rights."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.erasure_inventory import source_manifest
from apps.safety.models import ProcessingPurposePlan
from apps.safety.processing_plans import prepare

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Prepare independent selected-purpose treatment decisions"


@transaction.atomic
def decisions(case):
    manifest = source_manifest(None, case)
    return [
        dict(
            purpose=purpose,
            operation="review",
            basis=REASON,
            scope=REASON,
            reason=REASON,
            review_on=(timezone.localdate() + timedelta(days=7)).isoformat(),
        )
        for purpose in sorted({row["purpose"] for row in manifest["entries"]})
    ]


@pytest.mark.parametrize("kind", ["restriction", "object"])
def test_own_account_preparation_is_scoped_idempotent_and_has_no_processing_effect(
    request, settings, monkeypatch, kind
):
    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch, kind)
    original = (
        case.version,
        case.status,
        case.initial_due_at,
        subject.email,
        subject.is_active,
        subject.session_version,
    )
    values = decisions(case)
    key = uuid4()
    plan = prepare(actor, case.pk, key, case.version, REASON, values)
    assert prepare(actor, case.pk, key, case.version, REASON, values).pk == plan.pk
    body = unseal(plan.encrypted_plan)
    assert body["kind"] == kind and body["enforced"] is False and body["partial"] is True
    assert plan.account_subject_id == subject.pk and plan.person_id is None
    assert ProcessingPurposePlan.objects.count() == 1
    with pytest.raises(ValidationError):
        prepare(actor, case.pk, key, case.version, REASON, values[:-1])
    case.refresh_from_db()
    subject.refresh_from_db()
    assert (
        case.version,
        case.status,
        case.initial_due_at,
        subject.email,
        subject.is_active,
        subject.session_version,
    ) == original


def test_unchecked_or_wrong_scope_cannot_create_plan(request, settings, monkeypatch):
    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch, "restriction")
    values = decisions(case)
    case.scope_status = "unverified"
    case.save(update_fields=["scope_status"])
    with pytest.raises(ValidationError):
        prepare(actor, case.pk, uuid4(), case.version, REASON, values)
    with pytest.raises(PermissionDenied):
        prepare(subject, case.pk, uuid4(), case.version, REASON, values)
    assert not ProcessingPurposePlan.objects.exists()


def test_http_preview_prepare_reload_and_source_drift(request, settings, monkeypatch):
    import json

    from django.urls import reverse

    from apps.listings.models import Favorite, Listing
    from apps.safety.erasure_inventory import canonical
    from apps.safety.processing_plans import preview
    from apps.safety.rights import fingerprint

    case, actor, staff, subject, _, _ = prepared_account(
        request, settings, monkeypatch, "restriction"
    )
    path = reverse("processing_prepare", kwargs={"case_id": case.pk})
    assert (
        staff.get(path).status_code == 200 and "core.User" not in staff.get(path).content.decode()
    )
    key = uuid4()
    response = staff.post(
        path, {"key": key, "version": case.version, "operation": "preview", "reason": REASON}
    )
    assert response.status_code == 200
    manifest = response.context["manifest"]
    assert preview(actor, case.pk, key, case.version, REASON) == manifest
    payload = {
        "key": uuid4(),
        "version": case.version,
        "operation": "prepare",
        "reason": REASON,
        "source_digest": fingerprint(canonical(manifest)),
        "decisions": json.dumps(decisions(case)),
    }
    assert staff.post(path, payload).status_code == 200
    assert staff.post(path, payload).status_code == 200
    assert ProcessingPurposePlan.objects.count() == 1
    assert (
        "core.User" not in staff.get(path).content.decode()
        and REASON not in staff.get(path).content.decode()
    )
    with transaction.atomic():
        assert fingerprint(canonical(source_manifest(None, case))) == payload["source_digest"]
    Favorite.objects.create(user=subject, listing=Listing.objects.first())
    payload["key"] = uuid4()
    assert staff.post(path, payload).status_code == 409
    assert ProcessingPurposePlan.objects.count() == 1


def test_malformed_operation_is_controlled_without_persisting_plan(request, settings, monkeypatch):
    case, actor, _, _, _, _ = prepared_account(request, settings, monkeypatch, "object")
    values = decisions(case)
    values[0]["operation"] = []
    with pytest.raises(ValidationError):
        prepare(actor, case.pk, uuid4(), case.version, REASON, values)
    assert not ProcessingPurposePlan.objects.exists()
