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
    "Conflicting inspection key": ("Clave de consulta incompatible", "Conflicting inspection key"),
    "Copy inspection source changed": (
        "Origen de la consulta de copia cambiado",
        "Copy inspection source changed",
    ),
    "Inspect the first page before continuing": (
        "Consulta primero la primera página antes de continuar",
        "Inspect the first page before continuing",
    ),
    "Inspection page unavailable": (
        "Página de consulta no disponible",
        "Inspection page unavailable",
    ),
    "Invalid copy inspection page": (
        "Página de consulta de copia no válida",
        "Invalid copy inspection page",
    ),
    "Invalid or expired inspection cursor": (
        "Cursor de consulta no válido o caducado",
        "Invalid or expired inspection cursor",
    ),
    "Request changed": ("Solicitud cambiada", "Request changed"),
    "Conflicting review access key": (
        "Clave de acceso a revisión incompatible",
        "Conflicting review access key",
    ),
    "Invalid review access purpose": (
        "Motivo de acceso a revisión no válido",
        "Invalid review access purpose",
    ),
    "Page review evidence changed": (
        "Evidencia de revisión de página cambiada",
        "Page review evidence changed",
    ),
    "Page review source changed": (
        "Origen de revisión de página cambiado",
        "Page review source changed",
    ),
    "Page review unavailable": ("Revisión de página no disponible", "Page review unavailable"),
    "Conflicting page review": ("Revisión de página incompatible", "Conflicting page review"),
    "Conflicting page review key": (
        "Clave de revisión de página incompatible",
        "Conflicting page review key",
    ),
    "Inspect the current page first": (
        "Consulta primero la página actual",
        "Inspect the current page first",
    ),
    "Inspection evidence unavailable": (
        "Evidencia de consulta no disponible",
        "Inspection evidence unavailable",
    ),
    "Inspection source changed": ("Origen de consulta cambiado", "Inspection source changed"),
    "Invalid inspection evidence": (
        "Evidencia de consulta no válida",
        "Invalid inspection evidence",
    ),
    "Invalid page review": ("Revisión de página no válida", "Invalid page review"),
    "Page review version changed": (
        "Versión de revisión de página cambiada",
        "Page review version changed",
    ),
    "Page unavailable": ("Página no disponible", "Page unavailable"),
    "Invalid reviewed page": ("Página revisada no válida", "Invalid reviewed page"),
    "Invalid reviewed header": ("Cabecera revisada no válida", "Invalid reviewed header"),
    "This section is immutable": (
        "Esta sección no admite modificaciones",
        "This section is immutable",
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
