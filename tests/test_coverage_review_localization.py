"""Coverage presentation keeps native readings/decision bounds and private text."""

from uuid import uuid4

import pytest
from playwright.sync_api import expect

from apps.safety.rights_portability_coverage_review_views import (
    DecisionForm,
    PageForm,
    condition_captions,
)


def captions(page, language):
    pairs = {
        "dataset": ("Conjunto", "Dataset"),
        "row_number": ("Registro", "Record"),
        "field_page": ("Página", "Page"),
        "reason": ("Motivo privado", "Private purpose"),
    }
    for name, pair in pairs.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")
    for name, pair in {
        "reason": ("Motivo privado de decisión", "Private decision reason"),
        "outcome": ("Decisión", "Decision"),
    }.items():
        expect(page.locator(f'label[for="decision_{name}"]')).to_have_text(
            pair[language == "en"] + ":"
        )
    expect(page.locator('#id_dataset option[value="binary"]')).to_have_text(
        "Images" if language == "en" else "Imágenes"
    )
    expect(page.locator('#decision_outcome option[value="approved"]')).to_have_text(
        "Approve" if language == "en" else "Aprobar"
    )


@pytest.mark.parametrize("language", ["es", "en"])
def test_forms_defaults_raw_bounds_and_tristate(language):
    raw = "Literal / independent synthetic coverage rationale"
    page = PageForm(
        {
            "key": uuid4(),
            "version": 1,
            "operation": "inspect",
            "dataset": "binary",
            "row_number": 1,
            "field_page": 1,
            "reason": raw,
        },
        language=language,
    )
    decision = DecisionForm(
        {"key": uuid4(), "version": 1, "operation": "review", "outcome": "approved", "reason": raw},
        language=language,
    )
    assert page.is_valid() and decision.is_valid()
    assert page.cleaned_data["reason"] == raw and decision.cleaned_data["reason"] == raw
    for cls in [PageForm, DecisionForm]:
        original = cls()
        for name, field in cls.base_fields.items():
            assert original.fields[name].label == field.label
        assert cls.base_fields["reason"].max_length == 200
    assert dict(PageForm().fields["dataset"].choices)["binary"] == "Imágenes / Images"
    assert list(DecisionForm().fields["outcome"].choices) == list(
        DecisionForm.base_fields["outcome"].choices
    )
    for name, field in decision.fields.items():
        assert field.widget.attrs["id"] == "decision_" + name
    data = {
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": False,
        "third_party_reviewed": None,
        "reason": raw,
        "evidence": raw,
    }
    saved = data.copy()
    result = condition_captions(data, language)
    assert data == saved and "reason" not in result and "evidence" not in result
    assert result["automated"] == ("Yes" if language == "en" else "Sí")
    assert result["subject_related"] == "No"
    assert result["third_party_reviewed"] == ("Unknown" if language == "en" else "Desconocido")
