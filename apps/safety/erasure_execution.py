"""Actual local deletion of reviewed scopes; broader erasure remains open."""

import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, models, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import AccountToken, RecoveryCode, User
from apps.listings.models import Favorite, Listing, Rate, Revision

from .crypto import seal, unseal
from .erasure_inventory import canonical
from .erasure_plans import authorized_inventory
from .models import (
    ErasureExecution,
    ErasurePlan,
    RightsAction,
    RightsExport,
    RightsExportImage,
    RightsRequest,
)
from .rights import allowed, fingerprint
from .rights_scope import locked_case, permitted
from .views import private

SUPPORTED = [
    ("profile", "Alias público / Public alias"),
    ("publication", "Contenido de anuncio / Listing content"),
    ("authentication", "Tokens, códigos y sesiones / Tokens, codes and sessions"),
    ("account_preferences", "Favoritos propios / Own favorites"),
    ("transient_copy", "Contenido de copias transitorias / Transient copy contents"),
]


@transaction.atomic
@sensitive_variables()
def execute(user, case_id, plan_id, key, version, purposes, reason, confirmed):
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
    ):
        raise PermissionDenied
    case, person, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    if (
        not isinstance(purposes, list)
        or not purposes
        or any(not isinstance(value, str) for value in purposes)
        or len(purposes) != len(set(purposes))
        or not set(purposes) <= {value for value, _ in SUPPORTED}
    ):
        raise ValidationError("Select supported scopes / Selecciona ámbitos implementados")
    if "profile" in purposes and "publication" not in purposes:
        raise ValidationError(
            "Erase publication together with profile / Suprime publicación junto al perfil"
        )
    signature = fingerprint(
        canonical(
            {
                "plan": str(plan_id),
                "version": version,
                "purposes": sorted(purposes),
                "reason": reason,
                "confirmed": confirmed,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "erasure_execute"
            and previous.payload_digest == signature
        ):
            return ErasureExecution.objects.get(action=previous)
        raise ValidationError("Conflicting action key / Clave incompatible")
    if (
        case.version != version
        or confirmed is not True
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError(
            "Confirm current scoped execution / Confirma ejecución del ámbito actual"
        )
    plan = ErasurePlan.objects.filter(pk=plan_id, action__request=case, action__actor=user).first()
    if (
        not plan
        or ErasureExecution.objects.filter(plan=plan).exists()
        or (plan.review_on and plan.review_on <= timezone.localdate())
    ):
        raise ValidationError(
            "Current unexecuted plan required / Plan vigente sin ejecutar obligatorio"
        )
    # Account writers lock User before tokens/codes. Favorite writers lock it after target Listing.
    subject = None
    if set(purposes) & {"authentication", "account_preferences"}:
        if not person or not person.subject_id:
            raise ValidationError(
                "Subject account unidentified / Cuenta del sujeto sin identificar"
            )
        subject = User.objects.select_for_update(no_key=True).get(pk=person.subject_id)
    exports = (
        list(RightsExport.objects.select_for_update().filter(person=person).order_by("pk"))
        if "transient_copy" in purposes
        else []
    )
    if exports:
        list(
            RightsExportImage.objects.select_for_update().filter(export__in=exports).order_by("pk")
        )
    revisions = (
        list(Revision.objects.select_for_update().filter(listing__person=person).order_by("pk"))
        if "publication" in purposes
        else []
    )
    inventory, _ = authorized_inventory(user, case, person, plan.inventory_id)
    if inventory.source_digest != plan.source_digest:
        raise ValidationError("Plan source changed / Fuente del plan cambiada")
    decisions = unseal(plan.encrypted_decisions)
    approved = {row["purpose"] for row in decisions["decisions"] if row["operation"] == "erase"}
    if not set(purposes) <= approved:
        raise ValidationError(
            "Each selected purpose must be reviewed for erasure / Cada finalidad seleccionada debe decidir supresión"
        )
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="erasure_execute",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = {
                "schema": "erasure-execution-v1",
                "executed_purposes": sorted(purposes),
                "pending_purposes": sorted(
                    {row["purpose"] for row in decisions["decisions"]} - set(purposes)
                ),
                "partial": True,
                "identity_simulated": True,
                "tokens_deleted": 0,
                "recovery_codes_deleted": 0,
                "favorites_deleted": 0,
                "copies_cleared": 0,
                "images_cleared": 0,
                "sessions_revoked": False,
                "revisions_cleared": 0,
                "rates_deleted": 0,
                "profile_alias_cleared": False,
            }
            if "publication" in purposes:
                ids = [revision.pk for revision in revisions]
                result["revisions_cleared"] = len(ids)
                result["rates_deleted"] = Rate.objects.filter(revision_id__in=ids).count()
                Rate.objects.filter(revision_id__in=ids).delete()
                for revision in revisions:
                    revision.categories.clear()
                    revision.services.clear()
                    revision.travel_areas.clear()
                Revision.objects.filter(pk__in=ids).update(
                    status="withdrawn",
                    edit_version=models.F("edit_version") + 1,
                    title="",
                    description="",
                    description_alternative="",
                    profile_type="",
                    municipality=None,
                    postal_code=None,
                    zone=None,
                    spoken_languages=[],
                    days=[],
                    time_slot="",
                    reception=False,
                    travel=False,
                    phone="",
                    whatsapp=False,
                    telegram="",
                    contact_exposure_accepted=False,
                    updated_at=timezone.now(),
                )
                Listing.objects.filter(person=person).update(
                    status="withdrawn",
                    approved_revision=None,
                    available_until=None,
                    published_at=None,
                    expires_at=None,
                    lifecycle_version=models.F("lifecycle_version") + 1,
                )
                person.publication_erased_at = timezone.now()
                person.save(update_fields=["publication_erased_at"])
            if "profile" in purposes:
                person.alias = ""
                person.assigned_editor = None
                person.save(update_fields=["alias", "assigned_editor"])
                result["profile_alias_cleared"] = True
            if "authentication" in purposes:
                result["tokens_deleted"] = AccountToken.objects.filter(user=subject).count()
                result["recovery_codes_deleted"] = RecoveryCode.objects.filter(user=subject).count()
                AccountToken.objects.filter(user=subject).delete()
                RecoveryCode.objects.filter(user=subject).delete()
            if "account_preferences" in purposes:
                result["favorites_deleted"] = Favorite.objects.filter(user=subject).count()
                Favorite.objects.filter(user=subject).delete()
            if subject:
                subject.session_version += 1
                subject.mfa_version += 1
                subject.save(update_fields=["session_version", "mfa_version"])
                result["sessions_revoked"] = True
            if "transient_copy" in purposes:
                ids = [export.pk for export in exports if not export.purged_at]
                result["copies_cleared"] = len(ids)
                result["images_cleared"] = (
                    RightsExportImage.objects.filter(export_id__in=ids)
                    .exclude(encrypted_content="")
                    .count()
                )
                RightsExportImage.objects.filter(export_id__in=ids).update(encrypted_content="")
                RightsExport.objects.filter(pk__in=ids).update(
                    encrypted_payload="", purged_at=timezone.now()
                )
            record = ErasureExecution.objects.create(
                plan=plan,
                action=action,
                proof=inventory.proof,
                person=person,
                encrypted_result=seal(result),
            )
            person.rights_version += 1
            person.save(update_fields=["rights_version"])
            case.version += 1
            case.scope_status = "unverified"
            case.save(update_fields=["version", "scope_status"])
            return record
    except IntegrityError as error:
        raise ValidationError("Execution conflict / Conflicto de ejecución") from error


class ExecutionForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    purposes = forms.MultipleChoiceField(
        choices=SUPPORTED,
        widget=forms.CheckboxSelectMultiple,
        label="Ámbitos revisados para ejecutar / Reviewed scopes to execute",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo minimizado / Minimized reason",
    )
    confirmed = forms.BooleanField(
        label="Confirmo la ejecución parcial irreversible del ámbito / I confirm irreversible partial scoped execution"
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def apply(request, case_id, plan_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case or not ErasurePlan.objects.filter(pk=plan_id, action__request=case).exists():
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = ExecutionForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    result = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            execution = execute(request.user, case.pk, plan_id, **form.cleaned_data)
            result = unseal(execution.encrypted_result)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            status = 200
    return private(
        render(
            request,
            "safety/erasure_execution.html",
            {"case": case, "form": form, "result": result},
            status=status,
        )
    )
