from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared

from apps.safety.crypto import unseal
from apps.safety.models import RightsCopyPageReview, RightsExportPreview
from apps.safety.rights_copy_inspection import inspect_page
from apps.safety.rights_copy_page_review import record
from apps.safety.tasks import purge_expired_copy_page_reviews

pytestmark = pytest.mark.django_db(transaction=True)


def test_encrypted_page_decisions_version_replay_and_purge_do_not_approve_copy(request, settings):
    case, actor, _, _, _, person = prepared(request, settings)
    read = inspect_page(
        actor, case.pk, case.version, uuid4(), "Inspect current source page before review"
    )
    entries = deepcopy(read["entries"])
    entries[0]["description"] = "Reviewed text without third party information"
    key = uuid4()
    reason = "Record scoped reviewed page without approving entire copy"
    row = record(actor, case.pk, case.version, key, read["read_id"], 0, reason, entries)
    assert row.version == 1 and row.proof.request_id == case.pk
    assert entries[0]["description"] not in row.encrypted_entries
    assert unseal(row.encrypted_entries) == entries
    assert (
        record(actor, case.pk, case.version, key, read["read_id"], 0, reason, entries).pk == row.pk
    )
    with pytest.raises(ValidationError, match="version changed"):
        record(actor, case.pk, case.version, uuid4(), read["read_id"], 0, reason, entries)
    changed = deepcopy(entries)
    changed[0]["description"] = "Second reviewed text"
    next_row = record(actor, case.pk, case.version, uuid4(), read["read_id"], 1, reason, changed)
    assert next_row.version == 2 and unseal(row.encrypted_entries) == entries
    assert RightsCopyPageReview.objects.count() == 2
    assert not RightsExportPreview.objects.filter(request=case).exists()
    before_version = case.version
    case.refresh_from_db()
    assert case.version == before_version and case.status == "reviewing"
    assert (
        person.listing.revisions.get(pk=entries[0]["revision"]).description
        != changed[0]["description"]
    )
    RightsCopyPageReview.objects.filter(pk=row.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert purge_expired_copy_page_reviews() == 1 and purge_expired_copy_page_reviews() == 0
    row.refresh_from_db()
    assert row.encrypted_entries == "" and row.purged_at and row.version == 1
    assert RightsCopyPageReview.objects.get(pk=next_row.pk).encrypted_entries
    with pytest.raises(ValidationError, match="unavailable"):
        record(actor, case.pk, case.version, key, read["read_id"], 0, reason, entries)


def test_stale_page_source_or_injected_identity_cannot_be_saved(request, settings):
    case, actor, _, _, _, person = prepared(request, settings)
    read = inspect_page(
        actor, case.pk, case.version, uuid4(), "Inspect current page before source changes"
    )
    entries = deepcopy(read["entries"])
    entries[0]["revision"] = str(uuid4())
    with pytest.raises(ValidationError):
        record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            read["read_id"],
            0,
            "Reject foreign page revision injection",
            entries,
        )
    person.listing.revisions.filter(pk=read["entries"][0]["revision"]).update(
        title="Changed source"
    )
    with pytest.raises(ValidationError, match="source changed"):
        record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            read["read_id"],
            0,
            "Reject obsolete source page decisions",
            read["entries"],
        )
    assert not RightsCopyPageReview.objects.exists()


@pytest.mark.parametrize("replay", [False, True])
def test_permission_revoked_during_page_source_read_rejects_new_and_repeated_save(
    request, settings, monkeypatch, replay
):
    from django.core.exceptions import PermissionDenied

    from apps.safety import rights_copy_page_review
    from apps.safety.models import RightsAction

    case, actor, _, _, _, _ = prepared(request, settings)
    read = inspect_page(
        actor, case.pk, case.version, uuid4(), "Inspect current page before changed authority"
    )
    key = uuid4()
    reason = "Save reviewed page before changed authority"
    if replay:
        record(actor, case.pk, case.version, key, read["read_id"], 0, reason, read["entries"])
    before = (RightsCopyPageReview.objects.count(), RightsAction.objects.count())
    original = rights_copy_page_review.source_copy

    def revoke(*args):
        source = original(*args)
        actor.user_permissions.clear()
        return source

    monkeypatch.setattr(rights_copy_page_review, "source_copy", revoke)
    with pytest.raises(PermissionDenied):
        record(actor, case.pk, case.version, key, read["read_id"], 0, reason, read["entries"])
    assert (RightsCopyPageReview.objects.count(), RightsAction.objects.count()) == before


def test_erasure_inventory_tracks_page_content_and_purge_without_disclosing_it(request, settings):
    from apps.core.models import Person
    from apps.safety.erasure_inventory import source_manifest

    case, actor, _, _, _, person = prepared(request, settings)
    other = Person.objects.exclude(pk=person.pk).first()
    assert other is not None

    def entry(subject):
        return next(
            item
            for item in source_manifest(subject)["entries"]
            if item["model"] == "safety.RightsCopyPageReview"
        )

    before = entry(person)
    foreign_before = entry(other)
    read = inspect_page(
        actor, case.pk, case.version, uuid4(), "Inspect page for scoped erasure evidence"
    )
    row = record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        read["read_id"],
        0,
        "Save temporary page decisions for scoped inventory",
        read["entries"],
    )
    recorded = entry(person)
    assert recorded["count"] == before["count"] + 1
    assert recorded["state_digest"] != before["state_digest"]
    assert recorded["purpose"] == "dependent_evidence"
    assert row.encrypted_entries not in str(source_manifest(person))
    assert read["entries"][0]["description"] not in str(source_manifest(person))
    assert entry(other) == foreign_before

    # Damaged ciphertext must still invalidate evidence without inventory decrypting it.
    damaged = "Opaque damaged page content for inventory integrity"
    RightsCopyPageReview.objects.filter(pk=row.pk).update(encrypted_entries=damaged)
    changed = entry(person)
    assert changed["state_digest"] != recorded["state_digest"]
    assert damaged not in str(source_manifest(person))
    RightsCopyPageReview.objects.filter(pk=row.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert purge_expired_copy_page_reviews() == 1
    purged = entry(person)
    assert purged["count"] == recorded["count"]
    assert purged["state_digest"] != changed["state_digest"]
    assert entry(other) == foreign_before


def test_http_page_save_is_private_replayable_and_get_does_not_restore_content(request, settings):
    import json

    from django.urls import reverse

    case, actor, staff, _, _, _ = prepared(request, settings)
    path = reverse("rights_export_prepare", kwargs={"case_id": case.pk})
    response = staff.post(
        path,
        {
            "key": uuid4(),
            "version": case.version,
            "operation": "inspect_page",
            "purpose": "Review current page through HTTP",
        },
    )
    assert response.status_code == 200
    read = response.context["page_data"]
    assert response.context["page_review_form"] is not None
    entries = deepcopy(read["entries"])
    entries[0]["description"] = "PRIVATE_HTTP_REVIEWED_CONTENT"
    data = {
        "key": str(uuid4()),
        "version": case.version,
        "operation": "save_page",
        "read_id": read["read_id"],
        "page_version": read["page_version"],
        "reason": "Record private HTTP page decisions",
        "entries": json.dumps(entries),
    }
    saved = staff.post(path, data)
    assert saved.status_code == 200 and saved.context["saved_page"].version == 1
    assert "no-store" in saved["Cache-Control"]
    assert b"PRIVATE_HTTP_REVIEWED_CONTENT" not in saved.content
    assert staff.post(path, data).status_code == 200
    assert RightsCopyPageReview.objects.count() == 1
    get = staff.get(path)
    assert get.status_code == 200 and b"PRIVATE_HTTP_REVIEWED_CONTENT" not in get.content
    assert get.context["saved_page"] is None
    access = {
        "key": str(uuid4()),
        "version": case.version,
        "operation": "inspect_saved_page",
        "review_id": saved.context["saved_page"].pk,
        "purpose": "Recover private HTTP page decisions",
    }
    recovered = staff.post(path, access)
    assert recovered.status_code == 200
    assert b"PRIVATE_HTTP_REVIEWED_CONTENT" in recovered.content
    assert "no-store" in recovered["Cache-Control"]
    assert staff.post(path, access).status_code == 200
    assert b"PRIVATE_HTTP_REVIEWED_CONTENT" not in staff.get(path).content
    actor.user_permissions.clear()
    assert staff.post(path, access).status_code == 403
    assert staff.post(path, data).status_code == 403
    assert RightsCopyPageReview.objects.count() == 1


def test_saved_page_read_audits_before_decryption_and_rejects_damaged_or_stale_evidence(
    request, settings, monkeypatch
):
    from apps.safety import rights_copy_page_review
    from apps.safety.models import RightsAction

    case, actor, _, _, _, person = prepared(request, settings)
    read = inspect_page(
        actor, case.pk, case.version, uuid4(), "Inspect page before persistent review"
    )
    row = record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        read["read_id"],
        0,
        "Record page before audited recovery",
        read["entries"],
    )
    original = rights_copy_page_review.unseal

    def audited(value):
        assert RightsAction.objects.filter(operation="copy_review_read").exists()
        return original(value)

    monkeypatch.setattr(rights_copy_page_review, "unseal", audited)
    key = uuid4()
    purpose = "Recover scoped saved page decisions"
    result = rights_copy_page_review.inspect_saved(
        actor, case.pk, case.version, key, row.pk, purpose
    )
    assert result["entries"] == read["entries"]
    assert (
        rights_copy_page_review.inspect_saved(actor, case.pk, case.version, key, row.pk, purpose)
        == result
    )
    assert RightsAction.objects.filter(operation="copy_review_read").count() == 1
    RightsCopyPageReview.objects.filter(pk=row.pk).update(encrypted_entries="damaged ciphertext")
    with pytest.raises(ValidationError, match="unavailable"):
        rights_copy_page_review.inspect_saved(
            actor, case.pk, case.version, uuid4(), row.pk, purpose
        )
    assert RightsAction.objects.filter(operation="copy_review_read").count() == 1
    person.listing.revisions.filter(pk=read["entries"][0]["revision"]).update(
        title="Changed source"
    )
    with pytest.raises(ValidationError, match="source changed"):
        rights_copy_page_review.inspect_saved(
            actor, case.pk, case.version, uuid4(), row.pk, purpose
        )
    assert RightsAction.objects.filter(operation="copy_review_read").count() == 1


@pytest.mark.parametrize("account_only", [False, True])
def test_header_review_redacts_own_identity_and_preserves_scope(
    request, settings, monkeypatch, account_only
):
    from test_account_copy_races import prepared_account

    from apps.safety.rights_copy_page_review import inspect_saved

    if account_only:
        case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, _, _, _, person = prepared(request, settings)
        subject = person.subject
    section = "subject_account"
    read = inspect_page(
        actor, case.pk, case.version, uuid4(), "Inspect subject account header", section=section
    )
    assert len(read["entries"]) == 1
    assert read["entries"][0]["email"] == subject.email
    entries = deepcopy(read["entries"])
    entries[0]["email"] = ""
    row = record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        read["read_id"],
        0,
        "Redact subject email in private copy",
        entries,
    )
    recovered = inspect_saved(
        actor, case.pk, case.version, uuid4(), row.pk, "Recover reviewed account identity"
    )
    assert recovered["entries"][0]["email"] == ""
    subject.refresh_from_db()
    assert subject.email == read["entries"][0]["email"]
    injected = deepcopy(entries)
    injected[0]["email"] = "other-person@example.invalid"
    with pytest.raises(ValidationError):
        record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            read["read_id"],
            1,
            "Reject foreign identity in header",
            injected,
        )
    profile = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid4(),
        "Inspect profile header separately",
        section="profile",
    )
    if account_only:
        assert profile["entries"] == []
        with pytest.raises(ValidationError):
            record(
                actor,
                case.pk,
                case.version,
                uuid4(),
                profile["read_id"],
                0,
                "Reject invented managed profile header",
                [{"alias": "Injected"}],
            )
    else:
        header = deepcopy(profile["entries"])
        header[0]["alias"] = "Reviewed private alias"
        saved = record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            profile["read_id"],
            0,
            "Review private profile alias",
            header,
        )
        assert unseal(saved.encrypted_entries) == header
    assert not RightsExportPreview.objects.filter(request=case).exists()


def test_account_inventory_excludes_current_review_and_tracks_prior_subject_evidence(
    request, settings, monkeypatch
):
    from copy import copy

    from django.db import transaction
    from test_account_copy_races import prepared_account

    from apps.core.models import User
    from apps.safety.account_erasure_inventory import source
    from apps.safety.models import RightsRequest

    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
    read = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid4(),
        "Inspect own account before inventory",
        section="subject_account",
    )
    row = record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        read["read_id"],
        0,
        "Record own account page for inventory",
        read["entries"],
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
                if item["model"] == "safety.RightsCopyPageReview"
            )
            assert row.encrypted_entries not in str(manifest)
            return entry

    assert snapshot(case.pk)["count"] == 0
    visible = snapshot(previous.pk)
    excluded = snapshot(foreign.pk)
    assert visible["count"] == 1 and excluded["count"] == 0
    RightsCopyPageReview.objects.filter(pk=row.pk).update(
        encrypted_entries="opaque damaged decision"
    )
    changed = snapshot(previous.pk)
    assert changed["state_digest"] != visible["state_digest"]
    assert snapshot(foreign.pk) == excluded
    assert snapshot(case.pk)["count"] == 0
