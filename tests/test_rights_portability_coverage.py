"""Pure coverage coherence: not authorization, persistence or independent review."""

from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError

from apps.safety.rights_portability import DATASETS
from apps.safety.rights_portability_coverage import compile_coverage
from apps.safety.rights_portability_selection import row_reference


def fixture():
    facts = {
        "status": "eligible",
        "basis": "contract",
        "origin": "provided",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic assessed scope of every dataset",
        "evidence": "Synthetic documented provided personal values",
    }
    assessment = {name: dict(facts) for name in DATASETS}
    source = {
        "profile": {"alias": "Synthetic alias", "generated_reference": "synthetic-reference"},
        "subject_account": None,
        "revisions": [],
        "legal_acceptances": [],
        "account_activity": {"agency_relationships": [], "personal_contacts": [], "favorites": []},
        "representation": None,
    }
    reference = row_reference("profile", 0, source["profile"])
    selection = {name: [] for name in DATASETS}
    selection["profile"] = [{"row": reference, "fields": ["/alias"]}]
    omissions = {name: {} for name in DATASETS}
    omissions["profile"] = {reference: {"all": dict(facts, status="excluded", origin="inferred")}}
    return source, assessment, selection, omissions, reference, facts


def test_partial_row_has_explicit_definite_omissions_and_no_evidence_in_projection():
    source, assessment, selection, omissions, reference, _ = fixture()
    summary = compile_coverage(source, assessment, selection, omissions, [], {})
    assert summary["datasets"]["profile"] == {
        "status": "covered",
        "rows": 1,
        "included_fields": 1,
        "excluded_fields": 1,
    }
    assert summary["projection"]["datasets"]["profile"] == [
        {"fields": {"/alias": "Synthetic alias"}}
    ]
    assert reference not in str(summary)
    assert "Synthetic documented" not in str(summary)


@pytest.mark.parametrize(
    "mutation",
    ["missing", "unknown", "extra", "pending", "binary_shape", "missing_dataset", "included_path"],
)
def test_incomplete_unknown_or_foreign_coverage_rejected(mutation):
    source, assessment, selection, omissions, reference, facts = fixture()
    images = []
    if mutation == "missing":
        omissions["profile"] = {}
    elif mutation == "unknown":
        omissions["profile"][reference]["all"].update(
            basis="unknown",
            origin="unknown",
            automated=None,
            subject_related=None,
            third_party_reviewed=None,
        )
    elif mutation == "extra":
        omissions["profile"]["foreign-row"] = deepcopy(omissions["profile"][reference])
    elif mutation == "pending":
        assessment["profile"]["status"] = "pending"
    elif mutation == "binary_shape":
        images = [{}]
    elif mutation == "missing_dataset":
        omissions.pop("favorites")
    elif mutation == "included_path":
        omissions["profile"][reference] = {
            "fields": {"/alias": dict(facts, status="excluded", origin="inferred")}
        }
    with pytest.raises(ValidationError):
        compile_coverage(source, assessment, selection, omissions, images, {})


def test_exact_field_exclusions_and_empty_rows():
    source, assessment, selection, omissions, reference, facts = fixture()
    omissions["profile"][reference] = {
        "fields": {"/generated_reference": dict(facts, status="excluded", origin="inferred")}
    }
    summary = compile_coverage(source, assessment, selection, omissions, [], {})
    assert summary["datasets"]["favorites"]["rows"] == 0
    assert summary["datasets"]["profile"]["excluded_fields"] == 1


@pytest.mark.parametrize("outcome", ["missing", "unknown", "excluded", "included", "overlap"])
def test_metadata_selection_does_not_complete_binary_coverage(outcome):
    source, assessment, _, _, _, facts = fixture()
    source["profile"] = None
    photo = "00000000-0000-0000-0000-000000000001"
    source["revisions"] = [{"images": [{"photo": photo, "processing_status": "ready"}]}]
    reference = row_reference("revisions", 0, source["revisions"][0])
    selection = {name: [] for name in DATASETS}
    selection["revisions"] = [
        {"row": reference, "fields": ["/images/0/photo", "/images/0/processing_status"]}
    ]
    omissions = {name: {} for name in DATASETS}
    images, image_omissions = [], {}
    if outcome in {"excluded", "overlap"}:
        image_omissions[photo] = dict(facts, status="excluded", origin="third_party")
    elif outcome == "unknown":
        image_omissions[photo] = dict(
            facts,
            status="excluded",
            basis="unknown",
            origin="unknown",
            automated=None,
            subject_related=None,
        )
    if outcome in {"included", "overlap"}:
        images = [
            {
                "row": reference,
                "path": "/images/0/photo",
                "photo": photo,
                "content_digest": "a" * 64,
                "conditions": facts,
            }
        ]
    if outcome in {"missing", "unknown", "overlap"}:
        with pytest.raises(ValidationError):
            compile_coverage(source, assessment, selection, omissions, images, image_omissions)
    else:
        summary = compile_coverage(
            source, assessment, selection, omissions, images, image_omissions
        )
        assert summary["included_images"] == (outcome == "included")
        assert summary["excluded_images"] == (outcome == "excluded")


def test_approved_dataset_exclusion_covers_rows_without_selection():
    source, assessment, selection, omissions, _, facts = fixture()
    assessment["profile"] = dict(facts, status="excluded", basis="legal_obligation")
    selection.pop("profile")
    omissions["profile"] = {}
    result = compile_coverage(source, assessment, selection, omissions, [], {})
    assert result["datasets"]["profile"] == {"status": "excluded", "rows": 1}


def test_mixed_selected_fields_still_require_own_eligibility():
    source, assessment, selection, omissions, reference, facts = fixture()
    assessment["profile"].update(
        status="granular",
        origin="mixed",
        basis="unknown",
        subject_related=None,
        third_party_reviewed=None,
    )
    with pytest.raises(ValidationError):
        compile_coverage(source, assessment, selection, omissions, [], {})
    result = compile_coverage(
        source,
        assessment,
        selection,
        omissions,
        [],
        {},
        field_evidence={"profile": {reference: {"/alias": facts}}},
    )
    assert result["datasets"]["profile"]["included_fields"] == 1


def test_changed_source_invalidates_old_row_declarations():
    source, assessment, selection, omissions, _, _ = fixture()
    source["profile"]["alias"] = "Changed synthetic alias"
    with pytest.raises(ValidationError):
        compile_coverage(source, assessment, selection, omissions, [], {})


def test_fully_selected_row_rejects_unnecessary_omission():
    source, assessment, selection, omissions, _, _ = fixture()
    selection["profile"][0]["fields"].append("/generated_reference")
    with pytest.raises(ValidationError):
        compile_coverage(source, assessment, selection, omissions, [], {})
    omissions["profile"] = {}
    result = compile_coverage(source, assessment, selection, omissions, [], {})
    assert result["datasets"]["profile"]["included_fields"] == 2
    assert result["datasets"]["profile"]["excluded_fields"] == 0


def test_source_binary_duplicates_rejected_even_when_excluded():
    source, assessment, _, _, _, facts = fixture()
    source["profile"] = None
    photo = "00000000-0000-0000-0000-000000000001"
    image_row = {"images": [{"photo": photo, "processing_status": "ready"}]}
    source["revisions"] = [image_row, deepcopy(image_row)]
    selection = {name: [] for name in DATASETS}
    omissions = {name: {} for name in DATASETS}
    excluded = dict(facts, status="excluded", origin="inferred")
    for index, row in enumerate(source["revisions"]):
        omissions["revisions"][row_reference("revisions", index, row)] = {"all": excluded}
    with pytest.raises(ValidationError, match="Duplicate source binary"):
        compile_coverage(source, assessment, selection, omissions, [], {photo: excluded})
