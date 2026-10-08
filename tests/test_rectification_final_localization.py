"""Rectification presentation preserves recipient review and close, distinct from partial responses."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from playwright.sync_api import expect
from test_reset_localization import db_sync

from apps.safety.models import RightsAction
from apps.safety.rectification_final_views import FinalForm


def assert_form(page, language):
    en = language == "en"
    labels = {
        "operation": ("Operación", "Operation"),
        "recipient_review": ("Revisión de destinatarios", "Recipient review"),
        "draft": ("Borrador", "Draft"),
        "read": ("Consulta auditada", "Audited read"),
        "review": ("Revisión final", "Final review"),
        "purpose": ("Motivo de consulta", "Access purpose"),
        "reason": ("Motivos", "Grounds"),
        "text": ("Respuesta privada", "Private response"),
        "confirmed": (
            "Respuesta revisada sin datos de terceros",
            "Reviewed response without third-party data",
        ),
        "outcome": ("Decisión", "Outcome"),
    }
    for field, pair in labels.items():
        expect(page.locator(f'label[for="id_{field}"]')).to_have_text(pair[en] + ":")
    for name, pairs in {
        "operation": [
            ("prepare", "Preparar respuesta", "Prepare response"),
            ("inspect", "Consultar borrador independiente", "Inspect independent draft"),
            ("review", "Revisar respuesta", "Review response"),
            ("close", "Emitir y cerrar", "Issue and close"),
        ],
        "outcome": [("approved", "Aprobar", "Approve"), ("rejected", "Rechazar", "Reject")],
    }.items():
        assert page.locator(f"[name={name}] option").evaluate_all(
            "nodes=>nodes.map(n=>[n.value,n.textContent])"
        ) == [[v, en_caption if en else es_caption] for v, es_caption, en_caption in pairs]


def check_missing_preparation(page, language, case_id):
    before = db_sync(lambda: RightsAction.objects.filter(request_id=case_id).count())
    page.evaluate("document.querySelector('form').noValidate=true")
    with page.expect_response(lambda response: response.request.method == "POST") as pending:
        page.locator("button[type=submit]").click()
    assert pending.value.status == 400
    assert_form(page, language)
    assert (
        page.locator(".errorlist").all_text_contents()
        == ["Required for this action" if language == "en" else "Obligatorio para esta acción"] * 4
    )
    assert db_sync(lambda: RightsAction.objects.filter(request_id=case_id).count()) == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_rectification_recipient_review_and_close_requirements(language):
    field = FinalForm(language=language).fields["recipient_review"]
    assert field.clean("1") == 1
    with pytest.raises(ValidationError):
        field.clean(str(uuid4()))
    values = {"key": str(uuid4()), "version": 1, "responses": 0, "operation": "close"}
    form = FinalForm(values, language=language)
    assert not form.is_valid()
    assert form.errors == {
        "review": [
            "Required for this action" if language == "en" else "Obligatorio para esta acción"
        ]
    }
    form = FinalForm(values | {"review": 1}, language=language)
    assert form.is_valid() and form.cleaned_data["operation"] == "close"
    assert not form.fields["confirmed"].required
    assert form.fields["text"].min_length == 50 and form.fields["text"].max_length == 4000
