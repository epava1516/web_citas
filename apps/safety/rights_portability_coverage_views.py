"""Private guided omission declarations; GET never restores source or evidence."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsPortabilitySelectionReview, RightsRequest
from .rights import allowed
from .rights_copy_page_review import fresh_authority
from .rights_portability_coverage import exclusion
from .rights_portability_coverage_pages import MAX_AGE, SALT, prepare_page, save_page
from .rights_portability_prepare_selection_views import CatalogForm, SaveForm, field_label
from .rights_portability_views import DatasetForm
from .views import private


class Catalog(CatalogForm):
    def __init__(self, *args, case, actor, **kwargs):
        super().__init__(*args, case=case, **kwargs)
        self.fields["review"] = forms.ModelChoiceField(
            queryset=RightsPortabilitySelectionReview.objects.filter(
                selection__request=case,
                selection__actor=actor,
                outcome="approved",
                selection__purged_at__isnull=True,
                selection__expires_at__gt=timezone.now(),
            )
            .select_related("selection")
            .order_by("-pk"),
            label="Selección aprobada / Approved selection",
        )


class ImageCatalog(Catalog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("dataset")
        self.fields.pop("row_number")
        self.fields["field_page"].label = "Página de imágenes / Image page"


class Save(SaveForm):
    reason = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado de cobertura / Private coverage reason",
    )

    def __init__(self, *args, paths, **kwargs):
        super().__init__(*args, paths=paths, **kwargs)
        self.fields["reason"].label = "Motivo privado de cobertura / Private coverage reason"
        self.fields[
            "paths"
        ].label = "Omisiones justificadas en esta página / Justified omissions on this page"


class Decision(DatasetForm):
    path = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, selected_paths=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("dataset")
        self.fields.pop("status")
        self.selected_paths = set(selected_paths)

    @property
    def path_label(self):
        return field_label(self["path"].value() or "")

    def clean(self):
        values = super().clean()
        if not self.errors and values.get("path") in self.selected_paths:
            try:
                exclusion(
                    {
                        "status": "excluded",
                        **{name: value for name, value in values.items() if name != "path"},
                    }
                )
            except ValidationError as error:
                raise forms.ValidationError(error.messages) from error
        return values


class DecisionsBase(forms.BaseFormSet):
    def __init__(self, *args, allowed_paths, **kwargs):
        self.allowed_paths = allowed_paths
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        paths = [form.cleaned_data.get("path") for form in self.forms]
        if len(paths) != len(self.allowed_paths) or set(paths) != set(self.allowed_paths):
            raise forms.ValidationError("Evalúa cada campo una vez / Assess each field once")


Decisions = forms.formset_factory(
    Decision, formset=DecisionsBase, extra=0, max_num=50, absolute_max=50, validate_max=True
)


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id, *, images=False):
    from .rights_portability_coverage_images import (
        SALT as IMAGE_SALT,
    )
    from .rights_portability_coverage_images import (
        prepare_images,
        save_images,
    )

    catalog_type = ImageCatalog if images else Catalog
    token_salt = IMAGE_SALT if images else SALT
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    try:
        fresh_authority(request.user, case, request.user.session_version, request.user.mfa_version)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    if case.assigned_to_id != request.user.pk:
        return private(HttpResponse("Assigned reviewer required", status=403))
    if case.kind != "portability" or case.status != "reviewing":
        return private(HttpResponse("Current portability request required", status=409))
    form = catalog_type(
        case=case,
        actor=request.user,
        initial={
            "key": uuid4(),
            "version": case.version,
            "dataset": "subject_account" if case.account_subject_id else "profile",
        },
    )
    catalog = save_form = field_forms = saved = None
    errors = []
    status = 200
    if request.method == "POST":
        status = 400
        try:
            if request.POST.get("operation") == "catalog":
                form = catalog_type(request.POST, case=case, actor=request.user)
                if form.is_valid():
                    values = form.cleaned_data
                    catalog = (
                        prepare_images(
                            request.user,
                            case.pk,
                            values["version"],
                            values["review"].pk,
                            values["key"],
                            values["purpose"],
                            values["field_page"],
                        )
                        if images
                        else prepare_page(
                            request.user,
                            case.pk,
                            values["version"],
                            values["review"].pk,
                            values["key"],
                            values["purpose"],
                            values["dataset"],
                            values["row_number"] - 1,
                            values["field_page"],
                        )
                    )
                    if images:
                        catalog["fields"] = [
                            {
                                "path": item["photo"],
                                "value": item.get("processing_status", "—"),
                                "label": item["photo"],
                            }
                            for item in catalog["images"]
                        ]
                    paths = [item["path"] for item in catalog["fields"]]
                    save_form = Save(
                        paths=paths,
                        initial={
                            "key": uuid4(),
                            "token": catalog["token"],
                            "paths": list(catalog["decisions"]),
                        },
                    )
                    initial = []
                    for item in catalog["fields"]:
                        item["label"] = item["path"] if images else field_label(item["path"])
                        facts = {
                            "path": item["path"],
                            "basis": "unknown",
                            "origin": "unknown",
                            "automated": "unknown",
                            "subject_related": "unknown",
                            "third_party_reviewed": "unknown",
                            "reason": "",
                            "evidence": "",
                            **catalog["decisions"].get(item["path"], {}),
                        }
                        facts.pop("status", None)
                        for name in ("automated", "subject_related", "third_party_reviewed"):
                            if type(facts[name]) is bool:
                                facts[name] = "yes" if facts[name] else "no"
                        initial.append(facts)
                    field_forms = Decisions(initial=initial, prefix="fields", allowed_paths=paths)
                    status = 200
            elif request.POST.get("operation") == "save":
                context = signing.loads(
                    request.POST.get("token", ""), salt=token_salt, max_age=MAX_AGE
                )
                if images and isinstance(context, dict):
                    context["paths"] = context.get("photos")
                if not isinstance(context, dict) or not isinstance(context.get("paths"), list):
                    raise signing.BadSignature("Invalid coverage page")
                save_form = Save(request.POST, paths=context["paths"])
                field_forms = Decisions(
                    request.POST,
                    prefix="fields",
                    allowed_paths=context["paths"],
                    form_kwargs={"selected_paths": request.POST.getlist("paths")},
                )
                if save_form.is_valid() and field_forms.is_valid():
                    values = save_form.cleaned_data
                    decisions = {
                        item["path"]: {
                            "status": "excluded",
                            **{name: value for name, value in item.items() if name != "path"},
                        }
                        for item in field_forms.cleaned_data
                        if item["path"] in values["paths"]
                    }
                    saved = (save_images if images else save_page)(
                        request.user,
                        case.pk,
                        values["token"],
                        values["key"],
                        values["reason"],
                        decisions,
                    )
                    save_form = field_forms = None
                    status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except (signing.BadSignature, ValueError, TypeError):
            errors.append("Página caducada o inválida / Expired or invalid page")
            status = 409
        except ValidationError as error:
            errors.extend(error.messages)
            status = 409
    return private(
        render(
            request,
            "safety/rights_portability_coverage.html",
            {
                "images_mode": images,
                "case": case,
                "form": form,
                "catalog": catalog,
                "save_form": save_form,
                "field_forms": field_forms,
                "saved": saved,
                "page_errors": errors,
            },
            status=status,
        )
    )


def prepare_image_omissions(request, case_id):
    return prepare(request, case_id, images=True)
