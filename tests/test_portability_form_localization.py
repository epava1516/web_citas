"""Static presentation preserves typed unknowns and the native nine-dataset schema."""

import pytest
from django.utils import translation
from playwright.sync_api import expect

from apps.safety.rights_portability import DATASETS
from apps.safety.rights_portability_review_views import ReviewForm
from apps.safety.rights_portability_views import DatasetForm, Datasets, DraftForm, ReadForm


def captions(page, language):
    english = language == "en"
    for name, pair in {
        "reason": ("Motivo privado", "Private reason"),
        "assessment_id": ("Referencia de evaluación", "Assessment reference"),
        "purpose": ("Motivo de consulta", "Inspection purpose"),
    }.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[english] + ":")
    assert page.locator("fieldset").count() == 9
    for row in page.locator("fieldset").all():
        for name, pair in {
            "status": ("Decisión", "Decision"),
            "basis": ("Base jurídica", "Lawful basis"),
            "origin": ("Origen", "Origin"),
            "automated": ("Tratamiento automatizado", "Automated processing"),
            "subject_related": ("Datos del interesado", "Data concerning the subject"),
            "third_party_reviewed": ("Terceros revisados", "Third parties reviewed"),
            "reason": ("Justificación", "Justification"),
            "evidence": ("Evidencia", "Evidence"),
        }.items():
            expect(row.locator(f'label[for$="-{name}"]')).to_have_text(pair[english] + ":")
        expect(row.locator('option[value="pending"]')).to_have_text(
            "Pending" if english else "Pendiente"
        )
        for name in ["automated", "subject_related", "third_party_reviewed"]:
            expect(row.locator(f'select[name$="-{name}"] option[value="unknown"]')).to_have_text(
                "Unknown" if english else "Desconocido"
            )


@pytest.mark.parametrize("language", ["es", "en"])
def test_form_typed_unknowns_default_and_schema(language):
    with translation.override(language):
        field = DatasetForm(
            {
                "dataset": DATASETS[0],
                "status": "pending",
                "basis": "unknown",
                "origin": "unknown",
                "automated": "unknown",
                "subject_related": "yes",
                "third_party_reviewed": "no",
                "reason": "Literal / unmodified",
                "evidence": "Raw / evidence",
            },
            language=language,
        )
        assert field.is_valid(), field.errors
        assert field.cleaned_data["automated"] is None
        assert field.cleaned_data["subject_related"] is True
        assert field.cleaned_data["third_party_reviewed"] is False
        assert field.cleaned_data["reason"] == "Literal / unmodified"
        assert field.cleaned_data["evidence"] == "Raw / evidence"
        assert (
            Datasets.min_num,
            Datasets.max_num,
            Datasets.absolute_max,
            Datasets.validate_min,
            Datasets.validate_max,
        ) == (9, 9, 9, True, True)
        for cls in [DraftForm, ReadForm, ReviewForm]:
            original = cls()
            for name, base in cls.base_fields.items():
                assert original.fields[name].label == base.label
                if hasattr(base, "choices"):
                    assert list(original.fields[name].choices) == list(base.choices)
        original = DatasetForm()
        for name, base in DatasetForm.base_fields.items():
            assert original.fields[name].label == base.label
            if name not in {"basis", "origin"} and hasattr(base, "choices"):
                assert list(original.fields[name].choices) == list(base.choices)
