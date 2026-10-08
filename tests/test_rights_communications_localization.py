"""Presentation controls retain native operation requirements and untouched values."""

import pytest
from playwright.sync_api import expect

from apps.safety.communication_notice_views import NoticeForm
from apps.safety.recipient_assessment_views import DecisionForm
from apps.safety.rights_communication_views import CommunicationForm

pytestmark = pytest.mark.django_db(transaction=True)


def assert_screen(page, language, cls):
    form = cls(language=language)
    for name, field in form.fields.items():
        if field.widget.is_hidden:
            continue
        expect(page.locator(f'label[for="id_{name}"]')).to_have_text(field.label + ":")
        if hasattr(field, "choices"):
            for value, caption in field.choices:
                expect(page.locator(f'select[name="{name}"] option[value="{value}"]')).to_have_text(
                    caption
                )
    for fieldset in page.locator("fieldset").all():
        for name, field in DecisionForm(language=language).fields.items():
            if not field.widget.is_hidden:
                expect(fieldset.locator(f'label[for$="-{name}"]')).to_have_text(field.label + ":")


@pytest.mark.parametrize("language", ["es", "en"])
def test_operation_requirements_and_legacy(language):
    from uuid import uuid4

    labels = (
        ("Operation", "Outcome", "Required")
        if language == "en"
        else ("Operación", "Resultado", "Obligatorio")
    )
    for operation, required in {
        "source": ["execution", "purpose"],
        "propose": ["execution", "purpose"],
        "inspect": ["plan", "purpose"],
        "review": ["plan", "read", "reason", "outcome"],
        "deliver": ["review"],
    }.items():
        form = CommunicationForm(
            {"key": uuid4(), "version": 1, "responses": 0, "operation": operation},
            language=language,
        )
        assert not form.is_valid()
        assert set(form.errors) == set(required)
        assert all(errors == [labels[2]] for errors in form.errors.values())
        assert form.fields["operation"].label == labels[0]
        assert form.fields["outcome"].label == labels[1]
    values = {"operation": "inspect", "notice": 1, "purpose": "Synthetic / unmodified reason"}
    form = NoticeForm(values, language=language)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["purpose"] == values["purpose"]
    assert form.fields["notice"].label == ("Notice" if language == "en" else "Notificación")
    for operation, field in [("inspect", "purpose"), ("ack", "read")]:
        invalid = NoticeForm({"operation": operation, "notice": 1}, language=language)
        assert not invalid.is_valid()
        assert invalid.errors[field] == [labels[2]]
    for cls in [NoticeForm, CommunicationForm]:
        legacy = cls()
        for name, field in cls.base_fields.items():
            assert legacy.fields[name].label == field.label
            if hasattr(field, "choices"):
                assert list(legacy.fields[name].choices) == list(field.choices)
