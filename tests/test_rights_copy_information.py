from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared

from apps.safety.crypto import unseal
from apps.safety.models import RightsCopyInformation
from apps.safety.rights_copy_information import FIELDS, checked_information, record
from apps.safety.tasks import purge_expired_copy_information

pytestmark = pytest.mark.django_db(transaction=True)


def draft():
    return {
        "access": {
            field: {"status": "pending", "text": "", "source": "unknown"} for field in FIELDS
        },
        "portability": None,
    }


def test_information_drafts_are_encrypted_versioned_replayable_and_purged(request, settings):
    case, actor, _, _, _, person = prepared(request, settings)
    value = draft()
    value["access"]["purposes"] = {
        "status": "reviewed",
        "text": "Synthetic reviewed purpose",
        "source": "reviewer",
    }
    key = uuid4()
    reason = "Record partial information without closing request"
    row = record(actor, case.pk, case.version, key, 0, "synthetic-policy-v1", reason, value)
    from apps.safety.erasure_inventory import source_manifest

    manifest = source_manifest(person)
    entry = next(
        item for item in manifest["entries"] if item["model"] == "safety.RightsCopyInformation"
    )
    assert entry["count"] == 1 and entry["purpose"] == "dependent_evidence"
    assert row.encrypted_information not in str(manifest)
    assert "Synthetic reviewed purpose" not in str(manifest)
    assert unseal(row.encrypted_information) == value
    assert "Synthetic reviewed purpose" not in row.encrypted_information
    assert (
        record(actor, case.pk, case.version, key, 0, "synthetic-policy-v1", reason, value).pk
        == row.pk
    )
    with pytest.raises(ValidationError, match="version changed"):
        record(actor, case.pk, case.version, uuid4(), 0, "synthetic-policy-v1", reason, value)
    original = case.version
    case.refresh_from_db()
    assert case.version == original and case.status == "reviewing"
    RightsCopyInformation.objects.filter(pk=row.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert purge_expired_copy_information() == 1 and purge_expired_copy_information() == 0
    row.refresh_from_db()
    assert row.encrypted_information == "" and row.purged_at
    with pytest.raises(ValidationError, match="unavailable"):
        record(actor, case.pk, case.version, key, 0, "synthetic-policy-v1", reason, value)


def test_information_schema_rejects_unknown_assertions_and_keeps_portability_separate():
    value = draft()
    value["access"]["retention"]["text"] = "Unverified retention claim"
    with pytest.raises(ValidationError):
        checked_information("access", value)
    value = draft()
    value["portability"] = {"status": "pending", "reason": ""}
    with pytest.raises(ValidationError):
        checked_information("access", value)
    assert checked_information("portability", value) == value
    value["portability"]["status"] = "eligible"
    with pytest.raises(ValidationError):
        checked_information("portability", value)


def test_information_provenance_with_invalid_type_is_controlled():
    value = draft()
    value["access"]["purposes"] = {"status": "reviewed", "text": "Synthetic text", "source": []}
    with pytest.raises(ValidationError):
        checked_information("access", value)


def test_guided_http_information_save_audited_read_and_clean_get(request, settings, monkeypatch):
    from django.urls import reverse

    from apps.safety import rights_copy_information
    from apps.safety.models import RightsAction

    case, actor, staff, _, _, _ = prepared(request, settings)
    path = reverse("rights_copy_information_prepare", kwargs={"case_id": case.pk})
    first = staff.get(path)
    assert first.status_code == 200 and len(first.context["fields"]) == 10
    payload = {
        "operation": "record",
        "key": str(uuid4()),
        "version": case.version,
        "information_version": 0,
        "policy_version": "synthetic-v1",
        "reason": "Record guided partial access information",
        "information-TOTAL_FORMS": 10,
        "information-INITIAL_FORMS": 10,
        "information-MIN_NUM_FORMS": 10,
        "information-MAX_NUM_FORMS": 10,
    }
    for index, name in enumerate(FIELDS):
        payload.update(
            {
                f"information-{index}-field": name,
                f"information-{index}-status": "pending",
                f"information-{index}-source": "unknown",
                f"information-{index}-text": "",
            }
        )
    index = FIELDS.index("purposes")
    payload.update(
        {
            f"information-{index}-status": "reviewed",
            f"information-{index}-source": "reviewer",
            f"information-{index}-text": "PRIVATE_GUIDED_INFORMATION",
        }
    )
    payload["source_digest"] = first.context["form"].initial["source_digest"]
    response = staff.post(path, payload)
    assert response.status_code == 200
    saved = response.context["saved"]
    assert b"PRIVATE_GUIDED_INFORMATION" not in response.content
    assert staff.post(path, payload).status_code == 200
    assert RightsCopyInformation.objects.count() == 1
    original = rights_copy_information.unseal

    def audited(value):
        assert RightsAction.objects.filter(operation="copy_info_read").exists()
        return original(value)

    monkeypatch.setattr(rights_copy_information, "unseal", audited)
    reading = {
        "operation": "inspect",
        "key": str(uuid4()),
        "version": case.version,
        "information_id": saved.pk,
        "purpose": "Inspect saved guided information",
    }
    recovered = staff.post(path, reading)
    assert recovered.status_code == 200 and b"PRIVATE_GUIDED_INFORMATION" in recovered.content
    assert "no-store" in recovered["Cache-Control"]
    assert staff.post(path, reading).status_code == 200
    assert RightsAction.objects.filter(operation="copy_info_read").count() == 1
    assert b"PRIVATE_GUIDED_INFORMATION" not in staff.get(path).content
    RightsCopyInformation.objects.filter(pk=saved.pk).update(encrypted_information="damaged")
    assert staff.post(path, reading | {"key": str(uuid4())}).status_code == 409
    assert RightsAction.objects.filter(operation="copy_info_read").count() == 1
    actor.user_permissions.clear()
    assert staff.post(path, reading).status_code == 403


@pytest.mark.parametrize("kind", ["access", "portability"])
def test_own_account_guided_information_preserves_separate_pending_portability(
    request, settings, monkeypatch, kind
):
    from django.urls import reverse
    from test_account_copy_races import prepared_account

    case, _, staff, _, _, _ = prepared_account(request, settings, monkeypatch, kind=kind)
    path = reverse("rights_copy_information_prepare", kwargs={"case_id": case.pk})
    payload = {
        "operation": "record",
        "key": str(uuid4()),
        "version": case.version,
        "information_version": 0,
        "policy_version": "synthetic-account-policy",
        "reason": "Record own account information with pending fields",
        "information-TOTAL_FORMS": 10,
        "information-INITIAL_FORMS": 10,
        "information-MIN_NUM_FORMS": 10,
        "information-MAX_NUM_FORMS": 10,
    }
    for index, name in enumerate(FIELDS):
        payload.update(
            {
                f"information-{index}-field": name,
                f"information-{index}-status": "pending",
                f"information-{index}-source": "unknown",
                f"information-{index}-text": "",
            }
        )
    payload["source_digest"] = staff.get(path).context["form"].initial["source_digest"]
    duplicate = payload | {"information-1-field": FIELDS[0]}
    assert staff.post(path, duplicate).status_code == 409
    assert not RightsCopyInformation.objects.exists()
    assert staff.post(path, payload | {"information-TOTAL_FORMS": 11}).status_code == 400
    assert not RightsCopyInformation.objects.exists()
    response = staff.post(path, payload)
    assert response.status_code == 200
    saved = response.context["saved"]
    information = unseal(saved.encrypted_information)
    assert information["portability"] == (
        {"status": "pending", "reason": ""} if kind == "portability" else None
    )
    assert all(item["status"] == "pending" for item in information["access"].values())
    before = case.version
    case.refresh_from_db()
    assert case.version == before and case.status == "reviewing"


def test_account_inventory_excludes_current_information_and_tracks_prior_subject_evidence(
    request, settings, monkeypatch
):
    from copy import copy

    from django.db import transaction
    from test_account_copy_races import prepared_account

    from apps.core.models import User
    from apps.safety.account_erasure_inventory import source
    from apps.safety.models import RightsRequest

    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
    row = record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        0,
        "synthetic-policy-v1",
        "Record own account information for inventory",
        draft(),
    )

    # Extra cases are inventory-scope fixtures, not accepted rights workflows.
    previous = copy(case)
    previous.pk, previous.submission_key = uuid4(), uuid4()
    previous._state.adding = True
    previous.save(force_insert=True)
    foreign = copy(previous)
    foreign.pk, foreign.submission_key = uuid4(), uuid4()
    foreign.account_subject = User.objects.exclude(pk=subject.pk).first()
    foreign._state.adding = True
    foreign.save(force_insert=True)

    def snapshot(case_id):
        with transaction.atomic():
            current = RightsRequest.objects.get(pk=case_id)
            manifest = source(current)
            entry = next(
                item
                for item in manifest["entries"]
                if item["model"] == "safety.RightsCopyInformation"
            )
            assert row.encrypted_information not in str(manifest)
            return entry

    assert snapshot(case.pk)["count"] == 0
    visible = snapshot(previous.pk)
    excluded = snapshot(foreign.pk)
    assert visible["count"] == 1 and excluded["count"] == 0
    RightsCopyInformation.objects.filter(pk=row.pk).update(
        encrypted_information="opaque damaged decision"
    )
    changed = snapshot(previous.pk)
    assert changed["state_digest"] != visible["state_digest"]
    assert snapshot(foreign.pk) == excluded
    assert snapshot(case.pk)["count"] == 0
