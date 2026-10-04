import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from apps.listings.history import rectification_history_ids
from apps.mediafiles.models import Blob

from .models import RightsPhotoReintroduction, RightsPhotoReintroductionRead
from .photo_reintroduction_review import decide, inspect, locked, permission, source
from .views import private


class AuditForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(widget=forms.HiddenInput)
    purpose = forms.CharField(
        min_length=20, max_length=200, label="Motivo de consulta / Access purpose"
    )


class DecisionForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(widget=forms.HiddenInput)
    read_id = forms.IntegerField(widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[
            ("", "Selecciona / Choose"),
            ("maintain", "Mantener retirada / Maintain withdrawal"),
            ("false_positive", "Falso positivo visual / Visual false positive"),
            ("authorize", "Autorizar uso actual / Authorize current use"),
        ]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )
    reference = forms.CharField(
        min_length=3, max_length=200, label="Referencia de evidencia / Evidence reference"
    )


def allowed(request):
    permission(request.user)
    if request.session.get("mfa_version") != request.user.mfa_version:
        raise PermissionDenied


@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
@sensitive_post_parameters()
def review(request, candidate_id):
    allowed(request)
    try:
        candidate = locked(request.user, candidate_id)
    except RightsPhotoReintroduction.DoesNotExist:
        raise Http404
    except ValidationError:
        return private(HttpResponse("Review unavailable", status=409))
    audit = AuditForm(
        request.POST if request.POST.get("operation") == "inspect" else None,
        initial={"key": uuid.uuid4(), "version": candidate.review_version},
    )
    decision = DecisionForm(request.POST if request.POST.get("operation") == "decide" else None)
    read = None
    if request.method == "POST":
        try:
            if request.POST.get("operation") == "inspect" and audit.is_valid():
                read = inspect(request.user, candidate.pk, **audit.cleaned_data)
                decision = DecisionForm(
                    initial={
                        "key": uuid.uuid4(),
                        "version": candidate.review_version,
                        "read_id": read.pk,
                    }
                )
            elif request.POST.get("operation") == "decide" and decision.is_valid():
                decide(request.user, candidate.pk, **decision.cleaned_data)
                return redirect("photo_reuse_review", candidate_id=candidate.pk)
        except ValidationError as error:
            (audit if request.POST.get("operation") == "inspect" else decision).add_error(
                None, error
            )
    latest = candidate.decisions.order_by("-review_version").first()
    return private(
        render(
            request,
            "safety/photo_reuse_review.html",
            {
                "latest_decision": latest,
                "decision_current": bool(latest and latest.source_digest == source(candidate)),
                "candidate": candidate,
                "audit": audit,
                "decision": decision,
                "read": read,
            },
            status=400 if request.method == "POST" and not read else 200,
        )
    )


@login_required
@transaction.atomic
def image(request, candidate_id, read_id, side):
    allowed(request)
    try:
        candidate = locked(request.user, candidate_id)
    except RightsPhotoReintroduction.DoesNotExist:
        raise Http404
    except ValidationError:
        raise Http404
    get_object_or_404(
        RightsPhotoReintroductionRead,
        pk=read_id,
        candidate=candidate,
        actor=request.user,
        review_version=candidate.review_version,
        source_digest=source(candidate),
    )
    if side not in {"uploaded", "withdrawn"}:
        raise Http404
    blob = Blob.objects.get(
        pk=candidate.uploaded_blob_id if side == "uploaded" else candidate.disposition.blob_id
    )
    try:
        stream = blob.derivative.open("rb")
    except OSError:
        raise Http404
    return private(FileResponse(stream, content_type="image/webp"))


@login_required
@transaction.atomic
def queue(request):
    allowed(request)
    candidates = (
        RightsPhotoReintroduction.objects.filter(
            photo__removed_at__isnull=True,
            photo__rectification_upload__isnull=True,
            uploaded_blob_id=F("photo__blob_id"),
        )
        .exclude(photo__revision_id__in=rectification_history_ids())
        .order_by("created_at", "pk")
    )
    page = Paginator(candidates, 25).get_page(request.GET.get("page"))
    permitted_candidates = []
    for candidate in page:
        try:
            permitted_candidates.append(locked(request.user, candidate.pk))
        except (ValidationError, PermissionDenied):
            continue
    return private(
        render(
            request,
            "safety/photo_reuse_queue.html",
            {
                "candidates": permitted_candidates,
                "page": page,
            },
        )
    )
