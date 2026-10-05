"""Subject account source and correction validation; never mutates credentials."""

from django import forms
from django.core.exceptions import ValidationError
from django.db import connection
from django.views.decorators.debug import sensitive_variables

from apps.core.accounts import token_user_state
from apps.core.models import User

FIELDS = {"first_name", "last_name", "email"}


def locked_subject(person):
    if not connection.in_atomic_block:
        raise RuntimeError("Account source requires scope locks and an enclosing transaction")
    if not person or not person.subject_id:
        raise ValidationError(
            "Linked subject account required / Cuenta del sujeto vinculada obligatoria"
        )
    user = User.objects.select_for_update().get(pk=person.subject_id)
    if user.account_erased_at:
        raise ValidationError("Subject account erased / Cuenta del sujeto suprimida")
    return user


@sensitive_variables()
def source(person):
    user = locked_subject(person)
    return {
        "subject": str(user.pk),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "email_verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None,
        "is_active": user.is_active,
        "session_version": user.session_version,
        "mfa_version": user.mfa_version,
        "authentication_digest": token_user_state(user),
    }


@sensitive_variables()
def validate(value, person):
    if not isinstance(value, dict) or not value or set(value) - FIELDS:
        raise ValidationError("Invalid account correction / Corrección de cuenta no válida")
    user = locked_subject(person)
    result = {}
    for field, text in value.items():
        if not isinstance(text, str):
            raise ValidationError("Invalid account value / Valor de cuenta no válido")
        if field == "email":
            text = forms.EmailField(max_length=254).clean(text).strip().lower()
            if User.objects.filter(email__iexact=text).exclude(pk=user.pk).exists():
                raise ValidationError(
                    "Account correction unavailable / Corrección de cuenta no disponible"
                )
        else:
            text = forms.CharField(required=False, max_length=150).clean(text)
        result[field] = text
    return result


@sensitive_variables()
def apply(person, proposal, value):
    """Apply only after the caller validates review, receipt and fresh scoped proof."""
    from django.utils import timezone

    from apps.core.models import AccountToken

    from .models import RightsAccountEmailConfirmation
    from .rights import fingerprint

    user = locked_subject(person)
    changes = validate(value, person)
    previous = {field: getattr(user, field) for field in changes}
    changed_email = "email" in changes and changes["email"] != user.email.lower()
    confirmation = None
    now = timezone.now()
    if changed_email:
        from .account_email_confirmation import enabled

        if not enabled():
            raise ValidationError("Account confirmation delivery disabled")
        confirmation = (
            RightsAccountEmailConfirmation.objects.select_for_update()
            .filter(
                proposal=proposal,
                subject=user,
                revoked_at__isnull=True,
                consumed_at__isnull=True,
                confirmed_at__isnull=False,
            )
            .order_by("-created_at", "-pk")
            .first()
        )
        if (
            not confirmation
            or confirmation.expires_at <= now
            or confirmation.proof.status != "passed"
            or confirmation.source_digest != proposal.source_digest
            or confirmation.destination_digest != fingerprint(changes["email"])
        ):
            raise ValidationError(
                "Current destination confirmation required / Confirmación vigente del destino obligatoria"
            )
    for field, text in changes.items():
        setattr(user, field, text)
    updated = set(changes)
    if changed_email:
        user.email_verified_at = confirmation.confirmed_at
        user.session_version += 1
        updated.update({"email_verified_at", "session_version"})
    user.save(update_fields=sorted(updated))
    if changed_email:
        AccountToken.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
        confirmation.consumed_at = now
        confirmation.encrypted_delivery = ""
        confirmation.save(update_fields=["consumed_at", "encrypted_delivery"])
    return previous


def display(value, english=False):
    """Human labels for an already authorized projection; never include technical fields."""
    labels = {
        "first_name": "First name" if english else "Nombre",
        "last_name": "Last name" if english else "Apellidos",
        "email": "Email" if english else "Correo electrónico",
    }
    empty = "(empty)" if english else "(vacío)"
    return "\n".join(
        f"{label}: {value[field] or empty}" for field, label in labels.items() if field in value
    )
