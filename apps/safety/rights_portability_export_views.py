"""Assigned operator generation of approved portable fields; no values on GET."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsPortabilityCoverageReview, RightsPortabilitySelectionReview, RightsRequest
from .rectification_presentation import caption
from .rights import allowed
from .rights_copy_information_views import LocalizedForm
from .rights_copy_page_review import fresh_authority
from .rights_portability_jobs import enqueue
from .views import private


class ApprovedSelection(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.selection_id} · {obj.selection.version}"


class ApprovedCoverage(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.coverage_id} · {obj.coverage.version}"


class ExportForm(LocalizedForm):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    review = ApprovedSelection(
        queryset=RightsPortabilitySelectionReview.objects.none(),
        label="Selección aprobada / Approved selection",
    )
    coverage_review = ApprovedCoverage(
        queryset=RightsPortabilityCoverageReview.objects.none(),
        required=False,
        label="Cobertura aprobada / Approved coverage",
        help_text="Selecciona la cobertura para una entrega completa; sin ella se crea una copia parcial. / Select coverage for a complete delivery; otherwise the copy is partial.",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado de entrega / Private delivery reason",
    )

    def __init__(self, *args, case, actor, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        if language is not None:
            field = self.fields["coverage_review"]
            field.help_text = caption(field.help_text, language)
        self.fields["review"].queryset = (
            RightsPortabilitySelectionReview.objects.filter(
                selection__request=case,
                selection__actor=actor,
                outcome="approved",
                selection__purged_at__isnull=True,
                selection__expires_at__gt=timezone.now(),
            )
            .select_related("selection")
            .only("pk", "selection_id", "selection__version")
            .order_by("-pk")
        )
        self.fields["coverage_review"].queryset = (
            RightsPortabilityCoverageReview.objects.filter(
                coverage__request=case,
                coverage__actor=actor,
                outcome="approved",
                coverage__purged_at__isnull=True,
                coverage__expires_at__gt=timezone.now(),
            )
            .select_related("coverage")
            .only("pk", "coverage_id", "coverage__version")
            .order_by("-pk")
        )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        fresh_authority(request.user, case, request.user.session_version, request.user.mfa_version)
        if case.assigned_to_id != request.user.pk:
            raise PermissionDenied
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    if case.kind != "portability" or case.status != "reviewing":
        return private(
            HttpResponse(
                "Current portability request required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere una solicitud de portabilidad vigente",
                status=409,
            )
        )
    form = ExportForm(
        request.POST if request.method == "POST" else None,
        case=case,
        actor=request.user,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid4(), "version": case.version},
    )
    export = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            job = enqueue(
                request.user,
                case.pk,
                values["version"],
                values["review"].selection_id,
                values["review"].pk,
                values["key"],
                values["reason"],
                coverage_review_id=values["coverage_review"].pk
                if values["coverage_review"]
                else None,
            )
            return private(redirect("rights_portability_export_job", case.pk, job.pk))
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/rights_portability_export.html",
            {
                "case": case,
                "form": form,
                "export": export,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )


@login_required
@require_http_methods(["GET"])
def job_status(request, case_id, job_id):
    from .models import RightsPortabilityExportJob

    if not allowed(request):
        return private(HttpResponse(status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        fresh_authority(request.user, case, request.user.session_version, request.user.mfa_version)
        if case.assigned_to_id != request.user.pk:
            raise PermissionDenied
    except PermissionDenied:
        return private(HttpResponse(status=403))
    job = (
        RightsPortabilityExportJob.objects.filter(
            pk=job_id,
            request=case,
            actor=request.user,
            session_version=request.user.session_version,
            mfa_version=request.user.mfa_version,
        )
        .only("pk", "state", "export_id", "expires_at", "request_id")
        .first()
    )
    if job is None:
        raise Http404
    template = (
        "safety/_rights_portability_job.html"
        if request.headers.get("HX-Request") == "true"
        else "safety/rights_portability_job.html"
    )
    response = render(
        request,
        template,
        {
            "case": case,
            "job": job,
            "english": request.LANGUAGE_CODE == "en",
            "pending": job.state in {"queued", "running"},
        },
    )
    response.headers["Vary"] = "HX-Request, Cookie, Accept-Language"
    return private(response)
