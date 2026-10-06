"""Private final response preparation; no content reads on GET."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import (
    RightsAccessCoverageReview,
    RightsAccessResponseDraft,
    RightsAccessResponseReview,
    RightsAccessScopeInventory,
    RightsAction,
    RightsExport,
    RightsRequest,
)
from .rights import allowed
from .rights_access_response_draft import prepare
from .rights_access_response_review import authorize_reviewer, inspect, record
from .rights_copy_page_review import fresh_authority
from .rights_responses import ResponseForm
from .views import private


class DraftForm(ResponseForm):
    scope_inventory = forms.ModelChoiceField(
        queryset=RightsAccessScopeInventory.objects.none(),
        required=False,
        label="Inventario para paquete de acceso / Access package inventory",
    )
    delivery_decisions = forms.JSONField(
        required=False,
        widget=forms.Textarea,
        label="Decisiones por grupos y recursos / Group and resource decisions",
    )

    coverage_review = forms.ModelChoiceField(
        queryset=RightsAccessCoverageReview.objects.none(),
        required=False,
        label="Contabilidad aprobada / Approved accounting",
    )
    export = forms.ModelChoiceField(
        queryset=RightsExport.objects.none(),
        label="Copia con información aprobada / Copy with approved information",
    )

    def __init__(self, *args, case, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("kind")
        self.fields["scope_inventory"].queryset = (
            RightsAccessScopeInventory.objects.filter(
                request=case,
                actor=actor,
                case_version=case.version,
                response_version=case.response_version,
                purged_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .only("pk")
            .order_by("-pk")
        )

        self.fields["coverage_review"].queryset = (
            RightsAccessCoverageReview.objects.filter(
                coverage__request=case,
                coverage__actor=actor,
                coverage__case_version=case.version,
                coverage__response_version=case.response_version,
                coverage__purged_at__isnull=True,
                coverage__expires_at__gt=timezone.now(),
                outcome="approved",
            )
            .only("pk")
            .order_by("-pk")
        )

        self.fields["export"].queryset = (
            RightsExport.objects.filter(
                action__request=case,
                action__actor=actor,
                information_binding__review__outcome="approved",
                expires_at__gt=timezone.now(),
                purged_at__isnull=True,
            )
            .only("pk")
            .order_by("-created_at")
        )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare_response(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        fresh_authority(request.user, case, request.user.session_version, request.user.mfa_version)
        if case.assigned_to_id != request.user.pk or not request.user.has_perm(
            "safety.respond_rights_request"
        ):
            raise PermissionDenied
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    if case.kind != "access" or case.status != "reviewing":
        return private(HttpResponse("Current access request required", status=409))
    form = DraftForm(
        request.POST if request.method == "POST" else None,
        case=case,
        actor=request.user,
        initial={
            "key": uuid4(),
            "version": case.version,
            "response_version": case.response_version,
        },
    )
    draft = None
    package_preview = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            inspecting = request.POST.get("operation") == "inspect_package"
            prepared = prepare(
                request.user,
                case.pk,
                values["version"],
                values["response_version"],
                values["export"].pk,
                values["key"],
                values["reason"],
                values["response"],
                values["redaction_confirmed"],
                scope_inventory_id=values["scope_inventory"].pk
                if values["scope_inventory"]
                else None,
                delivery_decisions=values["delivery_decisions"],
                coverage_review_id=values["coverage_review"].pk
                if values["coverage_review"]
                else None,
                inspect_only=inspecting,
            )
            if inspecting:
                package_preview = prepared
                initial = dict(values)
                initial["key"] = uuid4()
                initial["delivery_decisions"] = {
                    "models": {
                        label: {"status": "pending", "reason": ""}
                        for label in package_preview["groups"]
                    },
                    "resources": {
                        "status": "pending",
                        "reason": "",
                        **(
                            {"origin_digest": package_preview["resource_scope"]["digest"]}
                            if package_preview["resource_scope"].get("configured")
                            else {}
                        ),
                    },
                }
            else:
                draft = prepared
                initial = {
                    "key": uuid4(),
                    "version": case.version,
                    "response_version": case.response_version,
                }
            form = DraftForm(case=case, actor=request.user, initial=initial)
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/rights_access_response.html",
            {
                "case": case,
                "form": form,
                "draft": draft,
                "package_preview": package_preview,
                "english": request.LANGUAGE_CODE == "en",
                "approved_drafts": RightsAccessResponseReview.objects.filter(
                    draft__request=case,
                    draft__actor=request.user,
                    outcome="approved",
                    draft__case_version=case.version,
                    draft__response_version=case.response_version,
                    draft__purged_at__isnull=True,
                    draft__expires_at__gt=timezone.now(),
                )
                .only("pk", "draft_id")
                .order_by("-pk")[:50],
            },
            status=status,
        )
    )


class ReviewForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado / Private purpose",
    )


class DecisionForm(ReviewForm):
    read_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[("approved", "Aprobar / Approve"), ("rejected", "Rechazar / Reject")],
        label="Decisión / Decision",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["id"] = "decision_" + name


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def review_response(request, case_id, draft_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        authorize_reviewer(request.user, case)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    draft = (
        RightsAccessResponseDraft.objects.filter(pk=draft_id, request=case)
        .only("pk", "actor_id", "export_id", "expires_at")
        .first()
    )
    if draft is None:
        raise Http404
    if draft.actor_id == request.user.pk:
        return private(HttpResponse("Independent reviewer required", status=403))
    initial = {"key": uuid4(), "version": case.version}
    form = ReviewForm(initial=initial)
    decision_form = DecisionForm(initial={"key": uuid4(), "version": case.version})
    public = decision = None
    status = 200
    if request.method == "POST":
        decision_mode = request.POST.get("operation") == "review"
        active = DecisionForm(request.POST) if decision_mode else ReviewForm(request.POST)
        if decision_mode:
            decision_form = active
        else:
            form = active
        status = 400
        if active.is_valid():
            values = active.cleaned_data
            try:
                if decision_mode:
                    decision = record(
                        request.user,
                        case.pk,
                        values["version"],
                        draft.pk,
                        values["read_id"],
                        values["key"],
                        values["reason"],
                        values["outcome"],
                    )
                else:
                    _, public = inspect(
                        request.user,
                        case.pk,
                        values["version"],
                        draft.pk,
                        values["key"],
                        values["reason"],
                    )
                    read_id = RightsAction.objects.get(key=values["key"]).pk
                    decision_form = DecisionForm(
                        initial={"key": uuid4(), "version": case.version, "read_id": read_id}
                    )
                status = 200
            except PermissionDenied:
                return private(HttpResponse("Forbidden", status=403))
            except ValidationError as error:
                active.add_error(None, error)
                status = 409
    return private(
        render(
            request,
            "safety/rights_access_response_review.html",
            {
                "case": case,
                "draft": draft,
                "form": form,
                "decision_form": decision_form,
                "public": public,
                "decision": decision,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )
