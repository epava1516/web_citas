"""Dependencies of successful request-local contact cleaning, never authority."""

from django import forms
from django.core.validators import MaxLengthValidator, ProhibitNullCharactersValidator
from django.db import models
from django.forms import models as form_models

from . import forms as listing_forms
from .forms import ContactsForm
from .models import Revision


def function_token(function):
    function = getattr(function, "__func__", function)
    while getattr(function, "_publication_dependency_wrapper", None) is function:
        function = function._publication_dependency_original
        function = getattr(function, "__func__", function)
    return function


FORM_METHODS = {
    name: function_token(getattr(ContactsForm, name))
    for name in ["__init__", "is_valid", "full_clean", "_clean_fields", "_clean_form",
                 "_post_clean", "_get_validation_exclusions", "validate_unique", "clean",
                 "clean_telegram", "add_error"]
}
MODEL_METHODS = {
    name: function_token(getattr(Revision, name))
    for name in ["full_clean", "clean_fields", "clean", "validate_unique", "validate_constraints"]
}
CONSTRUCT_INSTANCE = function_token(form_models.construct_instance)
NORMALIZE_TELEGRAM = function_token(listing_forms.normalize_telegram)
MODEL_NAMES = ("whatsapp", "telegram", "contact_exposure_accepted")
INPUT_NAMES = (*MODEL_NAMES, "accept_publishing", "legal_version")


def form_methods_supported():
    return (
        all(function_token(getattr(ContactsForm, name)) is expected
            for name, expected in FORM_METHODS.items())
        and function_token(form_models.construct_instance) is CONSTRUCT_INSTANCE
        and function_token(listing_forms.normalize_telegram) is NORMALIZE_TELEGRAM
        and all(not hasattr(ContactsForm, "clean_" + name)
                for name in INPUT_NAMES if name != "telegram")
        and ContactsForm._meta.model is Revision
        and tuple(ContactsForm._meta.fields) == MODEL_NAMES
        and ContactsForm._meta.exclude is None
    )


# Only the actual native classes/operations used by this form are audited.
FORM_FIELD_METHODS = {
    cls: {name: function_token(getattr(cls, name))
          for name in ["clean", "to_python", "validate", "run_validators", "_clean_bound_field"]}
    for cls in [forms.CharField, forms.BooleanField]
}
MODEL_FIELD_METHODS = {
    cls: {name: function_token(getattr(cls, name))
          for name in ["clean", "to_python", "validate", "run_validators", "save_form_data"]}
    for cls in [models.CharField, models.BooleanField]
}
WIDGET_METHODS = {
    cls: {name: function_token(getattr(cls, name))
          for name in ["value_from_datadict", "value_omitted_from_data"]}
    for cls in [forms.TextInput, forms.HiddenInput, forms.CheckboxInput]
}
VALIDATOR_METHODS = {
    cls: {name: function_token(getattr(cls, name))
          for name in (["__call__", "clean", "compare"] if cls is MaxLengthValidator
                       else ["__call__"])}
    for cls in [MaxLengthValidator, ProhibitNullCharactersValidator]
}


def validator_signature(validators):
    signature = []
    for validator in validators:
        cls = type(validator)
        if (cls not in VALIDATOR_METHODS
                or any(function_token(getattr(validator, name)) is not expected
                       for name, expected in VALIDATOR_METHODS[cls].items())):
            return None
        if cls is MaxLengthValidator:
            if type(validator.limit_value) is not int:
                return None
            signature.append((cls, validator.limit_value))
        else:
            signature.append((cls,))
    return tuple(signature)


def form_fields_signature(fields):
    if set(fields) != set(INPUT_NAMES):
        return None
    result = []
    for name in INPUT_NAMES:
        field = fields[name]
        cls, widget_cls = type(field), type(field.widget)
        if (cls not in FORM_FIELD_METHODS or widget_cls not in WIDGET_METHODS
                or field.disabled
                or any(function_token(getattr(field, method)) is not expected
                       for method, expected in FORM_FIELD_METHODS[cls].items())
                or any(function_token(getattr(field.widget, method)) is not expected
                       for method, expected in WIDGET_METHODS[widget_cls].items())):
            return None
        validators = validator_signature(field.validators)
        if validators is None:
            return None
        # Label/help/error text changes cannot change a successful value. Errors
        # are never cached. Empty-values behavior and widget extraction are fixed
        # to these audited native definitions, including None/blank semantics.
        if field.empty_values != forms.Field.empty_values:
            return None
        result.append((name, cls, widget_cls, field.required, validators,
                       getattr(field, "strip", None), getattr(field, "empty_value", None)))
    return tuple(result)


def model_signature(revision):
    if (type(revision) is not Revision or revision._meta is not Revision._meta
            or revision._state.adding or revision._meta.constraints
            or revision._meta.unique_together
            or any(function_token(getattr(revision, name)) is not expected
                   for name, expected in MODEL_METHODS.items())):
        return None
    result = []
    for name in MODEL_NAMES:
        field = revision._meta.get_field(name)
        cls = type(field)
        if (cls not in MODEL_FIELD_METHODS or field.generated or field.unique or field.choices
                or field.unique_for_date or field.unique_for_month or field.unique_for_year
                or any(function_token(getattr(field, method)) is not expected
                       for method, expected in MODEL_FIELD_METHODS[cls].items())):
            return None
        validators = validator_signature(field.validators)
        if validators is None:
            return None
        result.append((name, cls, field.blank, field.null, field.editable, validators))
    return tuple(result)


def contact_success_key(prototype, data, revision, language):
    if (type(data) is not dict or set(data) != set(INPUT_NAMES)
            or prototype.empty_permitted or prototype.prefix is not None):
        return None
    fields = form_fields_signature(prototype.fields)
    model = model_signature(revision)
    if fields is None or model is None:
        return None
    inputs = []
    for name in INPUT_NAMES:
        value = data[name]
        if value is not None and type(value) not in (str, bool, int):
            return None
        inputs.append((name, type(value), value))
    # Prototype identity fixes the request-owned definitions/catalog. All model
    # fields outside Meta.fields are excluded by native ModelForm; no custom
    # model clean/constraints/unique or unknown callable is allowed here.
    return (id(prototype), language, revision._state.db, fields, model, tuple(inputs))
