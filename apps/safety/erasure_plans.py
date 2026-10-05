"""Per-purpose decisions bound to an audited inventory. No implicit execution."""

import uuid
from datetime import date, timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .crypto import seal, unseal
from .erasure_inventory import canonical, source_manifest
from .models import ErasureInventory, ErasurePlan, RightsAction, RightsRequest
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_profile_case as locked_case
from .rights_scope import permitted
from .rights_verification import authorized_proof, complete_read
from .views import private

OPERATIONS = [
    ("", "Selecciona / Select"),
    ("erase", "Suprimir / Erase"),
    ("redact", "Redactar ámbito / Redact scope"),
    ("retain", "Conservar con revisión / Retain with review"),
    ("review", "Pendiente de revisión / Awaiting review"),
]
LABELS = {
    "profile": "Perfil / Profile",
    "publication": "Publicación / Publication",
    "media": "Imágenes / Images",
    "account": "Cuenta del sujeto / Subject account",
    "authentication": "Tokens y recuperación / Tokens and recovery",
    "account_preferences": "Preferencias / Preferences",
    "contact": "Comprobación de contacto / Contact checks",
    "shared_contact_review": "Teléfono referenciado / Referenced phone",
    "representation": "Representación / Representation",
    "evidence": "Evidencias / Evidence",
    "dependent_evidence": "Dependencias de evidencia / Evidence dependencies",
    "third_party_evidence": "Expedientes con terceros / Cases with third parties",
    "transient_copy": "Copias transitorias / Transient copies",
}


@sensitive_variables()
def normalized_decisions(manifest, decisions):
    purposes = {item["purpose"] for item in manifest["entries"]}
    fields = {"purpose", "operation", "basis", "reason", "scope", "review_on"}
    if not isinstance(decisions, list) or len(decisions) != len(purposes):
        raise ValidationError("Review every purpose / Revisa todas las finalidades")
    seen = set()
    output = []
    today = timezone.localdate()
    for item in decisions:
        if not isinstance(item, dict) or set(item) != fields:
            raise ValidationError("Invalid decision structure / Estructura de decisión inválida")
        purpose = item["purpose"]
        if (
            not isinstance(purpose, str)
            or purpose not in purposes
            or purpose in seen
            or not isinstance(item["operation"], str)
            or item["operation"] not in {"erase", "redact", "retain", "review"}
        ):
            raise ValidationError("Invalid purpose or operation / Finalidad u operación inválida")
        seen.add(purpose)
        for field, maximum in [("basis", 1000), ("reason", 2000), ("scope", 1000)]:
            if not isinstance(item[field], str) or not 20 <= len(item[field].strip()) <= maximum:
                raise ValidationError(
                    "Record minimized basis, scope and reason / Registra fundamento, ámbito y motivo minimizados"
                )
        reviewed = item["review_on"]
        if item["operation"] in {"retain", "review"}:
            try:
                reviewed = date.fromisoformat(reviewed) if isinstance(reviewed, str) else reviewed
                if not isinstance(reviewed, date) or not today < reviewed <= today + timedelta(
                    days=365
                ):
                    raise ValueError
            except (TypeError, ValueError) as error:
                raise ValidationError(
                    "Review date must be within the next year / Revisión dentro del próximo año"
                ) from error
            reviewed = reviewed.isoformat()
        elif reviewed is not None and reviewed != "":
            raise ValidationError(
                "Review date only for retention or review / Fecha solo para conservación o revisión"
            )
        else:
            reviewed = None
        if item["operation"] == "erase" and (
            (purpose == "media" and any(row["shared_reference"] for row in manifest["media"]))
            or (purpose == "shared_contact_review" and manifest["shared_phone"])
            or (purpose == "account" and manifest["account_has_other_responsibilities"])
        ):
            raise ValidationError(
                "Shared resources require scoped review or redaction / Recursos compartidos requieren revisión de ámbito o redacción"
            )
        output.append(item | {"review_on": reviewed})
    return sorted(output, key=lambda item: item["purpose"])


@sensitive_variables()
def authorized_inventory(user, case, person, inventory_id):
    if (
        not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
        or not user.mfa_enabled
        or not permitted(user, case)
    ):
        raise PermissionDenied
    if (
        case.kind != "erase"
        or case.assigned_to_id != user.pk
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect assigned current erasure request / Consulta la solicitud asignada actual"
        )
    proof = authorized_proof(case, person, "erase")
    inventory = ErasureInventory.objects.filter(
        pk=inventory_id,
        action__request=case,
        action__actor=user,
        person=person,
        action__expected_version=case.version,
        proof=proof,
    ).first()
    if not inventory:
        raise ValidationError(
            "Prepare an authorized current inventory / Prepara un inventario autorizado actual"
        )
    manifest = unseal(inventory.encrypted_manifest)
    if (
        fingerprint(canonical(manifest)) != inventory.source_digest
        or fingerprint(canonical(source_manifest(person))) != inventory.source_digest
    ):
        raise ValidationError(
            "Resources changed; prepare and review again / Recursos cambiados; prepara y revisa de nuevo"
        )
    return inventory, manifest


@transaction.atomic
@sensitive_variables()
def record(user, case_id, inventory_id, key, version, decisions):
    case, person, _ = locked_case(case_id, lock_listing=True)
    if case.version != version:
        raise ValidationError("Request changed; reload / Solicitud cambiada; recarga")
    inventory, manifest = authorized_inventory(user, case, person, inventory_id)
    decisions = normalized_decisions(manifest, decisions)
    signature = fingerprint(
        canonical({"inventory": str(inventory.pk), "version": version, "decisions": decisions})
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "erasure_plan"
            and previous.payload_digest == signature
        ):
            return ErasurePlan.objects.get(action=previous)
        raise ValidationError("Conflicting action key / Clave incompatible")
    dates = [date.fromisoformat(item["review_on"]) for item in decisions if item["review_on"]]
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="erasure_plan",
                payload_digest=signature,
                encrypted_reason=seal(
                    {"reason": "Recorded per-purpose decisions; execution remains pending"}
                ),
            )
            return ErasurePlan.objects.create(
                inventory=inventory,
                action=action,
                source_digest=inventory.source_digest,
                encrypted_decisions=seal(
                    {"schema": "erasure-plan-v1", "decisions": decisions, "execution_ready": False}
                ),
                review_on=min(dates) if dates else None,
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error


class PlanForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class DecisionForm(forms.Form):
    purpose = forms.CharField(widget=forms.HiddenInput)
    operation = forms.ChoiceField(choices=OPERATIONS, label="Decisión / Decision")
    scope = forms.CharField(
        min_length=20,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Datos incluidos y excluidos / Included and excluded data",
    )
    basis = forms.CharField(
        min_length=20,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Fundamento revisado / Reviewed basis",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Motivo minimizado / Minimized reason",
    )
    review_on = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha de nueva revisión, no plazo legal de borrado / Next review date, not legal deletion deadline",
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id, inventory_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if (
        not case
        or not ErasureInventory.objects.filter(pk=inventory_id, action__request=case).exists()
    ):
        raise Http404
    try:
        with transaction.atomic():
            locked, person, _ = locked_case(case.pk, lock_listing=True)
            _, manifest = authorized_inventory(request.user, locked, person, inventory_id)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    except ValidationError:
        return private(
            HttpResponse(
                "Resources or evidence changed; prepare and review again / Recursos o evidencia cambiados; prepara y revisa de nuevo",
                status=409,
            )
        )
    purposes = sorted({entry["purpose"] for entry in manifest["entries"]})
    form = PlanForm(request.POST or None, initial={"key": uuid.uuid4(), "version": case.version})
    factory = forms.formset_factory(
        DecisionForm, extra=0, max_num=len(purposes), validate_max=True, absolute_max=20
    )
    formset = factory(
        request.POST or None,
        prefix="decisions",
        initial=[{"purpose": purpose} for purpose in purposes],
    )
    for decision, purpose in zip(formset.forms, purposes):
        decision.purpose_label = LABELS.get(purpose, purpose)
    result = None
    plan = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        try:
            plan = record(
                request.user,
                case.pk,
                inventory_id,
                decisions=formset.cleaned_data,
                **form.cleaned_data,
            )
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            result = True
            status = 200
    return private(
        render(
            request,
            "safety/erasure_plan.html",
            {"case": case, "form": form, "formset": formset, "recorded": result, "plan": plan},
            status=status,
        )
    )
