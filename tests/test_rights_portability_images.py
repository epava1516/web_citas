from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError
from test_rights_portability import assessment

from apps.safety.rights_portability_images import checked_images
from apps.safety.rights_portability_selection import row_reference


def inputs():
    row = {
        "revision": "synthetic",
        "images": [{"photo": "synthetic-photo", "processing_status": "ready"}],
    }
    value = assessment()
    facts = dict(
        status="eligible",
        basis="contract",
        origin="provided",
        automated=True,
        subject_related=True,
        third_party_reviewed=True,
        reason="Synthetic image provenance assessed independently",
        evidence="Synthetic evidence for provided image and processing",
    )
    value["revisions"].update(facts)
    value["revisions"].update(status="granular", origin="mixed")
    selected = [
        {
            "row": row_reference("revisions", 0, row),
            "path": "/images/0/photo",
            "photo": "synthetic-photo",
            "content_digest": "a" * 64,
            "conditions": facts,
        }
    ]
    return {"revisions": [row]}, value, selected, {"synthetic-photo": "a" * 64}


def test_binary_declaration_requires_its_own_conditions_and_exact_audited_content():
    source, value, selected, inspected = inputs()
    assert checked_images(source, value, selected, inspected) == selected
    assert checked_images(source, value, [], {}) == []
    with pytest.raises(ValidationError):
        checked_images(source, value, selected, {})
    changed = deepcopy(source)
    changed["revisions"][0]["images"][0]["photo"] = "another-photo"
    with pytest.raises(ValidationError):
        checked_images(changed, value, selected, inspected)


@pytest.mark.parametrize(
    "change",
    [
        "third_party",
        "inferred",
        "unknown",
        "unreviewed",
        "digest",
        "path",
        "long_path",
        "duplicate",
        "extra",
        "source_status",
        "excluded",
    ],
)
def test_unreviewed_or_changed_binary_declarations_are_rejected(change):
    source, value, selected, inspected = inputs()
    if change in {"third_party", "inferred", "unknown"}:
        selected[0]["conditions"]["origin"] = change
    elif change == "unreviewed":
        selected[0]["conditions"]["third_party_reviewed"] = False
    elif change == "digest":
        selected[0]["content_digest"] = "b" * 64
    elif change == "path":
        selected[0]["path"] = "/images/00/photo"
    elif change == "long_path":
        selected[0]["path"] = "/images/" + "9" * 5000 + "/photo"
    elif change == "duplicate":
        selected.append(deepcopy(selected[0]))
    elif change == "extra":
        inspected["another-photo"] = "a" * 64
    elif change == "source_status":
        source["revisions"][0]["images"][0]["processing_status"] = "failed"
    elif change == "excluded":
        value["revisions"].update(status="excluded", origin="third_party")
    with pytest.raises(ValidationError):
        checked_images(source, value, selected, inspected)


def test_sparse_binary_selection_hashes_only_candidate_rows_with_original_indices(monkeypatch):
    from apps.safety import rights_portability_images as images

    source, value, selected, inspected = inputs()
    chosen = deepcopy(source["revisions"][0])
    rows = [{"revision": f"synthetic-{index}", "description": "Synthetic narrative " * 500,
             "images": []} for index in range(500)]
    rows[317] = chosen
    rows[499]["images"] = [{"photo": "unselected-photo", "processing_status": "ready"}]
    source["revisions"] = rows
    selected[0]["row"] = row_reference("revisions", 317, chosen)
    before = deepcopy(source)
    calls = []
    native = images.row_reference

    def counted(dataset, index, row):
        calls.append(index)
        return native(dataset, index, row)

    monkeypatch.setattr(images, "row_reference", counted)
    assert checked_images(source, value, selected, inspected) == selected
    assert source == before
    assert calls == [317]
    # A valid foreign row hash cannot substitute for the row containing this photo.
    selected[0]["row"] = native("revisions", 499, rows[499])
    with pytest.raises(ValidationError):
        checked_images(source, value, selected, inspected)
