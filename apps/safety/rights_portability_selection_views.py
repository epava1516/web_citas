"""Private selection review; GET never restores selected values."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods, require_POST

from .models import RightsPortabilitySelection, RightsRequest
from .rights import allowed
from .rights_copy_information_views import LocalizedForm
from .rights_portability_review import authorize
from .rights_portability_selection_review import record
from .rights_portability_views import translated
from .views import private


class ReviewForm(LocalizedForm):
    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        if language is not None:
            self.fields["operation"].label = "Operation" if language == "en" else "Operación"
            self.fields["outcome"].label = "Outcome" if language == "en" else "Resultado"

    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[("inspect", "Consultar / Inspect"), ("review", "Decidir / Decide")]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[("", "—"), ("approved", "Aprobar / Approve"), ("rejected", "Rechazar / Reject")],
    )


class ImageInspectionForm(LocalizedForm):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado de consulta / Private inspection purpose",
    )

    def __init__(self, *args, photo_id=None, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        if photo_id:
            for name, field in self.fields.items():
                field.widget.attrs["id"] = f"image-{photo_id}-{name}"


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def review(request, case_id, selection_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if case.kind != "portability":
        return private(
            HttpResponse(
                "Portability request required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere una solicitud de portabilidad",
                status=409,
            )
        )
    try:
        authorize(request.user, case)
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    information = RightsPortabilitySelection.objects.filter(pk=selection_id, request=case).first()
    if not information:
        raise Http404
    if information.actor_id == request.user.pk:
        return private(
            HttpResponse(
                "Independent reviewer required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere revisión independiente",
                status=403,
            )
        )
    form = ReviewForm(
        request.POST if request.method == "POST" else None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid4(), "version": case.version},
    )
    body, decision = None, None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            values = form.cleaned_data
            result, body = record(
                request.user,
                case.pk,
                values["version"],
                information.pk,
                values["key"],
                values["reason"],
                values["operation"],
                values["outcome"],
            )
            decision = result if body is None else None
            form = ReviewForm(
                language=request.LANGUAGE_CODE, initial={"key": uuid4(), "version": case.version}
            )
            status = 200
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    reviewed_fields = []
    field_reviews = []
    if body:
        for name, rows in body["datasets"].items():
            reviewed_fields.append(
                {
                    "label": translated(name),
                    "rows": [
                        [
                            {
                                "label": " › ".join(
                                    segment.replace("~1", "/").replace("~0", "~").replace("_", " ")
                                    for segment in path[1:].split("/")
                                ),
                                "value": value,
                            }
                            for path, value in row["fields"].items()
                        ]
                        for row in rows
                    ],
                }
            )
    if body:
        for dataset, rows in body.get("field_evidence", {}).items():
            for fields in rows.values():
                for path, facts in fields.items():
                    field_reviews.append(
                        {
                            "dataset": translated(dataset),
                            "path": path,
                            "basis": translated(facts["basis"]),
                            "origin": translated(facts["origin"]),
                            "reason": facts["reason"],
                            "evidence": facts["evidence"],
                            "automated": facts["automated"],
                            "subject_related": facts["subject_related"],
                            "third_party_reviewed": facts["third_party_reviewed"],
                        }
                    )
    return private(
        render(
            request,
            "safety/rights_portability_selection_review.html",
            {
                "case": case,
                "selection_id": information.pk,
                "form": form,
                "body": body,
                "reviewed_fields": reviewed_fields,
                "field_reviews": field_reviews,
                "decision": decision,
                "binary_images": [
                    {
                        "photo": item["photo"],
                        "conditions": item["conditions"],
                        "basis": translated(item["conditions"]["basis"]),
                        "origin": translated(item["conditions"]["origin"]),
                        "form": ImageInspectionForm(
                            photo_id=item["photo"],
                            language=request.LANGUAGE_CODE,
                            initial={"key": uuid4(), "version": case.version},
                        ),
                    }
                    for item in (body.get("images", []) if body else [])
                ],
            },
            status=status,
        )
    )


@login_required
@require_POST
@sensitive_post_parameters()
@sensitive_variables()
def inspect_image(request, case_id, selection_id, photo_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ImageInspectionForm(request.POST, language=request.LANGUAGE_CODE)
    if not form.is_valid():
        return private(
            HttpResponse(
                "Invalid inspection form"
                if request.LANGUAGE_CODE == "en"
                else "Formulario de consulta inválido",
                status=400,
            )
        )
    from .rights_portability_image_read import inspect

    values = form.cleaned_data
    try:
        _, content = inspect(
            request.user,
            case_id,
            values["version"],
            selection_id,
            photo_id,
            values["key"],
            values["reason"],
        )
    except RightsRequest.DoesNotExist:
        raise Http404 from None
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    except ValidationError:
        return private(
            HttpResponse(
                "Image or authorization changed"
                if request.LANGUAGE_CODE == "en"
                else "La imagen o la autorización han cambiado",
                status=409,
            )
        )
    response = HttpResponse(content, content_type="image/webp")
    response["Content-Disposition"] = 'inline; filename="portable-image-review.webp"'
    return private(response)
