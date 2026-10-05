"""Persistent precaution over publication; not a complete Article 18 disposition."""

import json
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .crypto import seal
from .models import PrivacyPublicationHold, RightsAction, RightsRequest
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_profile_case as locked_case
from .rights_scope import permitted
from .rights_verification import authorized_proof, complete_read
from .views import private

GROUNDS = {
    "accuracy": "Exactitud en revisión / Accuracy under review",
    "preservation": "Conservación solicitada / Preservation requested",
    "claims": "Conservación para reclamaciones / Preservation for claims",
    "objection_pending": "Oposición en revisión / Objection under review",
}


@transaction.atomic
@sensitive_variables()
def hold(user, case_id, key, version, reason, ground):
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
    ):
        raise PermissionDenied
    case, person, listing = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    signature = fingerprint(
        json.dumps({"version": version, "reason": reason, "ground": ground}, sort_keys=True)
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "publication_hold"
            and previous.payload_digest == signature
        ):
            return PrivacyPublicationHold.objects.get(action=previous)
        raise ValidationError("Conflicting action key / Clave incompatible")
    if (
        case.version != version
        or case.assigned_to_id != user.pk
        or case.status != "reviewing"
        or case.kind not in {"restriction", "object", "rectify"}
        or ground not in GROUNDS
        or (case.kind == "object" and ground != "objection_pending")
        or (case.kind == "rectify" and ground != "accuracy")
        or not 20 <= len(reason.strip()) <= 2000
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect the assigned current request and ground / Consulta la solicitud asignada actual y el motivo"
        )
    proof = authorized_proof(case, person, case.kind)
    if PrivacyPublicationHold.objects.filter(action__request=case).exists():
        raise ValidationError("Request already has a hold / Solicitud ya tiene medida")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="publication_hold",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = PrivacyPublicationHold.objects.create(
                action=action,
                proof=proof,
                person=person,
                subject_snapshot=str(person.subject_id or ""),
                manager_version=person.manager_version,
                ground=ground,
                previous_listing_status=listing.status if listing else "",
                previous_lifecycle_version=listing.lifecycle_version if listing else None,
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error
    if listing:
        if listing.status == "published":
            listing.status = "paused"
        listing.available_until = None
        listing.lifecycle_version += 1
        listing.save(update_fields=["status", "available_until", "lifecycle_version"])
    case.version += 1
    case.scope_status = "unverified"
    # The broader rights request remains open; publication is only one processing purpose.
    case.save(update_fields=["version", "scope_status"])
    return result


class HoldForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    ground = forms.ChoiceField(
        choices=list(GROUNDS.items()), label="Fundamento revisado / Reviewed ground"
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo interno minimizado / Minimized internal reason",
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def apply(request, case_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if case.kind not in {"restriction", "object", "rectify"}:
        return private(HttpResponse("Unsupported request type", status=409))
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = HoldForm(request.POST or None, initial={"key": uuid.uuid4(), "version": case.version})
    if case.kind in {"object", "rectify"}:
        ground = "objection_pending" if case.kind == "object" else "accuracy"
        form.fields["ground"].choices = [(ground, GROUNDS[ground])]
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            hold(request.user, case.pk, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("rights_inspect", case_id=case.pk))
    existing = PrivacyPublicationHold.objects.filter(action__request=case).first()
    return private(
        render(
            request,
            "safety/privacy_hold.html",
            {"case": case, "form": form, "hold": existing},
            status=status,
        )
    )
