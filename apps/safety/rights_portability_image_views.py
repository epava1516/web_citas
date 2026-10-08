"""Private guided binary eligibility; inspected content appears only after POST."""

import base64
from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsRequest
from .rights import allowed
from .rights_copy_information_views import LocalizedForm
from .rights_copy_page_review import fresh_authority
from .rights_portability_image_selection import prepare, save
from .rights_portability_prepare_selection_views import CatalogForm, FieldDecisionForm
from .views import private


class ImageCatalogForm(CatalogForm):
    revision_number = forms.IntegerField(min_value=1, initial=1, label="Revisión / Revision")
    image_number = forms.IntegerField(min_value=1, initial=1, label="Imagen / Image")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("dataset", "row_number", "field_page"):
            self.fields.pop(field)


class ImageSaveForm(LocalizedForm):
    operation = forms.CharField(initial="save", widget=forms.HiddenInput)
    key = forms.UUIDField(widget=forms.HiddenInput)
    token = forms.CharField(widget=forms.HiddenInput)
    include = forms.BooleanField(required=False, label="Incluir esta imagen / Include this image")
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado del cambio / Private change reason",
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare_images(request, case_id):
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
    if case.kind != "portability" or case.status != "reviewing" or not case.person_id:
        return private(
            HttpResponse(
                "Current profile portability request required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere una solicitud de portabilidad vigente de perfil",
                status=409,
            )
        )
    initial = {"key": uuid4(), "version": case.version}
    catalog_form = ImageCatalogForm(case=case, language=request.LANGUAGE_CODE, initial=initial)
    save_form, facts_form, image_data, saved, errors = None, None, None, None, []
    status = 400 if request.method == "POST" else 200
    if request.method == "POST":
        operation = request.POST.get("operation")
        try:
            if operation == "catalog":
                catalog_form = ImageCatalogForm(
                    request.POST, case=case, language=request.LANGUAGE_CODE
                )
                if catalog_form.is_valid():
                    values = catalog_form.cleaned_data
                    page = prepare(
                        request.user,
                        case.pk,
                        values["version"],
                        values["review"].pk,
                        values["key"],
                        values["purpose"],
                        values["revision_number"] - 1,
                        values["image_number"] - 1,
                    )
                    path = page["declaration"]["path"]
                    facts = page["conditions"] or {}
                    facts_initial = {"path": path, **facts}
                    for name in ("automated", "subject_related", "third_party_reviewed"):
                        facts_initial[name] = (
                            "yes"
                            if facts.get(name) is True
                            else "no"
                            if facts.get(name) is False
                            else "unknown"
                        )
                    facts_form = FieldDecisionForm(
                        prefix="image", language=request.LANGUAGE_CODE, initial=facts_initial
                    )
                    save_form = ImageSaveForm(
                        language=request.LANGUAGE_CODE,
                        initial={
                            "key": uuid4(),
                            "token": page["token"],
                            "include": page["included"],
                        },
                    )
                    image_data = (
                        "data:image/webp;base64," + base64.b64encode(page["content"]).decode()
                    )
                    status = 200
            elif operation == "save":
                save_form = ImageSaveForm(request.POST, language=request.LANGUAGE_CODE)
                if save_form.is_valid():
                    values = save_form.cleaned_data
                    path = request.POST.get("image-path", "")
                    facts_form = FieldDecisionForm(
                        request.POST,
                        prefix="image",
                        language=request.LANGUAGE_CODE,
                        selected_paths=[path] if values["include"] else [],
                    )
                    if facts_form.is_valid():
                        conditions = {
                            name: value
                            for name, value in facts_form.cleaned_data.items()
                            if name != "path"
                        }
                        saved = save(
                            request.user,
                            values["key"],
                            values["token"],
                            values["reason"],
                            values["include"],
                            {"status": "eligible", **conditions},
                            path=path,
                        )
                        save_form, facts_form = None, None
                        status = 200
            else:
                errors.append(
                    "Invalid operation" if request.LANGUAGE_CODE == "en" else "Operación inválida"
                )
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            errors.extend(error.messages)
            status = 409
    return private(
        render(
            request,
            "safety/rights_portability_images.html",
            {
                "case": case,
                "catalog_form": catalog_form,
                "save_form": save_form,
                "facts_form": facts_form,
                "image_data": image_data,
                "saved": saved,
                "errors": errors,
            },
            status=status,
        )
    )
