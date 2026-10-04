"""Actual local deletion of reviewed scopes; broader erasure remains open."""

import hashlib
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

from apps.core.models import (
    AccountToken,
    PhoneChallenge,
    RecoveryCode,
    RepresentationAction,
    RepresentationInvitation,
    User,
)
from apps.listings.models import Favorite, Listing, Rate, Revision
from apps.mediafiles.models import Blob, MediaErasure, Photo

from .crypto import seal, unseal
from .erasure_inventory import canonical
from .erasure_plans import authorized_inventory
from .models import (
    ErasureExecution,
    ErasurePlan,
    RightsAction,
    RightsExport,
    RightsExportImage,
    RightsExportPart,
    RightsRequest,
)
from .rights import allowed, fingerprint
from .rights_scope import locked_case, permitted
from .rights_verification import enabled
from .views import private

SUPPORTED = [
    ("account", "Identidad y acceso de cuenta / Account identity and access"),
    ("contact", "Desafíos de teléfono / Phone challenges"),
    ("representation", "Autorización e invitaciones / Authorization and invitations"),
    ("shared_contact_review", "Asociación al teléfono / Phone association"),
    ("media", "Archivos y huellas propios / Own files and fingerprints"),
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
    # Our own revocation changes manager_version while another identical request waits.
    # Re-read it under lock before replay; new executions still validate proof and source below.
    case, person, _ = locked_case(case_id, lock_listing=True, allow_version_change=True)
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
    if set(purposes) & {"account", "authentication", "account_preferences"}:
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
        if set(purposes) & {"publication", "shared_contact_review"}
        else []
    )
    if not enabled():
        raise ValidationError(
            "Identity and scope not established / Identidad y alcance no comprobados"
        )
    decisions = unseal(plan.encrypted_decisions)
    operations = {row["purpose"]: row["operation"] for row in decisions["decisions"]}
    media_redaction = "media" in purposes and operations.get("media") == "redact"
    media = []
    shared_ids = set()
    if "media" in purposes:
        blob_ids = Photo.objects.filter(revision__listing__person=person).values_list(
            "blob_id", flat=True
        )
        media = list(Blob.objects.select_for_update().filter(pk__in=blob_ids).order_by("pk"))
        for blob in media:
            if Photo.objects.filter(blob=blob).exclude(revision__listing__person=person).exists():
                shared_ids.add(blob.pk)
                if not media_redaction:
                    raise ValidationError(
                        "Shared image requires separate scoped review / Imagen compartida requiere revisión de ámbito"
                    )
        for blob in media:
            names = [value for value in [blob.original.name, blob.derivative.name] if value]
            if (
                names
                and Blob.objects.exclude(pk=blob.pk)
                .filter(models.Q(original__in=names) | models.Q(derivative__in=names))
                .exists()
            ):
                if not media_redaction:
                    raise ValidationError("Storage path shared / Ruta de almacenamiento compartida")
        list(
            Photo.objects.select_for_update()
            .filter(revision__listing__person=person)
            .order_by("pk")
        )
    inventory, manifest = authorized_inventory(user, case, person, plan.inventory_id)
    if "account" in purposes:
        if manifest["account_has_other_responsibilities"]:
            raise ValidationError(
                "Account has other responsibilities / Cuenta con otras responsabilidades"
            )
        if not {"authentication", "account_preferences"} <= set(purposes) or (
            "publication" not in purposes and not person.publication_erased_at
        ):
            raise ValidationError(
                "Review credentials, preferences and publication together / Revisa credenciales, preferencias y publicación conjuntamente"
            )
    if inventory.source_digest != plan.source_digest:
        raise ValidationError("Plan source changed / Fuente del plan cambiada")
    approved = {
        purpose
        for purpose, operation in operations.items()
        if operation == "erase" and purpose != "shared_contact_review"
    }
    if operations.get("shared_contact_review") == "redact":
        approved.add("shared_contact_review")
    if media_redaction:
        if not shared_ids:
            raise ValidationError(
                "No shared media to detach / No hay imágenes compartidas que desvincular"
            )
        approved.add("media")
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
                "parts_cleared": 0,
                "sessions_revoked": False,
                "revisions_cleared": 0,
                "rates_deleted": 0,
                "profile_alias_cleared": False,
                "media_jobs_queued": 0,
                "media_refs_detached": 0,
                "exclusive_media_pending": 0,
                "phone_challenges_deleted": 0,
                "representation_invitations_deleted": 0,
                "representation_revoked": False,
                "previous_manager_version": person.manager_version,
                "resulting_manager_version": person.manager_version,
                "phone_association_detached": False,
                "account_fields_cleared": False,
            }
            if "contact" in purposes:
                result["phone_challenges_deleted"] = PhoneChallenge.objects.filter(
                    person=person
                ).count()
                PhoneChallenge.objects.filter(person=person).delete()
            if "representation" in purposes:
                result["representation_invitations_deleted"] = (
                    RepresentationInvitation.objects.filter(person=person).count()
                )
                RepresentationInvitation.objects.filter(person=person).delete()
                person.consent_revoked_at = timezone.now()
                person.manager_version += 1
                case.manager_version = person.manager_version
                result["resulting_manager_version"] = person.manager_version
                person.age_status = "pending"
                person.save(update_fields=["consent_revoked_at", "manager_version", "age_status"])
                RepresentationAction.objects.create(
                    person=person,
                    subject=person.subject,
                    manager_version=person.manager_version,
                    action="revoke",
                )
                Listing.objects.filter(person=person).update(
                    status=models.Case(
                        models.When(status="published", then=models.Value("paused")),
                        default=models.F("status"),
                    ),
                    available_until=None,
                    lifecycle_version=models.F("lifecycle_version") + 1,
                )
                result["representation_revoked"] = True
            if "shared_contact_review" in purposes:
                person.phone_claim = None
                person.save(update_fields=["phone_claim"])
                Revision.objects.filter(listing__person=person).update(
                    phone="",
                    whatsapp=False,
                    edit_version=models.F("edit_version") + 1,
                    updated_at=timezone.now(),
                )
                Listing.objects.filter(person=person).update(
                    status=models.Case(
                        models.When(status="published", then=models.Value("paused")),
                        default=models.F("status"),
                    ),
                    available_until=None,
                    lifecycle_version=models.F("lifecycle_version") + 1,
                )
                result["phone_association_detached"] = True
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
            if "account" in purposes:
                marker = uuid.uuid4().hex
                subject.username = "erased-" + marker
                subject.email = marker + "@example.invalid"
                subject.first_name = subject.last_name = ""
                subject.email_verified_at = None
                subject.is_active = False
                subject.role = "visitor"
                subject.last_login = None
                subject.mfa_secret_encrypted = ""
                subject.mfa_enabled = False
                subject.mfa_last_counter = -1
                subject.account_erased_at = timezone.now()
                subject.set_unusable_password()
                subject.save(
                    update_fields=[
                        "username",
                        "email",
                        "first_name",
                        "last_name",
                        "email_verified_at",
                        "is_active",
                        "role",
                        "last_login",
                        "mfa_secret_encrypted",
                        "mfa_enabled",
                        "mfa_last_counter",
                        "account_erased_at",
                        "password",
                    ]
                )
                result["account_fields_cleared"] = True
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
                result["parts_cleared"] = (
                    RightsExportPart.objects.filter(export_id__in=ids)
                    .exclude(encrypted_content="")
                    .count()
                )
                RightsExportPart.objects.filter(export_id__in=ids).update(encrypted_content="")
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
            if "media" in purposes:
                Photo.objects.filter(revision__listing__person=person).update(
                    removed_at=timezone.now(), approved=False, comparison_complete=True
                )
                if media_redaction:
                    placeholder = Blob.objects.create(
                        sha256=hashlib.sha256(uuid.uuid4().bytes).hexdigest(), status="erased"
                    )
                    result["media_refs_detached"] = Photo.objects.filter(
                        revision__listing__person=person, blob_id__in=shared_ids
                    ).update(blob=placeholder)
                    result["exclusive_media_pending"] = sum(
                        blob.pk not in shared_ids and blob.status != "erased" for blob in media
                    )
                    if result["exclusive_media_pending"]:
                        result["pending_purposes"] = sorted(
                            set(result["pending_purposes"]) | {"media"}
                        )
                for blob in [] if media_redaction else media:
                    if blob.status in {"erasing", "erased"}:
                        continue
                    MediaErasure.objects.create(
                        blob=blob,
                        execution=record,
                        encrypted_paths=seal(
                            {"original": blob.original.name, "derivative": blob.derivative.name}
                        ),
                    )
                    blob.status = "erasing"
                    blob.sha256 = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
                    blob.phash, blob.signature, blob.regional_hashes = "", {}, []
                    blob.width = blob.height = 0
                    blob.error_code = ""
                    blob.save(
                        update_fields=[
                            "status",
                            "sha256",
                            "phash",
                            "signature",
                            "regional_hashes",
                            "width",
                            "height",
                            "error_code",
                        ]
                    )
                    result["media_jobs_queued"] += 1
                record.encrypted_result = seal(result)
                record.save(update_fields=["encrypted_result"])
            person.rights_version += 1
            person.save(update_fields=["rights_version"])
            case.version += 1
            case.scope_status = "unverified"
            case.save(update_fields=["version", "scope_status", "manager_version"])
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
