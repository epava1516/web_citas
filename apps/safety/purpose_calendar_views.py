"""Private operational follow-up with explicit audited history reads."""

import uuid
from datetime import date, datetime, timedelta

from cryptography.fernet import InvalidToken
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from .crypto import seal, unseal
from .models import PurposeRestriction
from .purpose_calendar import permission, record
from .rights import allowed
from .views import private


class FollowUpForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    case_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consultar historial / Inspect history"),
            ("follow_up", "Registrar seguimiento / Record follow-up"),
        ]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo interno minimizado / Minimized internal reason",
    )
    next_review_on = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Próxima revisión operativa / Next operational review",
    )
    history_before = forms.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807, widget=forms.HiddenInput
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        english = language == "en"
        self.fields["operation"].label = "Operation" if english else "Operación"
        self.fields["operation"].choices = [
            ("inspect", "Inspect history" if english else "Consultar historial"),
            ("follow_up", "Record follow-up" if english else "Registrar seguimiento"),
        ]
        self.fields["reason"].label = (
            "Minimized internal reason" if english else "Motivo interno minimizado"
        )
        self.fields["next_review_on"].label = (
            "Next operational review" if english else "Próxima revisión operativa"
        )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def detail(request, restriction_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    restriction = (
        PurposeRestriction.objects.select_related("execution__action__request")
        .filter(pk=restriction_id)
        .first()
    )
    if not restriction:
        raise Http404
    case = restriction.execution.action.request
    try:
        permission(request.user, case, restriction)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    initial = {"key": uuid.uuid4(), "version": restriction.version, "case_version": case.version}
    form = FollowUpForm(request.POST or None, initial=initial, language=request.LANGUAGE_CODE)
    snapshot, recorded = None, False
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            _, snapshot = record(request.user, restriction.pk, **form.cleaned_data)
            recorded = form.cleaned_data["operation"] == "follow_up"
            restriction.refresh_from_db()
            form = FollowUpForm(
                language=request.LANGUAGE_CODE,
                initial={
                    "key": uuid.uuid4(),
                    "version": restriction.version,
                    "case_version": case.version,
                },
            )
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/purpose_calendar_detail.html",
            {
                "restriction": restriction,
                "case": case,
                "form": form,
                "snapshot": snapshot,
                "recorded": recorded,
            },
            status=status,
        )
    )


class CalendarFilterForm(forms.Form):
    attention = forms.ChoiceField(
        choices=[
            ("due", "Vencidas / Due"),
            ("soon", "Próximos siete días / Next seven days"),
            ("all", "Todas / All"),
        ]
    )
    purpose = forms.ChoiceField(
        required=False,
        choices=[("", "Todas / All"), ("account_preferences", "Preferencias / Preferences")],
    )
    mode = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Todos / All"),
            ("restrict", "Limitación / Restriction"),
            ("cease", "Cese / Cessation"),
        ],
    )


@login_required
@require_GET
def queue(request):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + name)
        for name in ["execute_rights_request", "review_purpose_calendar"]
    ):
        return private(HttpResponse("Forbidden", status=403))
    values = request.GET.copy()
    if "attention" not in values:
        values["attention"] = "due"
    form = CalendarFilterForm(values)
    if not form.is_valid():
        return private(HttpResponse("Invalid filters / Filtros inválidos", status=400))
    filters = form.cleaned_data
    rows = PurposeRestriction.objects.filter(active=True).select_related(
        "execution__action__request__person",
        "execution__action__request__referenced_revision__publisher_acceptance",
    )
    if filters["attention"] != "all":
        rows = rows.filter(
            review_on__lte=timezone.localdate()
            + timedelta(days=7 if filters["attention"] == "soon" else 0)
        )
    for field in ["purpose", "mode"]:
        if filters[field]:
            rows = rows.filter(**{field: filters[field]})
    cursor = request.GET.get("cursor")
    if cursor:
        try:
            token = unseal(cursor)
            if (
                token["user"] != request.user.pk
                or token["session"] != request.user.session_version
                or token["mfa"] != request.user.mfa_version
                or token["filters"] != filters
                or datetime.fromisoformat(token["expires"]) <= timezone.now()
            ):
                raise ValueError
            day = date.fromisoformat(token["review_on"])
            pk = token["pk"]
            if not isinstance(pk, int) or not 1 <= pk <= 9223372036854775807:
                raise ValueError
        except (InvalidToken, ValueError, KeyError, TypeError):
            return private(HttpResponse("Invalid cursor / Cursor inválido", status=400))
        rows = rows.filter(Q(review_on__gt=day) | Q(review_on=day, pk__gt=pk))
    candidates = list(rows.order_by("review_on", "pk")[:101])
    visible = []
    for restriction in candidates[:100]:
        case = restriction.execution.action.request
        try:
            permission(request.user, case, restriction)
        except PermissionDenied:
            continue
        visible.append(restriction)
    next_cursor = None
    if len(candidates) > 100:
        last = candidates[99]
        next_cursor = seal(
            {
                "user": request.user.pk,
                "session": request.user.session_version,
                "mfa": request.user.mfa_version,
                "filters": filters,
                "expires": (timezone.now() + timedelta(hours=1)).isoformat(),
                "review_on": last.review_on.isoformat(),
                "pk": last.pk,
            }
        )
    query = request.GET.copy()
    query.pop("cursor", None)
    return private(
        render(
            request,
            "safety/purpose_calendar_queue.html",
            {
                "form": form,
                "restrictions": visible,
                "next_cursor": next_cursor,
                "filters": query.urlencode(),
            },
        )
    )
