"""Final access response captions preserve shared defaults and typed review data."""

from uuid import uuid4

import pytest
from playwright.sync_api import expect

from apps.safety.rights_access_response_views import DecisionForm, ReviewForm

pytestmark = pytest.mark.django_db(transaction=True)


def assert_draft(page, language):
    for field, pair in {
        "reason": ("Motivo interno", "Internal reason"),
        "response": ("Respuesta privada minimizada", "Minimized private response"),
        "scope_inventory": ("Inventario para paquete de acceso", "Access package inventory"),
        "delivery_decisions": ("Decisiones por grupos y recursos", "Group and resource decisions"),
        "coverage_review": ("Contabilidad aprobada", "Approved accounting"),
        "export": ("Copia con información aprobada", "Copy with approved information"),
    }.items():
        expect(page.locator(f'label[for="id_{field}"]')).to_have_text(pair[language == "en"] + ":")


def assert_review(page, language):
    reason = "Private purpose" if language == "en" else "Motivo privado"
    for ident in ["id_reason", "decision_reason"]:
        expect(page.locator(f'label[for="{ident}"]')).to_have_text(reason + ":")
    expect(page.locator('label[for="decision_outcome"]')).to_have_text(
        ("Decision" if language == "en" else "Decisión") + ":"
    )
    for value, pair in [("approved", ("Aprobar", "Approve")), ("rejected", ("Rechazar", "Reject"))]:
        expect(page.locator(f'#decision_outcome option[value="{value}"]')).to_have_text(
            pair[language == "en"]
        )


@pytest.mark.parametrize("language", ["es", "en"])
def test_shared_review_values_and_legacy(language):
    data = {
        "key": uuid4(),
        "version": 1,
        "read_id": 1,
        "reason": "Synthetic / unchanged private purpose",
        "outcome": "approved",
    }
    form = DecisionForm(data, language=language)
    assert form.is_valid(), form.errors
    assert form.cleaned_data == data
    assert form.fields["reason"].label == (
        "Private purpose" if language == "en" else "Motivo privado"
    )
    assert not DecisionForm({**data, "reason": "short"}, language=language).is_valid()
    from apps.safety.rights_access_field_decision_views import ProposalForm
    from apps.safety.rights_access_scope_views import ScopeForm
    from apps.safety.rights_access_supplement_views import SupplementForm

    for cls in [ReviewForm, DecisionForm, ScopeForm, ProposalForm, SupplementForm]:
        legacy = cls()
        for name, field in cls.base_fields.items():
            assert legacy.fields[name].label == field.label
            if hasattr(field, "choices"):
                assert list(legacy.fields[name].choices) == list(field.choices)
