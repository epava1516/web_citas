"""Audited recipient candidates; role history is not proof of actual disclosure."""

import json

# HTTP access only exposes an audited summary; recipient references stay encrypted.
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import RepresentationAction
from apps.listings.models import Revision, Submission

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsRectificationExecution,
    RightsRectificationManagerNotice,
    RightsRectificationRecipientInventory,
    RightsRequest,
)
from .rectification_review import permission
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read
from .views import private


@sensitive_variables()
def snapshot(person, execution):
    candidates = {}

    def add(kind, reference, basis, evidence):
        if kind not in {"individual", "agency", "account"} or not reference:
            return
        key = kind, str(reference)
        candidate = candidates.setdefault(
            key, {"kind": kind, "reference": str(reference), "evidence": []}
        )
        candidate["evidence"].append({"basis": basis, "record": str(evidence)})

    add(
        "agency" if person.agency_id else "individual",
        person.agency_id or person.individual_id,
        "current_manager",
        person.pk,
    )
    for row in RepresentationAction.objects.filter(person=person).order_by("pk"):
        add(row.manager_kind, row.manager_id, "representation_history", row.pk)
        add(row.previous_manager_kind, row.previous_manager_id, "previous_representation", row.pk)
    for row in Submission.objects.filter(revision__listing__person=person).order_by("pk"):
        add("account", row.actor_id, "submission_actor", row.pk)
    for row in (
        Revision.objects.filter(listing__person=person, publisher_acceptance__isnull=False)
        .select_related("publisher_acceptance")
        .order_by("pk")
    ):
        add(
            "account",
            row.publisher_acceptance.user_id,
            "publishing_acceptance",
            row.publisher_acceptance_id,
        )
    notices = list(
        RightsRectificationManagerNotice.objects.filter(execution=execution)
        .order_by("pk")
        .values("pk", "recipient_id", "manager_version", "acknowledged_at")
    )
    # A notice identifies a concrete account, even if no publishing action exists.
    # This evidence proves only that an internal notice was created, not that the
    # account previously received the corrected personal data.
    for notice in notices:
        add("account", notice["recipient_id"], "internal_correction_notice", notice["pk"])
    data = {
        "candidates": [candidates[key] for key in sorted(candidates)],
        "manager_notices": notices,
        "complete": False,
        "pending": [
            "actual_disclosures_and_recipient_scope_review",
            "historical_editor_access_without_assignment_history",
            "public_audience_and_reuse_without_identified_recipients",
            "processors_and_external_destinations_register",
            "historical_recipient_contact_authorization_and_delivery",
        ],
        "person": str(person.pk),
        "manager_version": person.manager_version,
        "rights_version": person.rights_version,
        "execution": execution.pk,
    }
    return json.loads(json.dumps(data, sort_keys=True, default=str))


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, execution_id, key, version, purpose):
    permission(user)
    case, person, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    signature = fingerprint(
        json.dumps(
            {"execution": execution_id, "version": version, "purpose": purpose}, sort_keys=True
        )
    )
    execution = RightsRectificationExecution.objects.filter(
        pk=execution_id,
        notification__review__proposal__action__request=case,
        notification__review__proposal__person=person,
    ).first()
    if (
        not execution
        or case.kind != "rectify"
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or case.version != version
        or not complete_read(user, case)
        or not complete_response_read(user, case)
        or not 10 <= len(purpose.strip()) <= 200
        or execution.resulting_rights_version != person.rights_version
    ):
        raise ValidationError(
            "Inspect current executed correction / Consulta la rectificación ejecutada vigente"
        )
    proof = authorized_proof(case, person, "rectify")
    if proof.created_at <= execution.created_at:
        raise ValidationError(
            "Fresh post-execution proof required / Nueva comprobación posterior a ejecución obligatoria"
        )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "rectify_recipients"
            and previous.payload_digest == signature
        ):
            return RightsRectificationRecipientInventory.objects.get(action=previous)
        raise ValidationError("Conflicting inventory key / Clave incompatible")
    data = snapshot(person, execution)
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="rectify_recipients",
                payload_digest=signature,
                encrypted_reason=seal({"purpose": purpose}),
            )
            return RightsRectificationRecipientInventory.objects.create(
                execution=execution,
                action=action,
                proof=proof,
                source_digest=fingerprint(json.dumps(data, sort_keys=True)),
                encrypted_inventory=seal(data),
            )
    except IntegrityError as error:
        raise ValidationError(
            "Conflicting recipient inventory / Inventario incompatible"
        ) from error


class InventoryForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    purpose = forms.CharField(
        min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )


@login_required
@sensitive_post_parameters("purpose")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare_view(request, case_id, execution_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    try:
        permission(request.user)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    execution = (
        RightsRectificationExecution.objects.filter(
            pk=execution_id, notification__review__proposal__action__request=case
        )
        .only("pk")
        .first()
    )
    if not case or not execution:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = InventoryForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    data = None
    record = None
    status = 200 if request.method == "GET" else 400
    if request.method == "POST" and form.is_valid():
        try:
            values = form.cleaned_data
            record = prepare(
                request.user,
                case.pk,
                execution.pk,
                values["key"],
                values["version"],
                values["purpose"],
            )
            data = unseal(record.encrypted_inventory)
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/rectification_recipients.html",
            {"form": form, "inventory": data, "record": record, "case": case},
            status=status,
        )
    )
