import uuid
from datetime import timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core.agencies import person_queryset
from apps.core.verification import locked_manager_person

from .models import LifecycleAction, Listing
from .moderation import unresolved_matches
from .submissions import validate_submission


class ActionForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("pause", "Pausar / Pause"),
            ("resume", "Reanudar / Resume"),
            ("renew", "Renovar / Renew"),
            ("withdraw", "Retirar / Withdraw"),
            ("available", "Disponible ahora / Available now"),
            ("unavailable", "Cancelar disponibilidad / Cancel availability"),
        ]
    )
    confirm = forms.BooleanField(
        required=False,
        label="Confirmo que los datos aprobados siguen siendo correctos / I confirm approved information is still correct",
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        index = 1 if language == "en" else 0
        labels = {
            "operation": ("Operación", "Operation"),
            "confirm": (
                "Confirmo que los datos aprobados siguen siendo correctos",
                "I confirm approved information is still correct",
            ),
        }
        for name, translations in labels.items():
            self.fields[name].label = translations[index]
        choices = {
            "operation": [
                ("pause", ("Pausar", "Pause")),
                ("resume", ("Reanudar", "Resume")),
                ("renew", ("Renovar", "Renew")),
                ("withdraw", ("Retirar", "Withdraw")),
                ("available", ("Disponible ahora", "Available now")),
                ("unavailable", ("Cancelar disponibilidad", "Cancel availability")),
            ]
        }
        for name, options in choices.items():
            self.fields[name].choices = [
                (value, translations[index]) for value, translations in options
            ]


@transaction.atomic
def act(user, listing_id, key, version, operation, confirm=False):
    initial = Listing.objects.get(pk=listing_id)
    person = locked_manager_person(user, initial.person_id)
    listing = Listing.objects.select_for_update().get(pk=listing_id)
    previous = LifecycleAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.listing_id == listing.pk
            and previous.actor_id == user.pk
            and previous.manager_version == person.manager_version
            and previous.expected_version == version
            and previous.operation == operation
            and previous.confirmed == confirm
        ):
            return listing
        raise ValidationError("Action key conflict / Clave de acción incompatible")
    if listing.lifecycle_version != version:
        raise ValidationError("Publication changed; reload / Publicación cambiada; recarga")
    now = timezone.now()
    old_status = listing.status
    if operation in {"resume", "renew", "available"}:
        revision = listing.approved_revision
        if not revision or revision.status != "approved" or revision.listing_id != listing.pk:
            raise ValidationError("Approved revision required / Revisión aprobada obligatoria")
        validate_submission(revision, person)
        if unresolved_matches(revision).exists():
            raise ValidationError("Photo review pending / Revisión de fotografía pendiente")
    if operation == "pause" and listing.status == "published":
        listing.status = "paused"
        listing.available_until = None
    elif (
        operation == "resume"
        and listing.status == "paused"
        and listing.expires_at
        and listing.expires_at > now
    ):
        listing.status = "published"
    elif operation == "renew" and listing.status in {"published", "paused", "expired"}:
        if not confirm or not listing.expires_at or listing.expires_at > now + timedelta(days=7):
            raise ValidationError(
                "Confirm data; renewal opens seven days before expiry / Confirma los datos; renovación desde siete días antes de caducar"
            )
        listing.expires_at = now + timedelta(days=30)
        listing.published_at = now
        listing.available_until = None
        if listing.status == "expired":
            listing.status = "published"
    elif operation == "withdraw" and listing.status != "withdrawn":
        listing.revisions.filter(
            manager_version=person.manager_version, status__in=["draft", "processing", "pending"]
        ).update(status="withdrawn")
        listing.status = "withdrawn"
        listing.available_until = None
    elif (
        operation == "available"
        and listing.status == "published"
        and listing.expires_at
        and listing.expires_at > now
    ):
        listing.available_until = now + timedelta(hours=4)
    elif operation == "unavailable" and listing.status == "published":
        listing.available_until = None
    else:
        raise ValidationError(
            "Action unavailable in this state / Acción no disponible en este estado"
        )
    listing.lifecycle_version += 1
    listing.save(
        update_fields=[
            "status",
            "available_until",
            "expires_at",
            "published_at",
            "lifecycle_version",
        ]
    )
    LifecycleAction.objects.create(
        key=key,
        listing=listing,
        actor=user,
        approved_revision=listing.approved_revision,
        manager_version=person.manager_version,
        expected_version=version,
        confirmed=confirm,
        operation=operation,
        previous_status=old_status,
        resulting_status=listing.status,
    )
    return listing


@login_required
@require_http_methods(["GET", "POST"])
def panel(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, person__in=person_queryset(request.user))
    form = ActionForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid.uuid4(), "version": listing.lifecycle_version},
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            act(
                request.user,
                listing.pk,
                form.cleaned_data["key"],
                form.cleaned_data["version"],
                form.cleaned_data["operation"],
                form.cleaned_data["confirm"],
            )
        except PermissionDenied:
            return HttpResponse("Forbidden", status=403)
        except (ValidationError, IntegrityError) as error:
            form.add_error(
                None,
                error
                if isinstance(error, ValidationError)
                else "Action key conflict / Clave de acción incompatible",
            )
            status = 409
        else:
            response = redirect("listing_lifecycle", listing_id=listing.pk)
            response["Cache-Control"] = "private, no-store"
            return response
    response = render(
        request,
        "listings/lifecycle.html",
        {
            "listing": listing,
            "form": form,
            "events": listing.lifecycle_actions.filter(
                manager_version=listing.person.manager_version
            ).order_by("-created_at", "-pk")[:20],
        },
        status=status,
    )
    response["Cache-Control"] = "private, no-store"
    return response
