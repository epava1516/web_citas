"""Native typed targets and raw redaction remain independent of presentation language."""

from uuid import uuid4

import pytest

from apps.safety.rights_access_field_decision_views import ProposalForm
from apps.safety.rights_access_response_views import DecisionForm, ReviewForm
from apps.safety.rights_access_scope_views import ScopeForm

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_typed_values_and_legacy(language):
    data = {
        "key": uuid4(),
        "version": 1,
        "response_version": 0,
        "reason": "Synthetic / unchanged private purpose",
        "read_id": 1,
        "model": "core.User",
        "reference": "a" * 64,
        "field": "email",
        "outcome": "redacted",
        "redacted": "[redacted] / untouched@example.invalid",
    }
    form = ProposalForm(data, language=language)
    assert form.is_valid(), form.errors
    assert form.cleaned_data == data
    assert form.fields["reason"].label == (
        "Private purpose" if language == "en" else "Motivo privado"
    )
    assert list(form.fields["outcome"].choices) == [
        ("included", "Include" if language == "en" else "Incluir"),
        ("redacted", "Redact" if language == "en" else "Redactar"),
        ("omitted", "Omit" if language == "en" else "Omitir"),
    ]
    assert not ProposalForm({**data, "reference": "short"}, language=language).is_valid()
    scope = ScopeForm(
        {k: v for k, v in data.items() if k in ScopeForm.base_fields}, language=language
    )
    assert scope.is_valid(), scope.errors
    assert scope.cleaned_data["reason"] == data["reason"]
    for cls in [ScopeForm, ProposalForm, ReviewForm, DecisionForm]:
        legacy = cls()
        for name, field in cls.base_fields.items():
            assert legacy.fields[name].label == field.label
            if hasattr(field, "choices"):
                assert list(legacy.fields[name].choices) == list(field.choices)
