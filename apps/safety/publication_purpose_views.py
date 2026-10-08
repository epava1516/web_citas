"""Private publication purpose inspection, notification and release interface."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .models import PrivacyPublicationHold, RightsRequest
from .processing_review import authorize
from .publication_purpose_calendar import follow_up, history
from .publication_purpose_release import execute, inspect, permission, propose
from .purpose_release_views import ReleaseForm
from .rights import allowed
from .views import private


class PublicationReleaseForm(ReleaseForm):
    operation = forms.ChoiceField(
        choices=ReleaseForm.base_fields["operation"].choices
        + [
            ("follow_up", "Registrar seguimiento / Record follow-up"),
            ("history", "Consultar historial / Inspect history"),
        ]
    )
    history_before = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=9223372036854775807,
        label="Cursor de historial / History cursor",
    )
    hold_version = forms.IntegerField(
        required=False, min_value=1, label="Versión de medida / Measure version"
    )
    next_review_on = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Próxima revisión / Next review",
    )
    read_id = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=9223372036854775807,
        label="Consulta auditada / Audited inspection",
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, language=language, **kwargs)
        labels = {
            "history_before": ("Cursor de historial", "History cursor"),
            "hold_version": ("Versión de medida", "Measure version"),
            "next_review_on": ("Próxima revisión", "Next review"),
            "read_id": ("Consulta auditada", "Audited inspection"),
        }
        for name, pair in labels.items():
            self.fields[name].label = pair[language == "en"]

    def clean(self):
        values = super().clean()
        field = {"propose": "read_id", "execute": "proposal_id"}.get(values.get("operation"))
        if field and not values.get(field):
            self.add_error(
                field, "Reference required" if self.language == "en" else "Referencia obligatoria"
            )
        if values.get("operation") == "follow_up":
            for name in ["hold_version", "next_review_on"]:
                if not values.get(name):
                    self.add_error(
                        name, "Required field" if self.language == "en" else "Campo obligatorio"
                    )
        return values


@login_required
@sensitive_post_parameters("reason")
@require_http_methods(["GET", "POST"])
def release(request, case_id, hold_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    hold = (
        PrivacyPublicationHold.objects.select_related("action")
        .filter(
            pk=hold_id,
            action__request=case,
            purpose_execution__isnull=False,
        )
        .first()
    )
    if not case or not hold:
        raise Http404
    try:
        fresh = authorize(request.user, case, review_permission=False)
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    can_calendar = fresh.has_perm("safety.review_purpose_calendar")
    try:
        permission(request.user, case, hold)
        can_release = True
    except PermissionDenied:
        can_release = False
    if not can_calendar and not can_release:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    operation = request.POST.get("operation") if request.method == "POST" else None
    if (operation in {"follow_up", "history"} and not can_calendar) or (
        operation in {"inspect", "propose", "execute"} and not can_release
    ):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = PublicationReleaseForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid4(), "version": case.version, "hold_version": hold.version},
    )
    available_choices = [
        item
        for item in form.fields["operation"].choices
        if (item[0] in {"follow_up", "history"} and can_calendar)
        or (item[0] not in {"follow_up", "history"} and can_release)
    ]
    form.fields["operation"].choices = available_choices
    body, reading, proposal = None, None, None
    history_result = None
    follow_up_recorded = False
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        v = form.cleaned_data
        try:
            if v["operation"] == "inspect":
                reading, body = inspect(
                    request.user, case.pk, hold.pk, v["key"], v["version"], v["reason"]
                )
            elif v["operation"] == "history":
                _, history_result = history(
                    request.user,
                    case.pk,
                    hold.pk,
                    v["key"],
                    v["version"],
                    v["reason"],
                    v["history_before"],
                )
            elif v["operation"] == "follow_up":
                follow_up(
                    request.user,
                    case.pk,
                    hold.pk,
                    v["key"],
                    v["version"],
                    v["hold_version"],
                    v["reason"],
                    v["next_review_on"],
                )
                follow_up_recorded = True
            elif v["operation"] == "propose":
                proposal = propose(
                    request.user,
                    case.pk,
                    hold.pk,
                    v["key"],
                    v["version"],
                    v["read_id"],
                    v["reason"],
                    v["ground"],
                    v["resume_message_id"],
                )
            else:
                proposal = execute(
                    request.user,
                    case.pk,
                    hold.pk,
                    v["proposal_id"],
                    v["key"],
                    v["version"],
                    v["reason"],
                )
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            case.refresh_from_db()
            hold.refresh_from_db()
            form = PublicationReleaseForm(
                language=request.LANGUAGE_CODE,
                initial={
                    "key": uuid4(),
                    "version": case.version,
                    "hold_version": hold.version,
                    "read_id": reading.pk if reading else None,
                    "proposal_id": proposal.pk if proposal else None,
                },
            )
            form.fields["operation"].choices = available_choices
            status = 200
    return private(
        render(
            request,
            "safety/publication_purpose_release.html",
            {
                "case": case,
                "form": form,
                "decision": body,
                "history_result": history_result,
                "reading": reading,
                "proposal": proposal,
                "follow_up_recorded": follow_up_recorded,
                "can_calendar": can_calendar,
            },
            status=status,
        )
    )
