"""Explicit static copy-operation captions; never split or translate caller data."""

from django.core.exceptions import ValidationError

_MESSAGES = {
    "Request changed or purpose required / Solicitud cambiada o motivo obligatorio": (
        "Solicitud cambiada o motivo obligatorio",
        "Request changed or purpose required",
    ),
    "Review every current section page first": (
        "Revisa primero todas las páginas de las secciones actuales",
        "Review every current section page first",
    ),
}


def operation_error(error, language):
    """Return unknown errors unchanged; retain known errors' code, params and grouping."""
    if hasattr(error, "error_dict"):
        values = {
            field: [operation_error(item, language) for item in items]
            for field, items in error.error_dict.items()
        }
        if all(
            new is old
            for field, items in values.items()
            for new, old in zip(items, error.error_dict[field])
        ):
            return error
        return ValidationError(values)
    if hasattr(error, "message"):
        pair = _MESSAGES.get(error.message) if isinstance(error.message, str) else None
        if pair is None or language not in {"es", "en"}:
            return error
        return ValidationError(pair[language == "en"], code=error.code, params=error.params)
    values = [operation_error(item, language) for item in error.error_list]
    if all(new is old for new, old in zip(values, error.error_list)):
        return error
    return ValidationError(values)
