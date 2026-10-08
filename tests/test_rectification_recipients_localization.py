"""Recipient presentation preserves tokens, native validators and raw grounds."""

from copy import deepcopy

import pytest
from playwright.sync_api import expect
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.recipient_assessment_views import AccessForm, DecisionForm, Decisions
from apps.safety.recipient_review_views import ReviewForm
from apps.safety.rectification_recipients import InventoryForm

pytestmark = pytest.mark.django_db(transaction=True)


def assert_screen(page, language, kind):
    types = {"inventory": InventoryForm, "access": AccessForm, "review": ReviewForm}
    form = types[kind](language=language)
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
        form = DecisionForm(language=language)
        for name, field in form.fields.items():
            if field.widget.is_hidden:
                continue
            label = fieldset.locator(f'label[for$="-{name}"]')
            expect(label).to_have_text(field.label + ":")
            if hasattr(field, "choices"):
                for value, caption in field.choices:
                    expect(
                        fieldset.locator(f'select[name$="-{name}"] option[value="{value}"]')
                    ).to_have_text(caption)


@pytest.mark.parametrize("language", ["es", "en"])
def test_native_form_values_and_generic_denial(language, request, settings, monkeypatch):
    before = {
        cls: deepcopy(cls.base_fields)
        for cls in [InventoryForm, AccessForm, DecisionForm, ReviewForm]
    }
    data = {
        "target": "gap:raw/token",
        "outcome": "disproportionate",
        "reason": "Untranslated / synthetic raw grounds",
        "evidence": "Untranslated / synthetic raw evidence",
    }
    form = DecisionForm(data, language=language)
    assert form.is_valid(), form.errors
    assert form.cleaned_data == data
    assert form.fields["outcome"].label == (
        "Proposed decision" if language == "en" else "Decisión propuesta"
    )
    assert not DecisionForm({**data, "reason": "short"}, language=language).is_valid()
    bound = Decisions(
        {
            "decisions-TOTAL_FORMS": "1",
            "decisions-INITIAL_FORMS": "0",
            **{"decisions-0-" + k: v for k, v in data.items()},
        },
        prefix="decisions",
        form_kwargs={"language": language},
    )
    assert bound.is_valid(), bound.errors
    assert bound.cleaned_data == [data]
    assert (bound.max_num, bound.absolute_max, bound.validate_max) == (1000, 1000, True)
    for cls, fields in before.items():
        for name, field in fields.items():
            assert cls.base_fields[name].label == field.label
            if hasattr(field, "choices"):
                assert list(cls.base_fields[name].choices) == list(field.choices)
    from test_rectification_review import independent_case

    case, actor, client, _, _, _ = independent_case(request, settings, monkeypatch)
    from django.contrib.auth.models import Permission

    actor.user_permissions.remove(Permission.objects.get(codename="review_rectification"))
    case = str(case.pk)
    legacy = DecisionForm()
    assert legacy.fields["outcome"].label == DecisionForm.base_fields["outcome"].label
    assert list(legacy.fields["outcome"].choices) == list(
        DecisionForm.base_fields["outcome"].choices
    )
    for suffix in [
        "rectification-execution/1/recipients/",
        "recipient-inventory/1/assessment/",
        "recipient-assessment/1/review/",
    ]:
        # Valid native session, required rectification permission revoked before object lookup.
        path = f"/{language}/moderation/rights/{case}/" + suffix
        response = client.get(path)
        # URL coverage is asserted explicitly; no 404 accepted as authorization evidence.
        assert response.status_code == 403
        assert response.content.decode() == ("Forbidden" if language == "en" else "Acceso denegado")
        assert "no-store" in response["Cache-Control"]
