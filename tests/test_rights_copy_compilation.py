"""Compilation requires all latest current decisions without silently approving missing pages."""

from copy import deepcopy
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared

from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsCopyPageReview, RightsExportPreview
from apps.safety.rights_copy_inspection import SECTIONS, inspect_page
from apps.safety.rights_copy_page_review import compile_pages, record
from apps.safety.rights_exports import generate

pytestmark = pytest.mark.django_db(transaction=True)


def review_all(case, actor):
    saved = []
    for section in SECTIONS:
        page, cursor = 1, ""
        while True:
            read = inspect_page(
                actor,
                case.pk,
                case.version,
                uuid4(),
                "Review source before complete page compilation",
                section,
                page,
                cursor,
            )
            entries = deepcopy(read["entries"])
            if section == "subject_account" and entries:
                entries[0]["email"] = ""
            if section == "revisions":
                for revision in entries:
                    revision["description"] = "Reviewed compilation text"
                    for image in revision["images"]:
                        image["content_included"] = False
                        image["exclusion_code"] = "third_party"
            saved.append(
                record(
                    actor,
                    case.pk,
                    case.version,
                    uuid4(),
                    read["read_id"],
                    read["page_version"],
                    "Record decisions before complete page compilation",
                    entries,
                )
            )
            if not read["has_next"]:
                break
            page, cursor = page + 1, read["cursor"]
    return saved


@pytest.mark.parametrize("account_only", [False, True])
def test_compile_requires_every_section_preserves_redactions_and_generates_private_copy(
    request, settings, monkeypatch, account_only
):
    if account_only:
        case, actor, _, _, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, _, _, _, _ = prepared(request, settings)
    reason = "Compile every reviewed page without closing the request"
    with pytest.raises(ValidationError, match="every current"):
        compile_pages(actor, case.pk, case.version, uuid4(), reason)
    assert not RightsExportPreview.objects.filter(request=case).exists()
    rows = review_all(case, actor)
    key = uuid4()
    result = compile_pages(actor, case.pk, case.version, key, reason)
    assert result["partial"] and result["simulation"] and result["pending_review"]
    assert result["subject_account"]["email"] == ""
    assert (result["profile"] is None) == account_only
    assert all(row["description"] == "Reviewed compilation text" for row in result["revisions"])
    assert compile_pages(actor, case.pk, case.version, key, reason) == result
    assert RightsExportPreview.objects.filter(request=case).count() == 1
    assert RightsAction.objects.filter(operation="copy_pages_compile").count() == 1
    assert RightsAction.objects.filter(operation="copy_review_read").count() == len(rows)
    export = generate(actor, case.pk, uuid4(), case.version, reason, result)
    delivered = unseal(export.encrypted_payload)
    assert delivered["subject_account"]["email"] == ""
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_expired_latest_decision_does_not_fall_back_or_leave_partial_compilation_audit(
    request, settings
):
    from datetime import timedelta

    from django.utils import timezone

    case, actor, _, _, _, _ = prepared(request, settings)
    rows = review_all(case, actor)
    chosen = rows[-1]
    RightsCopyPageReview.objects.filter(pk=chosen.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    with pytest.raises(ValidationError, match="unavailable"):
        compile_pages(
            actor, case.pk, case.version, uuid4(), "Reject expired page during compilation"
        )
    assert not RightsExportPreview.objects.filter(request=case).exists()
    assert not RightsAction.objects.filter(
        operation__in=["copy_pages_compile", "copy_review_read"]
    ).exists()


def test_http_compilation_of_multiple_revision_pages_uses_latest_decisions(request, settings):
    import json

    from django.urls import reverse

    from apps.listings.models import Revision

    case, actor, staff, _, _, person = prepared(request, settings)
    Revision.objects.bulk_create(
        [
            Revision(
                listing=person.listing,
                manager_version=person.manager_version,
                title=f"Synthetic compilation history {n}",
            )
            for n in range(24)
        ]
    )
    rows = review_all(case, actor)
    revision_pages = [row for row in rows if row.section == "revisions"]
    assert [row.page for row in revision_pages] == [1, 2, 3]
    read = inspect_page(
        actor, case.pk, case.version, uuid4(), "Inspect first page for final revision"
    )
    entries = deepcopy(read["entries"])
    entries[0]["description"] = "Latest first-page reviewed decision"
    for revision in entries:
        for image in revision["images"]:
            image["content_included"] = False
            image["exclusion_code"] = "third_party"
    latest = record(
        actor,
        case.pk,
        case.version,
        uuid4(),
        read["read_id"],
        1,
        "Replace first-page decision before compilation",
        entries,
    )
    assert latest.version == 2
    path = reverse("rights_export_prepare", kwargs={"case_id": case.pk})
    response = staff.post(
        path,
        {
            "key": uuid4(),
            "version": case.version,
            "operation": "compile_pages",
            "reason": "Compile latest page decisions through HTTP",
        },
    )
    assert response.status_code == 200
    compiled = response.context["source"]
    assert len(compiled["revisions"]) == 25
    assert len({row["revision"] for row in compiled["revisions"]}) == 25
    assert compiled["revisions"][0]["description"] == entries[0]["description"]
    assert "no-store" in response["Cache-Control"]
    assert b"Latest first-page reviewed decision" not in staff.get(path).content
    result = staff.post(
        path,
        {
            "key": uuid4(),
            "version": case.version,
            "operation": "generate",
            "reason": "Generate copy compiled from current decisions",
            "copy": json.dumps(compiled),
        },
    )
    assert result.status_code == 302
    case.refresh_from_db()
    assert case.status == "reviewing"


@pytest.mark.parametrize("account_only", [False, True])
def test_direct_http_generation_sends_no_copy_body_and_replays_once(
    request, settings, monkeypatch, account_only
):
    from django.urls import reverse

    from apps.safety.models import RightsExport
    from apps.safety.rights_copy_page_review import generate_pages

    if account_only:
        case, actor, staff, _, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, staff, _, _, _ = prepared(request, settings)
    review_all(case, actor)
    path = reverse("rights_export_prepare", kwargs={"case_id": case.pk})
    version = case.version
    key = uuid4()
    reason = "Generate private copy directly from reviewed pages"
    data = {"key": str(key), "version": version, "operation": "generate_pages", "reason": reason}
    assert "copy" not in data and staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    export = RightsExport.objects.get()
    assert generate_pages(actor, case.pk, version, key, reason).pk == export.pk
    assert unseal(export.encrypted_payload)["subject_account"]["email"] == ""
    assert RightsAction.objects.filter(operation="copy_pages_export").count() == 1
    assert RightsAction.objects.filter(operation="export").count() == 1
    assert (
        staff.post(
            path, data | {"reason": "Different reason cannot reuse generation key"}
        ).status_code
        == 409
    )
    actor.user_permissions.clear()
    assert staff.post(path, data).status_code == 403
    assert RightsExport.objects.count() == 1


@pytest.mark.parametrize("change", ["proof", "session", "mfa", "source", "purged"])
def test_direct_generation_replay_rejects_changed_authority_or_unavailable_copy(
    request, settings, change
):
    from apps.core.models import User
    from apps.safety.models import RightsExport
    from apps.safety.rights_copy_page_review import generate_pages

    case, actor, _, _, _, person = prepared(request, settings)
    review_all(case, actor)
    key, version = uuid4(), case.version
    reason = "Generate private copy before authority changes"
    export = generate_pages(actor, case.pk, version, key, reason)
    if change == "proof":
        case.proofs.update(status="failed")
    elif change in {"session", "mfa"}:
        field = "session_version" if change == "session" else "mfa_version"
        User.objects.filter(pk=actor.pk).update(**{field: getattr(actor, field) + 1})
        actor = User.objects.get(pk=actor.pk)
    elif change == "source":
        person.listing.revisions.update(description="Source changed after direct generation")
    else:
        RightsExport.objects.filter(pk=export.pk).update(encrypted_payload="")
    with pytest.raises(ValidationError, match="no longer available"):
        generate_pages(actor, case.pk, version, key, reason)
    assert RightsExport.objects.count() == 1


def test_direct_generation_rolls_back_if_proof_changes_before_final_return(
    request, settings, monkeypatch
):
    from apps.safety import rights_exports
    from apps.safety.models import RightsExport
    from apps.safety.rights_copy_page_review import generate_pages

    case, actor, _, _, _, _ = prepared(request, settings)
    review_all(case, actor)
    version = case.version
    original = rights_exports.generate

    def invalidate(*args):
        export = original(*args)
        case.proofs.update(status="failed")
        return export

    monkeypatch.setattr(rights_exports, "generate", invalidate)
    with pytest.raises(ValidationError, match="no longer available"):
        generate_pages(
            actor, case.pk, version, uuid4(), "Reject proof changed before final response"
        )
    assert not RightsExport.objects.exists()
    assert not RightsAction.objects.filter(
        operation__in=["copy_pages_export", "copy_pages_compile", "export", "copy_review_read"]
    ).exists()
    case.refresh_from_db()
    assert case.version == version and case.scope_status == "simulated_passed"
