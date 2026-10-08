import json
import secrets
import uuid
from datetime import timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.accounts import limited
from apps.core.models import Agency, AgencyMember, Person
from apps.listings.models import Revision
from apps.listings.moderation import conflict_of_interest

from .crypto import digest, seal, unseal
from .models import Report, ReportAccess, UrgentReportAlert
from .notices import enqueue_ack


class ReportForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    receipt_secret = forms.RegexField(r"^[A-Za-z0-9_-]{43}$", widget=forms.HiddenInput)
    target = forms.CharField(required=False, max_length=1000, widget=forms.HiddenInput)
    mode = forms.ChoiceField(
        choices=[
            ("general", "Denuncia general / General report"),
            ("formal", "Notificación formal / Formal notice"),
        ]
    )
    reason = forms.ChoiceField(
        choices=[
            ("minor", "Menores / Minors"),
            ("exploitation", "Explotación / Exploitation"),
            ("nonconsent", "Sin consentimiento / Without consent"),
            ("illegal", "Contenido ilícito / Illegal content"),
            ("fraud", "Fraude / Fraud"),
            ("other", "Otro / Other"),
        ]
    )
    reference = forms.CharField(
        max_length=600, label="URL o referencia exacta / Exact URL or reference"
    )
    explanation = forms.CharField(
        min_length=20, max_length=4000, widget=forms.Textarea, label="Explicación / Explanation"
    )
    name = forms.CharField(
        required=False, max_length=120, label="Nombre del notificante / Notifier name"
    )
    email = forms.EmailField(required=False, label="Contacto privado / Private contact")
    exception = forms.BooleanField(
        required=False,
        label="Notificación sobre delitos de los artículos 3–7 de la Directiva 2011/93/UE / Notice concerning offences in Articles 3–7 of Directive 2011/93/EU",
    )
    good_faith = forms.BooleanField(
        label="Declaro de buena fe que la información es precisa y completa / I declare in good faith that the information is accurate and complete"
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.language = language
        index = 0 if language == "en" else 1
        labels = {
            "mode": ("Report type", "Tipo de denuncia"),
            "reason": ("Reason", "Motivo"),
            "reference": ("Exact URL or reference", "URL o referencia exacta"),
            "explanation": ("Explanation", "Explicación"),
            "name": ("Notifier name", "Nombre del notificante"),
            "email": ("Private contact", "Contacto privado"),
            "exception": (
                "Notice concerning offences in Articles 3–7 of Directive 2011/93/EU",
                "Notificación sobre delitos de los artículos 3–7 de la Directiva 2011/93/UE",
            ),
            "good_faith": (
                "I declare in good faith that the information is accurate and complete",
                "Declaro de buena fe que la información es precisa y completa",
            ),
        }
        for name, translations in labels.items():
            self.fields[name].label = translations[index]
        choices = {
            "mode": {
                "general": ("General report", "Denuncia general"),
                "formal": ("Formal notice", "Notificación formal"),
            },
            "reason": {
                "minor": ("Minors", "Menores"),
                "exploitation": ("Exploitation", "Explotación"),
                "nonconsent": ("Without consent", "Sin consentimiento"),
                "illegal": ("Illegal content", "Contenido ilícito"),
                "fraud": ("Fraud", "Fraude"),
                "other": ("Other", "Otro"),
            },
        }
        for name, translations in choices.items():
            self.fields[name].choices = [
                (value, translations[value][index]) for value, _ in self.fields[name].choices
            ]

    def clean(self):
        data = super().clean()
        if data.get("mode") == "formal" and not data.get("exception"):
            for field in ["name", "email"]:
                if not data.get(field):
                    self.add_error(
                        field,
                        "Required for formal notice"
                        if self.language == "en"
                        else "Obligatorio para notificación formal",
                    )
        return data


def private(response):
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Referrer-Policy"] = "same-origin"
    return response


@sensitive_post_parameters("receipt_secret", "explanation", "email", "name", "target", "reference")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def submit(request):
    initial = {
        "key": uuid.uuid4(),
        "receipt_secret": secrets.token_urlsafe(32),
        "target": request.GET.get("target", ""),
        "reference": request.GET.get("reference", ""),
    }
    form = ReportForm(request.POST or None, initial=initial, language=request.LANGUAGE_CODE)
    status = 400 if request.method == "POST" else 200
    if request.method == "POST":
        if limited(request, "report-create", limit=20):
            return private(
                HttpResponse(
                    "Too many requests"
                    if request.LANGUAGE_CODE == "en"
                    else "Demasiadas solicitudes",
                    status=429,
                )
            )
        if form.is_valid():
            data = dict(form.cleaned_data)
            key, secret = data.pop("key"), data.pop("receipt_secret")
            revision = None
            try:
                if data["target"]:
                    target = signing.loads(
                        data["target"], salt="public-report-target-v1", max_age=7200
                    )
                    revision = Revision.objects.get(
                        pk=target["revision"], listing_id=target["listing"]
                    )
            except (signing.BadSignature, KeyError, Revision.DoesNotExist, ValueError):
                form.add_error(
                    "target",
                    "Invalid or expired reference"
                    if request.LANGUAGE_CODE == "en"
                    else "Referencia inválida o caducada",
                )
            if not form.errors:
                fingerprint = digest(json.dumps(data, sort_keys=True, ensure_ascii=False))
                with transaction.atomic():
                    report, created = Report.objects.get_or_create(
                        submission_key=key,
                        defaults={
                            "receipt_digest": digest(secret),
                            "payload_digest": fingerprint,
                            "encrypted_payload": seal(data),
                            "actor": request.user if request.user.is_authenticated else None,
                            "listing_id": revision.listing_id if revision else None,
                            "revision": revision,
                            "reported_agency_id": revision.publisher_acceptance.agency_id
                            if revision
                            else None,
                            "reported_individual_id": revision.publisher_acceptance.user_id
                            if revision and not revision.publisher_acceptance.agency_id
                            else None,
                            "reported_subject_id": revision.listing.person.verificationcheck_set.filter(
                                manager_version=revision.manager_version, status="passed"
                            )
                            .order_by("-created_at")
                            .values_list("subject_id", flat=True)
                            .first()
                            if revision
                            else None,
                            "manager_version": revision.manager_version if revision else None,
                            "mode": data["mode"],
                            "reason": data["reason"],
                            "priority": 0
                            if data["reason"] in {"minor", "exploitation", "nonconsent"}
                            else 1,
                            "receipt_expires_at": timezone.now() + timedelta(days=30),
                        },
                    )
                    if created:
                        enqueue_ack(report, data.get("email"))
                        if report.priority == 0:
                            UrgentReportAlert.objects.create(report=report)
                if (
                    not constant_time_compare(report.receipt_digest, digest(secret))
                    or report.payload_digest != fingerprint
                ):
                    form.add_error(
                        None,
                        "Conflicting request replay"
                        if request.LANGUAGE_CODE == "en"
                        else "Solicitud repetida incompatible",
                    )
                    status = 409
                else:
                    return private(redirect("report_receipt", report_id=report.pk, secret=secret))
    return private(render(request, "safety/report.html", {"form": form}, status=status))


@sensitive_variables("secret")
@require_GET
def receipt(request, report_id, secret):
    report = Report.objects.filter(pk=report_id, receipt_expires_at__gt=timezone.now()).first()
    if (
        len(secret) != 43
        or not report
        or not constant_time_compare(report.receipt_digest, digest(secret))
    ):
        raise Http404
    return private(
        render(
            request,
            "safety/receipt.html",
            {
                "report": report,
                "notices": report.notices.only("kind", "status", "created_at").order_by("pk"),
            },
        )
    )


@login_required
@require_GET
def queue(request):
    if (
        not request.user.has_perm("safety.review_report")
        or not request.user.mfa_enabled
        or request.session.get("mfa_version") != request.user.mfa_version
    ):
        return private(HttpResponse("Forbidden", status=403))
    statuses = ["received", "reviewing"]
    if request.user.has_perm("safety.review_restriction"):
        statuses += ["restricted", "upheld"]
    reports = (
        Report.objects.filter(status__in=statuses)
        .exclude(actor=request.user)
        .select_related("listing__person__agency")
    )
    allowed = [report for report in reports if permitted(request.user, report)]
    return private(render(request, "safety/queue.html", {"reports": allowed}))


def permitted(user, report):
    if report.actor_id == user.pk or user.pk in [
        report.reported_individual_id,
        report.reported_subject_id,
    ]:
        return False
    if report.reported_agency_id and (
        report.reported_agency.owner_id == user.pk
        or AgencyMember.objects.filter(agency_id=report.reported_agency_id, user=user).exists()
    ):
        return False
    if report.revision_id and report.manager_version is None:
        return False  # Legacy target without a trustworthy snapshot needs separate triage.
    return not report.listing_id or not conflict_of_interest(user, report.listing.person)


class AccessForm(forms.Form):
    action_before = forms.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807, widget=forms.HiddenInput
    )
    purpose = forms.CharField(
        min_length=10, max_length=200, label="Motivo de consulta / Purpose of access"
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["purpose"].label = (
            "Purpose of access" if language == "en" else "Motivo de consulta"
        )


@login_required
@sensitive_post_parameters("purpose")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inspect(request, report_id):
    if (
        not request.user.has_perm("safety.review_report")
        or not request.user.mfa_enabled
        or request.session.get("mfa_version") != request.user.mfa_version
    ):
        return private(
            HttpResponse(
                ("Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado"), status=403
            )
        )
    report = (
        Report.objects.select_related("listing__person__agency", "reported_agency")
        .filter(pk=report_id)
        .first()
    )
    if not report:
        raise Http404
    if not permitted(request.user, report):
        return private(
            HttpResponse(
                (
                    "Conflict of interest"
                    if request.LANGUAGE_CODE == "en"
                    else "Conflicto de interés"
                ),
                status=403,
            )
        )
    form = AccessForm(request.POST or None, language=request.LANGUAGE_CODE)
    payload = None
    history = []
    next_action_cursor = None
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            person = report.listing.person if report.listing_id else None
            agency_ids = {
                value
                for value in [report.reported_agency_id, person.agency_id if person else None]
                if value
            }
            list(Agency.objects.select_for_update().filter(pk__in=agency_ids).order_by("pk"))
            if person:
                previous_agency = person.agency_id
                person = Person.objects.select_for_update().get(pk=person.pk)
                if person.agency_id != previous_agency:
                    return private(
                        HttpResponse(
                            (
                                "Management changed; reload"
                                if request.LANGUAGE_CODE == "en"
                                else "La gestión ha cambiado; recarga"
                            ),
                            status=409,
                        )
                    )
            report = (
                Report.objects.select_for_update(of=("self",))
                .select_related("listing__person__agency", "reported_agency")
                .get(pk=report_id)
            )
            if person:
                report.listing.person = person
            if not permitted(request.user, report):
                return private(
                    HttpResponse(
                        (
                            "Conflict of interest"
                            if request.LANGUAGE_CODE == "en"
                            else "Conflicto de interés"
                        ),
                        status=403,
                    )
                )
            payload = unseal(report.encrypted_payload)
            ReportAccess.objects.create(
                report=report,
                actor=request.user,
                purpose=form.cleaned_data["purpose"],
                case_version=report.version,
                action_before=form.cleaned_data["action_before"],
            )
            actions = report.actions.order_by("-pk")
            if form.cleaned_data["action_before"]:
                actions = actions.filter(pk__lt=form.cleaned_data["action_before"])
            records = list(actions[:51])
            for action in records[:50]:
                history.append(
                    {
                        "actor_id": action.actor_id,
                        "created_at": action.created_at,
                        "operation": action.operation,
                        "expected_version": action.expected_version,
                        "reason": unseal(action.encrypted_reason)["reason"],
                    }
                )
            if len(records) > 50:
                next_action_cursor = records[49].pk
    return private(
        render(
            request,
            "safety/inspect.html",
            {
                "report": report,
                "form": form,
                "payload": payload,
                "history": history,
                "next_action_cursor": next_action_cursor,
            },
            status=400 if request.method == "POST" and not form.is_valid() else 200,
        )
    )


class DecisionForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    manager_version = forms.IntegerField(required=False, min_value=1, widget=forms.HiddenInput)
    revision_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    link_listing_id = forms.UUIDField(
        required=False, label="ID del anuncio referenciado / Referenced listing ID"
    )
    operation = forms.ChoiceField(
        choices=[
            ("claim", "Asignarme el caso / Assign case to me"),
            ("unassign", "Devolver caso a cola / Return case to queue"),
            (
                "uphold",
                "Confirmar restricción (revisión independiente) / Uphold restriction (independent review)",
            ),
            (
                "lift",
                "Levantar restricción (revisión independiente) / Lift restriction (independent review)",
            ),
            ("link", "Enlazar referencia a anuncio / Link reference to listing"),
            ("restrict", "Restringir publicación / Restrict publication"),
            ("dismiss", "Desestimar denuncia / Dismiss report"),
        ]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado fundamentado / Private reason with evidence",
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def decision(request, report_id):
    from .decisions import act

    if (
        not request.user.has_perm("safety.review_report")
        or not request.user.mfa_enabled
        or request.session.get("mfa_version") != request.user.mfa_version
    ):
        return private(HttpResponse("Forbidden", status=403))
    report = (
        Report.objects.filter(pk=report_id)
        .select_related("listing__person__agency", "reported_agency")
        .first()
    )
    if not report:
        raise Http404
    if not permitted(request.user, report):
        return private(HttpResponse("Conflict of interest", status=403))
    form = DecisionForm(
        request.POST or None,
        initial={
            "key": uuid.uuid4(),
            "version": report.version,
            "manager_version": report.listing.person.manager_version if report.listing_id else None,
            "revision_id": report.listing.approved_revision_id if report.listing_id else None,
        },
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            act(request.user, report_id, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("report_inspect", report_id=report.pk))
    return private(
        render(request, "safety/decision.html", {"form": form, "report": report}, status=status)
    )
