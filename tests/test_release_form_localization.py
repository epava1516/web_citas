"""Inherited extra operations must remain selectable and keep their distinct required fields."""

from uuid import uuid4

import pytest

from apps.safety.publication_purpose_views import PublicationReleaseForm
from apps.safety.purpose_release_views import ReleaseForm


@pytest.mark.parametrize("language", ["es", "en"])
def test_inherited_operations_and_required_errors_preserved(language):
    form = PublicationReleaseForm(
        {
            "key": uuid4(),
            "version": 1,
            "operation": "follow_up",
            "reason": "Synthetic minimized review reason",
        },
        language=language,
    )
    assert [value for value, _ in form.fields["operation"].choices] == [
        "inspect",
        "propose",
        "execute",
        "follow_up",
        "history",
    ]
    assert not form.is_valid()
    for field in ["hold_version", "next_review_on"]:
        assert form.errors[field] == ["Required field" if language == "en" else "Campo obligatorio"]
    form = PublicationReleaseForm(
        {
            "key": uuid4(),
            "version": 1,
            "operation": "propose",
            "reason": "Synthetic minimized review reason",
        },
        language=language,
    )
    assert not form.is_valid()
    assert form.errors["read_id"] == [
        "Reference required" if language == "en" else "Referencia obligatoria"
    ]
    assert [value for value, _ in ReleaseForm(language=language).fields["operation"].choices] == [
        "inspect",
        "propose",
        "execute",
    ]
