"""A native assignment helper remains part of the value-kernel proof boundary."""
from copy import copy
from functools import wraps

from apps.listings import projected_publication as projection
from apps.listings.forms import ContactsForm
from apps.listings.models import Revision
from apps.listings.public_validation import validate_publication_binding


def test_semantic_assignment_wrapper_disables_value_proof(monkeypatch):
    revision = Revision(manager_version=1)
    data = {"whatsapp": False, "telegram": "Valid_name",
            "contact_exposure_accepted": True, "accept_publishing": True,
            "legal_version": "synthetic"}
    assert projection.supported()
    field = Revision._meta.get_field("telegram")
    original = field.save_form_data

    @wraps(original)
    def change_value(instance, value):
        original(instance, "x" * 33)

    monkeypatch.setattr(field, "save_form_data", change_value)
    native = ContactsForm(data, instance=copy(revision))
    assert not native.is_valid() and "telegram" in native.errors
    prototype = ContactsForm(data, instance=copy(revision))
    # Deliberately bypass the proof gate to expose why this dependency matters.
    assert validate_publication_binding(prototype, data, copy(revision), value_model=True)
    assert not projection.supported()


def test_private_callbacks_do_not_retain_the_validated_binding(monkeypatch):
    import gc
    from weakref import ref
    from apps.listings import public_validation
    references = []
    original = public_validation.validate_publication_value_fields
    def observe(form):
        references.append(ref(form))
        return original(form)
    monkeypatch.setattr(public_validation, "validate_publication_value_fields", observe)
    revision = Revision(manager_version=1)
    data = {"whatsapp": False, "telegram": "Valid_name",
            "contact_exposure_accepted": True, "accept_publishing": True,
            "legal_version": "synthetic"}
    prototype = ContactsForm(data, instance=copy(revision))
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        assert validate_publication_binding(prototype, data, copy(revision), value_model=True)
        assert len(references) == 1 and references[0]() is None
    finally:
        if was_enabled:
            gc.enable()


def test_widget_prefix_cleaner_and_errors_match_native_fields():
    from apps.listings.public_validation import validate_publication_input_fields
    from django import forms
    class ValueForm(forms.Form):
        text = forms.CharField(max_length=5)
        enabled = forms.BooleanField(required=False)
        tags = forms.MultipleChoiceField(choices=[("a", "A"), ("b", "B")], required=False)
        def clean_text(self):
            return self.cleaned_data["text"].upper()
    for data in [{"p-text": " hi ", "p-enabled": "false", "p-tags": ["a", "b"]},
                 {"p-text": "too long", "p-tags": ["missing"]}, {}]:
        native = ValueForm(data, prefix="p")
        actual = ValueForm(data, prefix="p")
        actual._clean_fields = lambda: validate_publication_input_fields(actual)
        assert actual.is_valid() == native.is_valid()
        assert actual.errors.as_json() == native.errors.as_json()
        assert actual.cleaned_data == native.cleaned_data
