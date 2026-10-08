"""Selection review captions preserve private literals, bounds and per-photo IDs."""

from uuid import uuid4

import pytest

from apps.safety.rights_portability_selection_views import ImageInspectionForm, ReviewForm


@pytest.mark.parametrize("language", ["es", "en"])
def test_review_defaults_bounds_and_photo_ids(language):
    key = uuid4()
    literal = "Literal / independent private assessment"
    review = ReviewForm(
        {"key": key, "version": 1, "operation": "inspect", "reason": literal, "outcome": ""},
        language=language,
    )
    image = ImageInspectionForm(
        {"key": key, "version": 1, "reason": literal}, photo_id=42, language=language
    )
    assert review.is_valid() and image.is_valid()
    assert review.cleaned_data["reason"] == literal and image.cleaned_data["reason"] == literal
    for cls in [ReviewForm, ImageInspectionForm]:
        assert cls.base_fields["reason"].max_length == 200
        original = cls()
        for name, field in cls.base_fields.items():
            assert original.fields[name].label == field.label
            if hasattr(field, "choices"):
                assert list(original.fields[name].choices) == list(field.choices)
        assert not cls(
            {"key": key, "version": 1, "operation": "inspect", "reason": "x" * 201},
            language=language,
        ).is_valid()
    for name in image.fields:
        assert image.fields[name].widget.attrs["id"] == f"image-42-{name}"
    assert image.fields["reason"].label == (
        "Private inspection purpose" if language == "en" else "Motivo privado de consulta"
    )
