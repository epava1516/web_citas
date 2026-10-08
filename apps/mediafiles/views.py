from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.accounts import limited
from apps.core.agencies import person_queryset
from apps.core.verification import locked_manager_person
from apps.listings.models import Revision
from apps.listings.revisions import is_rectification_history

from .models import Photo, UploadAttempt
from .services import ingest


class UploadForm(forms.Form):
    image = forms.FileField(label="Fotografía / Photo")


@login_required
@require_POST
def upload(request, revision_id):
    revision = get_object_or_404(
        Revision, pk=revision_id, listing__person__in=person_queryset(request.user)
    )
    if limited(request, "photo-upload", 30):
        return HttpResponse(
            "Too many uploads" if request.LANGUAGE_CODE == "en" else "Demasiadas subidas",
            status=429,
        )
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            ingest(request.user, revision.pk, form.cleaned_data["image"])
            return redirect("draft_edit", revision_id=revision.pk, step=3)
        except ValidationError as error:
            UploadAttempt.objects.create(user=request.user, revision=revision, result="invalid")
            return HttpResponse(" / ".join(error.messages), status=400)
    return HttpResponse(
        "File required" if request.LANGUAGE_CODE == "en" else "Archivo requerido", status=400
    )


@login_required
@transaction.atomic
def private_photo(request, photo_id):
    photo = get_object_or_404(
        Photo,
        pk=photo_id,
        removed_at__isnull=True,
        revision__listing__person__in=person_queryset(request.user),
        revision__manager_version=F("revision__listing__person__manager_version"),
        rectification_upload__isnull=True,
    )
    try:
        person = locked_manager_person(request.user, photo.revision.listing.person_id)
    except PermissionDenied:
        return HttpResponse("Not found", status=404)
    revision = Revision.objects.select_for_update().get(pk=photo.revision_id)
    if (
        revision.status == "rights-stage"
        or revision.manager_version != person.manager_version
        or is_rectification_history(revision)
    ):
        return HttpResponse("Not found", status=404)
    # A rights operation may have detached or withdrawn the reference while
    # this request waited for its manager/person lock. Read it again afterwards.
    photo = get_object_or_404(
        Photo,
        pk=photo.pk,
        revision=revision,
        removed_at__isnull=True,
        rectification_upload__isnull=True,
    )
    if photo.blob.status != "ready" or not photo.blob.derivative:
        return HttpResponse("Photo processing", status=409)
    response = FileResponse(photo.blob.derivative.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def remove(request, photo_id):
    initial = get_object_or_404(
        Photo,
        pk=photo_id,
        rectification_upload__isnull=True,
        revision__listing__person__in=person_queryset(request.user),
    )
    with transaction.atomic():
        person = locked_manager_person(request.user, initial.revision.listing.person_id)
        revision = Revision.objects.select_for_update().get(pk=initial.revision_id)
        if (
            is_rectification_history(revision)
            or revision.status != "draft"
            or revision.manager_version != person.manager_version
        ):
            return HttpResponse("Revision not editable", status=409)
        photo = Photo.objects.select_for_update().get(pk=initial.pk)
        photo.removed_at = timezone.now()
        photo.save(update_fields=["removed_at"])
        revision.edit_version += 1
        revision.save(update_fields=["edit_version", "updated_at"])
    return redirect("draft_edit", revision_id=revision.pk, step=3)


@login_required
@require_POST
def reorder(request, photo_id):
    initial = get_object_or_404(
        Photo,
        pk=photo_id,
        removed_at__isnull=True,
        revision__listing__person__in=person_queryset(request.user),
        rectification_upload__isnull=True,
    )
    with transaction.atomic():
        person = locked_manager_person(request.user, initial.revision.listing.person_id)
        revision = Revision.objects.select_for_update().get(pk=initial.revision_id)
        if (
            is_rectification_history(revision)
            or revision.status != "draft"
            or revision.manager_version != person.manager_version
        ):
            return HttpResponse("Revision not editable", status=409)
        photos = list(
            revision.photos.filter(removed_at__isnull=True).order_by("position", "created_at")
        )
        index = next(i for i, photo in enumerate(photos) if photo.pk == initial.pk)
        delta = (
            -1
            if request.POST.get("direction") == "up"
            else 1
            if request.POST.get("direction") == "down"
            else 0
        )
        if not delta:
            return HttpResponse("Invalid direction", status=400)
        other = index + delta
        if 0 <= other < len(photos):
            photos[index], photos[other] = photos[other], photos[index]
        for position, photo in enumerate(photos):
            photo.position = position
        Photo.objects.bulk_update(photos, ["position"])
        revision.edit_version += 1
        revision.save(update_fields=["edit_version", "updated_at"])
    return redirect("draft_edit", revision_id=revision.pk, step=3)
