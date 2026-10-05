"""PostgreSQL own coverage preparation; synthetic exclusions only."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.safety import rights_portability_coverage_pages as pages
from apps.safety.crypto import seal, unseal
from apps.safety.models import RightsAction, RightsPortabilityCoverage
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_pages import prepare_page, save_page
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_guided_omissions_preserve_other_rows_replay_and_reject_stale_pages(
    request, settings, monkeypatch, account_only
):
    case, author, selection, decision, _, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    chosen = unseal(selection.encrypted_selection)["selection"]
    candidates = []
    for name, reader in SECTIONS.items():
        for index, row in enumerate(reader(source)):
            reference = row_reference(name, index, row)
            selected = next(
                (set(item["fields"]) for item in chosen[name] if item["row"] == reference), set()
            )
            if any(item["path"] not in selected for item in scalar_fields(row)):
                candidates.append((name, index))
    assert candidates
    reason = "Prepare synthetic omitted fields for later independent review"
    facts = {
        "status": "excluded",
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic fixture exclusion without any production factual claim",
        "evidence": "Synthetic fixture evidence for guided coverage storage",
    }
    name, index = candidates[0]
    page_key = uuid4()
    page = prepare_page(author, case.pk, case.version, decision.pk, page_key, reason, name, index)
    path = page["fields"][0]["path"]
    key = uuid4()
    row = save_page(author, case.pk, page["token"], key, reason, {path: facts})
    assert save_page(author, case.pk, page["token"], key, reason, {path: facts}).pk == row.pk
    with pytest.raises(ValidationError, match="Conflicting coverage page key"):
        prepare_page(author, case.pk, case.version, decision.pk, page_key, reason, name, index)
    with pytest.raises(ValidationError):
        save_page(author, case.pk, page["token"] + "tampered", uuid4(), reason, {path: facts})
    first_body = unseal(row.encrypted_coverage)
    assert first_body["omissions"][name][page["row"]]["fields"] == {path: facts}
    with pytest.raises(ValidationError):
        save_page(author, case.pk, page["token"], uuid4(), reason, {path: facts})
    other_name, other_index = candidates[1] if len(candidates) > 1 else candidates[0]
    other_key = uuid4()
    original_unseal = pages.unseal
    observed = []

    def audit_before_decryption(ciphertext):
        if ciphertext == row.encrypted_coverage:
            assert transaction.get_connection().in_atomic_block
            assert RightsAction.objects.filter(
                key=other_key, request=case, actor=author, operation="coverage_page"
            ).exists()
            observed.append(True)
        return original_unseal(ciphertext)

    with monkeypatch.context() as patch:
        patch.setattr(pages, "unseal", audit_before_decryption)
        other = prepare_page(
            author, case.pk, case.version, decision.pk, other_key, reason, other_name, other_index
        )
    assert observed
    other_path = next(
        item["path"]
        for item in other["fields"]
        if (other_name, other_index) != (name, index) or item["path"] != path
    )
    other_decisions = {other_path: facts}
    if (other_name, other_index) == (name, index):
        other_decisions[path] = facts
    with pytest.raises(ValidationError):
        save_page(author, case.pk, other["token"], uuid4(), reason, {"/foreign": facts})
    second = save_page(author, case.pk, other["token"], uuid4(), reason, other_decisions)
    second_body = unseal(second.encrypted_coverage)
    assert second_body["omissions"][name][page["row"]]["fields"][path] == facts
    assert second_body["image_omissions"] == first_body["image_omissions"]
    removal = prepare_page(author, case.pk, case.version, decision.pk, uuid4(), reason, name, index)
    kept = {other_path: facts} if (other_name, other_index) == (name, index) else {}
    third = save_page(author, case.pk, removal["token"], uuid4(), reason, kept)
    assert path not in unseal(third.encrypted_coverage)["omissions"][name].get(page["row"], {}).get(
        "fields", {}
    )
    assert (
        unseal(third.encrypted_coverage)["omissions"][other_name][other["row"]]["fields"][
            other_path
        ]
        == facts
    )
    third.encrypted_coverage = seal({"tampered": True})
    third.save(update_fields=["encrypted_coverage"])
    with pytest.raises(ValidationError):
        prepare_page(author, case.pk, case.version, decision.pk, uuid4(), reason, name, index)
    assert RightsPortabilityCoverage.objects.filter(request=case).count() == 3
    case.refresh_from_db()
    assert case.version == locked.version and case.status == locked.status
