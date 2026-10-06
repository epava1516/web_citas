"""Independent coverage read exposes omitted values only after audit, PostgreSQL."""

from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.safety import rights_portability_coverage_inspection as inspection
from apps.safety.models import RightsAction, RightsPortabilityCoverageRead
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_portability_coverage_store import save_coverage

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_independent_read_includes_pending_omissions_and_audits_before_decrypt(
    request, settings, monkeypatch, account_only
):
    case, author, _, decision, _, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    reason = "Inspect synthetic coverage including omitted source values"
    row = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        uuid4(),
        0,
        reason,
        {name: {} for name in SECTIONS},
        {},
        allow_partial=True,
    )
    reviewer = User.objects.get(pk=decision.action.actor_id)
    dataset = "subject_account" if account_only else "profile"
    key = uuid4()
    original = inspection.unseal
    observed = []
    # baseline_body uses the shared validator's unseal function.
    from apps.safety import rights_portability_coverage_pages as pages

    original_baseline = pages.unseal

    def audited(ciphertext):
        if ciphertext == row.encrypted_coverage:
            assert RightsAction.objects.filter(
                key=key, actor=reviewer, operation="coverage_inspect"
            ).exists()
            observed.append(True)
        return original_baseline(ciphertext)

    with monkeypatch.context() as patch:
        patch.setattr(pages, "unseal", audited)
        action, page = inspection.inspect_page(
            reviewer, case.pk, case.version, row.pk, key, reason, dataset
        )
    assert observed and action.operation == "coverage_inspect"
    recorded = RightsPortabilityCoverageRead.objects.get(action=action)
    assert recorded.coverage_id == row.pk and recorded.dataset == dataset
    assert recorded.coverage_digest == row.coverage_digest
    assert any(item["status"] == "pending" for item in page["fields"])
    assert any(item["status"] == "included" for item in page["fields"])
    assert "projection" not in page["summary"]
    assert (
        inspection.inspect_page(reviewer, case.pk, case.version, row.pk, key, reason, dataset)[0].pk
        == action.pk
    )
    with pytest.raises(PermissionDenied):
        inspection.inspect_page(author, case.pk, case.version, row.pk, uuid4(), reason, dataset)
    with pytest.raises(ValidationError):
        inspection.inspect_page(reviewer, case.pk, case.version, row.pk, key, reason, "favorites")
    assert original(row.encrypted_coverage)["allow_partial"] is True
    assert RightsPortabilityCoverageRead.objects.filter(coverage=row).count() == 1
    recorded.page_digest = "0" * 64
    recorded.save(update_fields=["page_digest"])
    with pytest.raises(ValidationError, match="Original coverage page digest changed"):
        inspection.inspect_page(reviewer, case.pk, case.version, row.pk, key, reason, dataset)


def test_independent_binary_metadata_read_distinguishes_pending_from_excluded(
    request, settings, monkeypatch
):
    case, author, _, decision, _, _, _ = prepared_selection(request, settings, monkeypatch, False)
    reason = "Inspect synthetic omitted binary conditions independently"
    row = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        uuid4(),
        0,
        reason,
        {name: {} for name in SECTIONS},
        {},
        allow_partial=True,
    )
    reviewer = User.objects.get(pk=decision.action.actor_id)
    key = uuid4()
    action, page = inspection.inspect_page(
        reviewer, case.pk, case.version, row.pk, key, reason, "revisions", binary=True
    )
    assert page["binary"] is True and page["fields"]
    assert all(
        item["status"] == "pending" and item["conditions"] is None for item in page["fields"]
    )
    assert all("photo" in item for item in page["fields"])
    assert "data:image" not in str(page)
    assert (
        inspection.inspect_page(
            reviewer, case.pk, case.version, row.pk, key, reason, "revisions", binary=True
        )[0].pk
        == action.pk
    )
    with pytest.raises(ValidationError):
        inspection.inspect_page(
            reviewer, case.pk, case.version, row.pk, key, reason, "revisions", binary=False
        )
    with pytest.raises(PermissionDenied):
        inspection.inspect_page(
            author, case.pk, case.version, row.pk, uuid4(), reason, "revisions", binary=True
        )


def test_complete_page_gate_rejects_partial_and_binds_original_reads(
    request, settings, monkeypatch
):
    from django.db import transaction

    from apps.safety.rights_exports import reviewer_case, source_copy
    from apps.safety.rights_portability_coverage_read_gate import (
        require_complete_reads,
        required_pages,
    )

    case, author, _, decision, _, _, _ = prepared_selection(request, settings, monkeypatch, True)
    reason = "Inspect all synthetic coverage pages before independent approval"
    row = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        uuid4(),
        0,
        reason,
        {name: {} for name in SECTIONS},
        {},
        allow_partial=True,
    )
    reviewer = User.objects.get(pk=decision.action.actor_id)
    with transaction.atomic():
        locked, person, listing = reviewer_case(reviewer, case.pk)
        source = source_copy(person, listing, locked)
        with pytest.raises(ValidationError, match="Inspect every current"):
            require_complete_reads(reviewer, locked, row, source)
    for dataset, index, page, binary in required_pages(source):
        inspection.inspect_page(
            reviewer,
            case.pk,
            case.version,
            row.pk,
            uuid4(),
            reason,
            dataset,
            index,
            page,
            binary=binary,
        )
    with transaction.atomic():
        ids = require_complete_reads(reviewer, case, row, source)
        assert len(ids) == len(required_pages(source))
        assert require_complete_reads(reviewer, case, row, source, ids=ids) == ids
        with pytest.raises(ValidationError):
            require_complete_reads(reviewer, case, row, source, ids=ids[:-1])
    read = RightsPortabilityCoverageRead.objects.get(pk=ids[0])
    read.page_digest = "0" * 64
    read.save(update_fields=["page_digest"])
    with transaction.atomic(), pytest.raises(ValidationError, match="Original coverage page digest changed"):
        require_complete_reads(reviewer, case, row, source, ids=ids)
    case.refresh_from_db()
    assert case.version == row.action.expected_version
