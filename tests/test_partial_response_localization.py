"""Exact partial response presentation preserves effective subclass types and server requirements."""

from uuid import uuid4

import pytest
from django import forms
from playwright.sync_api import expect

from apps.safety.erasure_final_views import FinalForm
from apps.safety.processing_final_views import ProcessingForm


def assert_form(page, language, family):
    en = language == "en"
    captions = {
        "operation": ("Operación", "Operation"),
        "execution": ("Ejecución de supresión", "Erasure execution")
        if family == "erase"
        else ("Ejecución", "Execution"),
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
    for field, pair in captions.items():
        expect(page.locator(f'label[for="id_{field}"]')).to_have_text(pair[en] + ":")
    for name, pairs in {
        "operation": [
            ("prepare", "Preparar respuesta", "Prepare response"),
            ("inspect", "Consultar borrador independiente", "Inspect independent draft"),
            ("review", "Revisar respuesta", "Review response"),
            ("issue", "Emitir respuesta", "Issue response"),
        ],
        "outcome": [("approved", "Aprobar", "Approve"), ("rejected", "Rechazar", "Reject")],
    }.items():
        assert page.locator(f"[name={name}] option").evaluate_all(
            "nodes => nodes.map(n => [n.value,n.textContent])"
        ) == [[value, english if en else spanish] for value, spanish, english in pairs]


def check_missing_preparation(page, language, family, database, case):
    from apps.safety.models import RightsAction

    before = database(lambda: RightsAction.objects.filter(request=case).count())
    page.evaluate("document.querySelector('form').noValidate = true")
    with page.expect_response(lambda response: response.request.method == "POST") as pending:
        page.locator("button[type=submit]").click()
    assert pending.value.status == 400
    assert_form(page, language, family)
    expected = "Required for this action" if language == "en" else "Obligatorio para esta acción"
    assert page.locator(".errorlist").all_text_contents() == [expected] * 4
    assert database(lambda: RightsAction.objects.filter(request=case).count()) == before


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("cls", [FinalForm, ProcessingForm])
def test_partial_response_effective_execution_type(language, cls):
    form = cls(language=language)
    execution = form.fields["execution"]
    if cls is FinalForm:
        assert isinstance(execution, forms.UUIDField)
        assert execution.clean(str(uuid4())).version == 4
        with pytest.raises(forms.ValidationError):
            execution.clean("1")
    else:
        assert isinstance(execution, forms.IntegerField) and execution.min_value == 1
        assert execution.clean("1") == 1
        with pytest.raises(forms.ValidationError):
            execution.clean(str(uuid4()))
    assert not execution.required
    assert form.fields["text"].min_length == 50 and form.fields["text"].max_length == 4000
