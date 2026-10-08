"""Language-only presentation for the correction proposal screen, not its native validators."""


def caption(value, language):
    if isinstance(value, str) and " / " in value:
        spanish, english = value.split(" / ", 1)
        return english if language == "en" else spanish
    return value


def proposal(form, language):
    for field in form.fields.values():
        field.label = caption(field.label, language)
        field.help_text = caption(field.help_text, language)
        # Model-backed choices retain their own labels, querysets and lazy evaluation.
        if hasattr(field, "choices") and not hasattr(field, "queryset"):
            field.choices = [(value, caption(label, language)) for value, label in field.choices]
    form.fields["operation"].label = "Operation" if language == "en" else "Operación"


def editors(rates, photos, language):
    english = language == "en"
    rate_labels = {
        "concept": ("Concepto", "Concept"),
        "mode": ("Modalidad", "Mode"),
        "amount": ("Importe", "Amount"),
        "duration_minutes": ("Duración en minutos", "Duration in minutes"),
        "DELETE": ("Eliminar", "Delete"),
    }
    modes = {
        "fixed": ("Fijo", "Fixed"),
        "from": ("Desde", "From"),
        "consult": ("Consultar", "Consult"),
    }
    for form in rates:
        for name, labels in rate_labels.items():
            form.fields[name].label = labels[english]
        form.fields["mode"].choices = [
            (value, modes[value][english] if value in modes else label)
            for value, label in form.fields["mode"].choices
        ]
    photo_labels = {
        "position": ("Orden", "Order"),
        "state": ("Estado", "State"),
        "DELETE": ("Eliminar", "Delete"),
    }
    # These source captions are English/Spanish, unlike the form's labels.
    states = {
        "Ready / Preparada": ("Preparada", "Ready"),
        "Failed / Fallida": ("Fallida", "Failed"),
        "Processing / Procesando": ("Procesando", "Processing"),
        "Unavailable / No disponible": ("No disponible", "Unavailable"),
    }
    for form in photos:
        for name, labels in photo_labels.items():
            form.fields[name].label = labels[english]
        original = form.initial.get("state")
        if original in states:
            form.initial["state"] = states[original][english]
