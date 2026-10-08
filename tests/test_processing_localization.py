"""Exact processing form presentation; dynamic scope remains case-dependent."""

from types import SimpleNamespace

import pytest
from playwright.sync_api import expect

from apps.safety.processing_views import ExecutionForm


def labels(page, language, fields):
    english = language == "en"
    for name, pair in fields.items():
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(pair[english] + ":")


def choices(page, name, values):
    assert (
        page.locator(f"[name={name}] option").evaluate_all(
            "nodes => nodes.map(n => [n.value,n.textContent])"
        )
        == values
    )


def assert_preparation(page, language):
    en = language == "en"
    labels(
        page,
        language,
        {
            "operation": ("Operación", "Operation"),
            "reason": ("Motivo minimizado", "Minimized reason"),
            "decisions": ("Decisiones por finalidad", "Purpose decisions"),
        },
    )
    choices(
        page,
        "operation",
        [
            ["preview", "Inspect purposes" if en else "Consultar finalidades"],
            ["prepare", "Prepare decisions" if en else "Preparar decisiones"],
        ],
    )


def assert_review(page, language):
    en = language == "en"
    labels(
        page,
        language,
        {
            "operation": ("Operación", "Operation"),
            "outcome": ("Decisión", "Outcome"),
            "reason": ("Motivo minimizado", "Minimized reason"),
        },
    )
    choices(
        page,
        "operation",
        [
            ["inspect", "Inspect plan" if en else "Consultar plan"],
            ["review", "Review plan" if en else "Revisar plan"],
        ],
    )
    choices(
        page,
        "outcome",
        [
            ["", "Select" if en else "Selecciona"],
            ["approved", "Approve" if en else "Aprobar"],
            ["rejected", "Reject" if en else "Rechazar"],
        ],
    )


def assert_execution(page, language):
    en = language == "en"
    labels(
        page,
        language,
        {
            "reason": ("Motivo minimizado", "Minimized reason"),
            "confirmed": ("Confirmo esta ejecución parcial", "I confirm this partial execution"),
        },
    )
    expect(page.locator('label[for="id_purposes_0"]')).to_have_text(
        "Account preferences" if en else "Preferencias de cuenta"
    )
    assert page.locator("[name=purposes]").count() == 1


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize(
    "account,person,subject,expected",
    [
        (1, None, None, ["account_preferences"]),
        (None, 1, 1, ["account_preferences", "publication"]),
        (None, 1, None, ["publication"]),
    ],
)
def test_execution_scope_choices_preserved(language, account, person, subject, expected):
    case = SimpleNamespace(
        account_subject_id=account, person_id=person, person=SimpleNamespace(subject_id=subject)
    )
    form = ExecutionForm(language=language, case=case)
    assert [value for value, _ in form.fields["purposes"].choices] == expected
    assert all(" / " not in caption for _, caption in form.fields["purposes"].choices)
    assert form.fields["confirmed"].required
    assert form.fields["reason"].min_length == 20 and form.fields["reason"].max_length == 2000
