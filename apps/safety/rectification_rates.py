"""Replace a complete tariff table using the existing listing form rules."""

from django.core.exceptions import ValidationError
from django.forms import formset_factory
from django.views.decorators.debug import sensitive_variables

from apps.listings.forms import RateForm

Editor = formset_factory(
    RateForm, extra=1, max_num=10, absolute_max=11, validate_max=True, can_delete=True
)


@sensitive_variables()
def validate(value):
    fields = {"concept", "mode", "amount", "currency", "duration_minutes"}
    if not isinstance(value, list) or len(value) > 10:
        raise ValidationError("At most ten rates / Máximo diez tarifas")
    normalized = []
    for row in value:
        if (
            not isinstance(row, dict)
            or set(row) != fields
            or not isinstance(row["concept"], str)
            or not isinstance(row["mode"], str)
            or row["currency"] != "EUR"
            or (row["amount"] is not None and not isinstance(row["amount"], str))
            or (row["duration_minutes"] is not None and type(row["duration_minutes"]) is not int)
        ):
            raise ValidationError("Invalid rate fields / Campos de tarifa no válidos")
        form = RateForm({key: val for key, val in row.items() if key != "currency"})
        if not form.is_valid():
            raise ValidationError("Invalid rate values / Valores de tarifa no válidos")
        cleaned = form.cleaned_data
        normalized.append(
            {
                "concept": cleaned["concept"],
                "mode": cleaned["mode"],
                "amount": format(cleaned["amount"], ".2f")
                if cleaned["amount"] is not None
                else None,
                "currency": "EUR",
                "duration_minutes": cleaned["duration_minutes"],
            }
        )
    return normalized


@sensitive_variables()
def source(revision):
    return [
        {
            "concept": row.concept,
            "mode": row.mode,
            "amount": format(row.amount, ".2f") if row.amount is not None else None,
            "currency": row.currency,
            "duration_minutes": row.duration_minutes,
        }
        for row in revision.rates.order_by("pk")
    ]


@sensitive_variables()
def changes(editor):
    return validate(
        [
            {
                "concept": row["concept"],
                "mode": row["mode"],
                "amount": format(row["amount"], ".2f") if row["amount"] is not None else None,
                "currency": "EUR",
                "duration_minutes": row["duration_minutes"],
            }
            for row in editor.cleaned_data
            if row and not row.get("DELETE")
        ]
    )


@sensitive_variables()
def display(value, english=False):
    labels = {
        "fixed": "Fixed" if english else "Fijo",
        "from": "From" if english else "Desde",
        "consult": "Consult" if english else "Consultar",
    }
    return "\n".join(
        " · ".join(
            [row["concept"], labels[row["mode"]]]
            + ([row["amount"] + " EUR"] if row["amount"] else [])
            + ([str(row["duration_minutes"]) + " min"] if row["duration_minutes"] else [])
        )
        for row in value
    ) or ("No rates specified" if english else "Sin tarifas indicadas")
