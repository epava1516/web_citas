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
