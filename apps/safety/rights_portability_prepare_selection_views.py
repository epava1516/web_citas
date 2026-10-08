"""Private guided scalar selection; values appear only after an audited POST."""

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

from .models import RightsPortabilityReview, RightsRequest
from .rectification_presentation import caption
from .rights import allowed
from .rights_copy_information_views import LocalizedForm
from .rights_copy_page_review import fresh_authority
from .rights_portability import DATASETS, checked_assessment
from .rights_portability_page_selection import MAX_AGE, SALT, latest_draft, prepare_page, save_page
from .rights_portability_reset_selection import reset_selection
from .rights_portability_views import DatasetForm, translated
from .views import private


def field_label(path):
    return " › ".join(
        segment.replace("~1", "/").replace("~0", "~").replace("_", " ")
        for segment in path[1:].split("/")
    )


class ApprovedChoice(forms.ModelChoiceField):
    presentation_language = None

    def label_from_instance(self, obj):
        label = (
            caption("Evaluación aprobada / Approved assessment", self.presentation_language)
            if self.presentation_language is not None
            else "Evaluación aprobada / Approved assessment"
        )
        return f"{label} {obj.pk} · {obj.assessment.version}"


class CatalogForm(LocalizedForm):
    operation = forms.CharField(initial="catalog", widget=forms.HiddenInput)
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    review = ApprovedChoice(
        queryset=RightsPortabilityReview.objects.none(),
        label="Evaluación aprobada / Approved assessment",
    )
    dataset = forms.ChoiceField(choices=[], label="Conjunto de datos / Dataset")
    row_number = forms.IntegerField(min_value=1, initial=1, label="Registro / Record")
    field_page = forms.IntegerField(min_value=1, initial=1, label="Página de campos / Field page")
    purpose = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado de consulta / Private inspection purpose",
    )

    def __init__(self, *args, case, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        self.fields["review"].presentation_language = language
        self.fields["dataset"].choices = [(name, translated(name)) for name in DATASETS]
        self.fields["review"].queryset = (
            RightsPortabilityReview.objects.filter(
                assessment__request=case,
                outcome="approved",
                assessment__purged_at__isnull=True,
                assessment__expires_at__gt=timezone.now(),
            )
            .select_related("assessment")
            .only("pk", "assessment_id", "assessment__version")
            .order_by("-pk")
        )


class SaveForm(LocalizedForm):
    operation = forms.CharField(initial="save", widget=forms.HiddenInput)
    key = forms.UUIDField(widget=forms.HiddenInput)
    token = forms.CharField(widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado de selección / Private selection reason",
    )
    paths = forms.MultipleChoiceField(
        required=False,
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        label="Campos seleccionados / Selected fields",
    )

    def __init__(self, *args, paths, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        self.fields["paths"].choices = [(path, field_label(path)) for path in paths]


class FieldDecisionForm(DatasetForm):
    path = forms.CharField(max_length=500, widget=forms.HiddenInput)

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
        if not self.errors and values["path"] in self.selected_paths:
            facts = {name: value for name, value in values.items() if name != "path"}
            try:
                checked_assessment({name: {"status": "eligible", **facts} for name in DATASETS})
            except ValidationError as error:
                raise forms.ValidationError(error.messages) from error
        return values


class FieldDecisionSet(forms.BaseFormSet):
    def __init__(self, *args, allowed_paths, **kwargs):
        self.allowed_paths = list(allowed_paths)
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        paths = [form.cleaned_data["path"] for form in self.forms]
        if len(paths) != len(self.allowed_paths) or set(paths) != set(self.allowed_paths):
            raise forms.ValidationError(
                "Evalúa cada campo consultado una vez / Assess each inspected field once"
            )


FieldDecisions = forms.formset_factory(
    FieldDecisionForm,
    formset=FieldDecisionSet,
    extra=0,
    max_num=50,
    absolute_max=50,
    validate_max=True,
)


class ResetForm(LocalizedForm):
    operation = forms.CharField(initial="reset", widget=forms.HiddenInput)
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    previous_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    previous_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    previous_digest = forms.RegexField(r"^[0-9a-f]{64}$", widget=forms.HiddenInput)
    review = ApprovedChoice(
        queryset=RightsPortabilityReview.objects.none(),
        label="Evaluación aprobada / Approved assessment",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado del reinicio / Private reset reason",
    )
    confirmed = forms.BooleanField(
        required=True,
        label="Confirmo descartar todas las elecciones del borrador actual / I confirm clearing all current draft choices",
    )

    def __init__(self, *args, case, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        self.fields["review"].presentation_language = language
        self.fields["review"].queryset = CatalogForm(case=case).fields["review"].queryset
        for name, field in self.fields.items():
            field.widget.attrs["id"] = "reset_" + name


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
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    if case.assigned_to_id != request.user.pk:
        return private(
            HttpResponse(
                "Assigned reviewer required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere el revisor asignado",
                status=403,
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
    catalog, saved, save_form = None, None, None
    page_errors = []
    field_forms = None
    reset_form, reset_done = None, False
    previous = latest_draft(case, request.user)
    if previous:
        reset_form = ResetForm(
            case=case,
            language=request.LANGUAGE_CODE,
            initial={
                "key": uuid4(),
                "version": case.version,
                "previous_id": previous.pk,
                "previous_version": previous.version,
                "previous_digest": previous.selection_digest,
            },
        )
    status = 200
    form = CatalogForm(
        case=case,
        language=request.LANGUAGE_CODE,
        initial={
            "key": uuid4(),
            "version": case.version,
            "dataset": "subject_account" if case.account_subject_id else "profile",
        },
    )
    if request.method == "POST":
        status = 400
        if request.POST.get("operation") == "catalog":
            form = CatalogForm(request.POST, case=case, language=request.LANGUAGE_CODE)
            if form.is_valid():
                values = form.cleaned_data
                try:
                    catalog = prepare_page(
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
                    save_form = SaveForm(
                        language=request.LANGUAGE_CODE,
                        paths=[item["path"] for item in catalog["fields"]],
                        initial={
                            "key": uuid4(),
                            "token": catalog["token"],
                            "paths": catalog["chosen"],
                        },
                    )
                    if catalog["granular"]:
                        initial_facts = [
                            {
                                "path": item["path"],
                                "basis": "unknown",
                                "origin": "unknown",
                                "automated": "unknown",
                                "subject_related": "unknown",
                                "third_party_reviewed": "unknown",
                                "reason": "",
                                "evidence": "",
                                **catalog["field_decisions"].get(item["path"], {}),
                            }
                            for item in catalog["fields"]
                        ]
                        # Existing boolean facts must match the tri-state widget values.
                        for facts in initial_facts:
                            for name in ("automated", "subject_related", "third_party_reviewed"):
                                if type(facts[name]) is bool:
                                    facts[name] = "yes" if facts[name] else "no"
                        field_forms = FieldDecisions(
                            initial=initial_facts,
                            prefix="fields",
                            form_kwargs={"language": request.LANGUAGE_CODE},
                            allowed_paths=[item["path"] for item in catalog["fields"]],
                        )
                    for item in catalog["fields"]:
                        item["label"] = field_label(item["path"])
                    form = CatalogForm(
                        case=case,
                        language=request.LANGUAGE_CODE,
                        initial={**values, "key": uuid4(), "review": values["review"].pk},
                    )
                    status = 200
                except PermissionDenied:
                    return private(
                        HttpResponse(
                            "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado",
                            status=403,
                        )
                    )
                except ValidationError as error:
                    form.add_error(None, error)
                    status = 409
        elif request.POST.get("operation") == "reset":
            reset_form = ResetForm(request.POST, case=case, language=request.LANGUAGE_CODE)
            if reset_form.is_valid():
                values = reset_form.cleaned_data
                try:
                    saved = reset_selection(
                        request.user,
                        case.pk,
                        values["version"],
                        values["review"].pk,
                        values["key"],
                        values["reason"],
                        values["previous_id"],
                        values["previous_version"],
                        values["previous_digest"],
                        values["confirmed"],
                    )
                    reset_done, reset_form, status = True, None, 200
                except PermissionDenied:
                    return private(
                        HttpResponse(
                            "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado",
                            status=403,
                        )
                    )
                except ValidationError as error:
                    reset_form.add_error(None, error)
                    status = 409
        elif request.POST.get("operation") == "save":
            try:
                context = signing.loads(request.POST.get("token", ""), salt=SALT, max_age=MAX_AGE)
                if not isinstance(context, dict) or not isinstance(context.get("paths"), list):
                    raise signing.BadSignature("Invalid page")
                save_form = SaveForm(
                    request.POST, paths=context["paths"], language=request.LANGUAGE_CODE
                )
                if context.get("granular"):
                    field_forms = FieldDecisions(
                        request.POST,
                        prefix="fields",
                        allowed_paths=context["paths"],
                        form_kwargs={
                            "selected_paths": request.POST.getlist("paths"),
                            "language": request.LANGUAGE_CODE,
                        },
                    )
                if save_form.is_valid() and (field_forms is None or field_forms.is_valid()):
                    values = save_form.cleaned_data
                    decisions = None
                    if field_forms is not None:
                        decisions = {
                            item["path"]: {
                                "status": "eligible",
                                **{name: value for name, value in item.items() if name != "path"},
                            }
                            for item in field_forms.cleaned_data
                            if item["path"] in values["paths"]
                        }
                    saved = save_page(
                        request.user,
                        case.pk,
                        values["token"],
                        values["key"],
                        values["reason"],
                        values["paths"],
                        field_decisions=decisions,
                    )
                    save_form, field_forms = None, None
                    status = 200
            except PermissionDenied:
                return private(
                    HttpResponse(
                        "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado",
                        status=403,
                    )
                )
            except (signing.BadSignature, ValueError, TypeError):
                page_errors.append(
                    caption(
                        "Página caducada o inválida / Expired or invalid page",
                        request.LANGUAGE_CODE,
                    )
                )
                status = 409
            except ValidationError as error:
                (save_form or form).add_error(None, error)
                status = 409
    return private(
        render(
            request,
            "safety/rights_portability_select.html",
            {
                "case": case,
                "form": form,
                "catalog": catalog,
                "save_form": save_form,
                "field_forms": field_forms,
                "saved": saved,
                "page_errors": page_errors,
                "reset_form": reset_form,
                "reset_done": reset_done,
            },
            status=status,
        )
    )
