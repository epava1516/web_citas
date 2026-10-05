from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError
from test_rights_portability import assessment

from apps.safety.rights_portability_selection import project_selected, row_reference


def inputs():
    source = {
        "subject_account": {
            "email": "synthetic@example.invalid",
            "username": "Synthetic",
            "nested": {"private": "Excluded", "provided": ["Selected", "Excluded"]},
        }
    }
    decisions = assessment()
    decisions["subject_account"].update(
        status="eligible",
        basis="contract",
        origin="provided",
        automated=True,
        subject_related=True,
        third_party_reviewed=True,
        reason="Synthetic reviewed eligibility for selected fields",
        evidence="Synthetic provenance and processing evidence",
    )
    selector = {
        "subject_account": [
            {
                "row": row_reference("subject_account", 0, source["subject_account"]),
                "fields": ["/email", "/nested/provided/0"],
            }
        ]
    }
    return source, decisions, selector


def test_selected_fields_omit_all_other_values_and_reject_changed_source():
    source, decisions, selection = inputs()
    result = project_selected(source, decisions, selection)
    assert result["datasets"]["subject_account"] == [
        {"fields": {"/email": "synthetic@example.invalid", "/nested/provided/0": "Selected"}}
    ]
    assert "Excluded" not in str(result) and "username" not in str(result)
    changed = deepcopy(source)
    changed["subject_account"]["username"] = "Changed source"
    with pytest.raises(ValidationError):
        project_selected(changed, decisions, selection)


@pytest.mark.parametrize(
    "paths",
    [
        ["/nested"],
        ["/missing"],
        ["/email", "/email"],
        ["/nested/provided/01"],
        ["/bad~2escape"],
        [],
    ],
)
def test_implicit_containers_invalid_paths_and_duplicates_are_rejected(paths):
    source, decisions, selection = inputs()
    selection["subject_account"][0]["fields"] = paths
    with pytest.raises(ValidationError):
        project_selected(source, decisions, selection)


def test_pending_dataset_cannot_be_selected():
    source, decisions, selection = inputs()
    decisions["subject_account"]["status"] = "pending"
    with pytest.raises(ValidationError):
        project_selected(source, decisions, selection)


def test_mixed_fields_require_exact_eligible_evidence_and_never_export_it():
    source, decisions, selection = inputs()
    eligible = deepcopy(decisions["subject_account"])
    decisions["subject_account"].update(status="granular", origin="mixed")
    ref = selection["subject_account"][0]["row"]
    with pytest.raises(ValidationError, match="exact field evidence"):
        project_selected(source, decisions, selection)
    facts = {
        "subject_account": {
            ref: {path: deepcopy(eligible) for path in selection["subject_account"][0]["fields"]}
        }
    }
    result = project_selected(source, decisions, selection, field_evidence=facts)
    assert (
        result["datasets"]["subject_account"][0]["fields"]["/email"] == "synthetic@example.invalid"
    )
    assert "evidence" not in str(result) and "Excluded" not in str(result)
    facts["subject_account"][ref]["/email"]["origin"] = "third_party"
    with pytest.raises(ValidationError, match="delivery conditions"):
        project_selected(source, decisions, selection, field_evidence=facts)
    facts["subject_account"][ref]["/email"] = eligible
    facts["subject_account"][ref]["/username"] = eligible
    with pytest.raises(ValidationError, match="exact evidence"):
        project_selected(source, decisions, selection, field_evidence=facts)
