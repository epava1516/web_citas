"""Scoped replacement images reuse the media pipeline without manager access."""

import json
import uuid
from datetime import timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.accounts import limited
from apps.listings.models import Revision
from apps.mediafiles.models import Blob, Photo
from apps.mediafiles.services import read_upload
from apps.mediafiles.tasks import process_blob

from .crypto import seal
from .models import (
    RightsAction,
    RightsRectificationPhotoUpload,
    RightsRectificationSourceRead,
    RightsRequest,
)
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read
from .views import private


@sensitive_variables()
def eligible(case, person, digest):
    return RightsRectificationPhotoUpload.objects.filter(
        action__request=case,
        proof__person=person,
        photo__revision__listing__person=person,
        photo__revision__status="rights-stage",
        proof__status="passed",
        photo__revision__manager_version=person.manager_version,
        person_rights_version=person.rights_version,
        source_digest=digest,
        expires_at__gt=timezone.now(),
        discarded_at__isnull=True,
    )


@sensitive_variables()
def baseline(case, person, listing):
    from .rights_rectification import source_snapshot

    _, snapshot = source_snapshot(case, person, listing, include_uploads=False)
    return fingerprint(json.dumps(snapshot, sort_keys=True))


@sensitive_variables()
def check_actor(user, case):
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
        or not permitted(user, case)
    ):
        raise PermissionDenied


@sensitive_variables()
def check_current(user, case, person, listing, version, additional_blob_ids=()):
    if (
        case.kind != "rectify"
        or case.status != "reviewing"
        or case.version != version
        or case.assigned_to_id != user.pk
        or not complete_read(user, case)
        or not complete_response_read(user, case)
        or not listing
        or not listing.approved_revision_id
    ):
        raise ValidationError(
            "Inspect current assigned source / Consulta la fuente asignada vigente"
        )
    proof = authorized_proof(case, person, "rectify")
    from .rights_rectification import source_snapshot

    _, snapshot = source_snapshot(case, person, listing, additional_blob_ids=additional_blob_ids)
    if not RightsRectificationSourceRead.objects.filter(
        request=case,
        actor=user,
        proof=proof,
        case_version=case.version,
        source_digest=fingerprint(json.dumps(snapshot, sort_keys=True)),
    ).exists():
        raise ValidationError(
            "Audited current source required / Consulta auditada vigente obligatoria"
        )
    return proof


@sensitive_variables()
def upload(user, case_id, key, version, image, reason):
    raw, decoded, sha = read_upload(image)
    written = None
    try:
        with transaction.atomic():
            case, person, listing = locked_case(case_id, lock_listing=True)
            check_actor(user, case)
            signature = fingerprint(
                json.dumps({"sha": sha, "version": version, "reason": reason}, sort_keys=True)
            )
            previous = RightsAction.objects.filter(key=key).first()
            if previous:
                if (
                    previous.request_id == case.pk
                    and previous.actor_id == user.pk
                    and previous.operation == "rectify_photo_upload"
                    and previous.payload_digest == signature
                ):
                    return RightsRectificationPhotoUpload.objects.get(action=previous)
                raise ValidationError("Conflicting upload key / Clave de carga incompatible")
            existing_blob = Blob.objects.filter(sha256=sha).first()
            proof = check_current(
                user, case, person, listing, version, [existing_blob.pk] if existing_blob else []
            )
            if not 20 <= len(reason.strip()) <= 2000:
                raise ValidationError("Private reason required / Motivo privado obligatorio")
            current_uploads = RightsRectificationPhotoUpload.objects.filter(
                action__request=case,
                proof__person=person,
                person_rights_version=person.rights_version,
                discarded_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            if current_uploads.count() >= 8:
                raise ValidationError(
                    "At most eight replacement uploads / Máximo ocho cargas de sustitución"
                )
            digest = baseline(case, person, listing)
            blob, created = Blob.objects.get_or_create(sha256=sha)
            blob = Blob.objects.select_for_update().get(pk=blob.pk)
            if blob.status in {"erasing", "erased", "purging", "purged"}:
                raise ValidationError("Image unavailable / Imagen no disponible")
            if created:
                blob.width, blob.height = decoded.size
                blob.original.save(str(uuid.uuid4()), ContentFile(raw), save=False)
                written = blob.original.name
                blob.save()
            revision = Revision.objects.create(
                listing=listing, manager_version=person.manager_version, status="rights-stage"
            )
            photo = Photo.objects.create(revision=revision, blob=blob)
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="rectify_photo_upload",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = RightsRectificationPhotoUpload.objects.create(
                action=action,
                proof=proof,
                photo=photo,
                source_digest=digest,
                person_rights_version=person.rights_version,
                expires_at=min(proof.expires_at, timezone.now() + timedelta(hours=24)),
            )
            transaction.on_commit(lambda: process_blob.delay(str(blob.pk)), robust=True)
            return result
    except Exception as error:
        if written:
            Blob._meta.get_field("original").storage.delete(written)
        if isinstance(error, IntegrityError):
            raise ValidationError("Conflicting upload key / Clave de carga incompatible") from error
        raise


@transaction.atomic
@sensitive_variables()
def discard(user, case_id, key, version, photo_id, reason):
    case, person, listing = locked_case(case_id, lock_listing=True)
    check_actor(user, case)
    signature = fingerprint(
        json.dumps({"photo": str(photo_id), "version": version, "reason": reason}, sort_keys=True)
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "rectify_img_discard"
            and previous.payload_digest == signature
        ):
            return
        raise ValidationError("Conflicting discard key / Clave incompatible")
    check_current(user, case, person, listing, version)
    item = (
        RightsRectificationPhotoUpload.objects.select_for_update()
        .filter(action__request=case, photo_id=photo_id, proof__person=person)
        .first()
    )
    if not item or item.discarded_at or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError(
            "Current upload and reason required / Carga vigente y motivo obligatorios"
        )
    item.discarded_at = timezone.now()
    item.save(update_fields=["discarded_at"])
    try:
        with transaction.atomic():
            RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="rectify_img_discard",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting discard key / Clave incompatible") from error


class UploadForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        widget=forms.HiddenInput,
        choices=[
            ("upload", "Prepare image / Preparar imagen"),
            ("discard", "Discard upload / Descartar carga"),
        ],
    )
    image = forms.FileField(required=False, label="Replacement image / Imagen de sustitución")
    photo_id = forms.UUIDField(
        widget=forms.HiddenInput,
        required=False,
        label="Uploaded reference to discard / Referencia cargada para descartar",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Private reason / Motivo privado",
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        return private(HttpResponse("Not found", status=404))
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    if case.kind != "rectify":
        return private(HttpResponse("Unsupported request type", status=409))
    form = UploadForm(
        request.POST or None,
        request.FILES or None,
        initial={
            "key": uuid.uuid4(),
            "version": case.version,
            "operation": "discard" if request.GET.get("discard") else "upload",
            "photo_id": request.GET.get("discard", ""),
        },
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        if limited(request, "rights-photo-upload", 20):
            return private(HttpResponse("Too many requests", status=429))
        data = form.cleaned_data
        try:
            if data["operation"] == "discard":
                if not data["photo_id"]:
                    raise ValidationError(
                        "Uploaded reference required / Referencia cargada obligatoria"
                    )
                discard(
                    request.user,
                    case.pk,
                    data["key"],
                    data["version"],
                    data["photo_id"],
                    data["reason"],
                )
            else:
                if not data["image"]:
                    raise ValidationError("Image required / Imagen obligatoria")
                upload(
                    request.user,
                    case.pk,
                    data["key"],
                    data["version"],
                    data["image"],
                    data["reason"],
                )
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("rights_rectification", case_id=case.pk))
    return private(
        render(
            request,
            "safety/rectification_uploads.html",
            {"case": case, "form": form},
            status=status,
        )
    )
