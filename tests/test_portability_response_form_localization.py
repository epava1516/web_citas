"""Response presentation preserves the covered queryset, raw text and close defaults."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from playwright.sync_api import expect

from apps.core.models import User
from apps.safety.models import RightsRequest
from apps.safety.rights_portability_response_views import (
    CloseForm,
    DecisionForm,
    DraftForm,
    ReviewForm,
)

pytestmark = pytest.mark.django_db


def draft_captions(page, language):
    pairs = {
        "export": ("Entrega cubierta", "Covered delivery"),
        "reason": ("Motivo interno", "Internal reason"),
        "response": ("Respuesta privada minimizada", "Minimized private response"),
        "redaction_confirmed": (
            "He revisado los datos de terceros y el alcance real de lo ejecutado",
            "I reviewed third-party data and actual execution scope",
        ),
    }
    for name, pair in pairs.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[language == "en"] + ":")


def review_captions(page, language):
    expect(page.locator('label[for="id_reason"]')).to_have_text(
        ("Private purpose" if language == "en" else "Motivo privado") + ":"
    )
    expect(page.locator('label[for="decision_reason"]')).to_have_text(
        ("Private purpose" if language == "en" else "Motivo privado") + ":"
    )
    expect(page.locator('label[for="decision_outcome"]')).to_have_text(
        ("Decision" if language == "en" else "Decisión") + ":"
    )
    expect(page.locator('#decision_outcome option[value="approved"]')).to_have_text(
        "Approve" if language == "en" else "Aprobar"
    )


@pytest.mark.parametrize("language", ["es", "en"])
def test_optional_language_query_defaults_and_private_literal(language):
    with CaptureQueriesContext(connection) as queries:
        plain = DraftForm(case=RightsRequest(pk=123), actor=User(pk=456))
        form = DraftForm(case=RightsRequest(pk=123), actor=User(pk=456), language=language)
        assert "kind" not in form.fields
        assert "coverage_review" in str(form.fields["export"].queryset.query)
        assert plain.fields["export"].label == "Entrega cubierta / Covered delivery"
        assert form.fields["export"].label == (
            "Covered delivery" if language == "en" else "Entrega cubierta"
        )
        assert form.fields["redaction_confirmed"].required
        literal = "Literal / private final response preserved through native minimum length"
        assert form.fields["response"].clean(literal) == literal
        for cls in [ReviewForm, DecisionForm, CloseForm]:
            original = cls()
            for name, field in original.fields.items():
                assert field.label == cls.base_fields[name].label
            assert cls.base_fields["reason"].max_length == 200
        decision = DecisionForm(language=language)
        for name, field in decision.fields.items():
            assert field.widget.attrs["id"] == "decision_" + name
        assert list(DecisionForm().fields["outcome"].choices) == list(
            DecisionForm.base_fields["outcome"].choices
        )
        assert len(queries) == 0
