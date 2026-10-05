"""Private per-dataset assessment draft form; GET contains no stored evidence bodies."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import User

from .models import RightsPortabilityAssessment, RightsRequest
from .rights import allowed, fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_portability import BASES, DATASETS, ORIGINS, inspect_assessment, save_assessment
from .views import private


class DraftForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    case_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    source_digest = forms.CharField(min_length=64, max_length=64, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )


class ReadForm(forms.Form):
    operation = forms.ChoiceField(
        choices=[("inspect", "inspect")], widget=forms.HiddenInput, initial="inspect"
    )
    key = forms.UUIDField(widget=forms.HiddenInput)
    case_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    assessment_id = forms.IntegerField(
        min_value=1, label="Referencia de evaluación / Assessment reference"
    )
    purpose = forms.CharField(
        min_length=20, max_length=200, label="Motivo de consulta / Inspection purpose"
    )


def fact(value):
    return {"unknown": None, "yes": True, "no": False}[value]


def fact_field(label):
    return forms.TypedChoiceField(
        choices=[("unknown", "Desconocido / Unknown"), ("yes", "Sí / Yes"), ("no", "No / No")],
        coerce=fact,
        label=label,
    )


LABELS = {
    "profile": ("Perfil", "Profile"),
    "subject_account": ("Cuenta del interesado", "Subject account"),
    "revisions": ("Versiones del anuncio", "Listing revisions"),
    "legal_acceptances": ("Aceptaciones legales", "Legal acceptances"),
    "favorites": ("Favoritos privados", "Private favorites"),
    "personal_contacts": ("Contactos personales", "Personal contacts"),
    "agency_relationships": ("Relaciones con agencias", "Agency relationships"),
    "verifications": ("Verificaciones", "Verifications"),
    "representation_history": ("Historial de representación", "Representation history"),
    "unknown": ("Desconocido", "Unknown"),
    "consent": ("Consentimiento", "Consent"),
    "contract": ("Contrato", "Contract"),
    "legal_obligation": ("Obligación legal", "Legal obligation"),
    "legitimate_interest": ("Interés legítimo", "Legitimate interest"),
    "other": ("Otra base", "Other basis"),
    "provided": ("Facilitados por el interesado", "Provided by the subject"),
    "observed": ("Observados en su actividad", "Observed activity"),
    "inferred": ("Inferidos o derivados", "Inferred or derived"),
    "third_party": ("Facilitados por terceros", "Provided by third parties"),
    "mixed": ("Origen mixto pendiente de separar", "Mixed origin requiring separation"),
}


def translated(name):
    return LABELS[name][1 if (get_language() or "").startswith("en") else 0]


class DatasetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field, values in [("basis", BASES), ("origin", ORIGINS)]:
            self.fields[field].choices = [(name, translated(name)) for name in sorted(values)]

    @property
    def dataset_label(self):
        name = self["dataset"].value()
        return translated(name) if name in LABELS else translated("unknown")

    dataset = forms.ChoiceField(choices=[(x, x) for x in DATASETS], widget=forms.HiddenInput)
    status = forms.ChoiceField(
        choices=[
            ("pending", "Pendiente / Pending"),
            ("eligible", "Elegible / Eligible"),
            ("excluded", "Excluido / Excluded"),
            ("granular", "Evaluar campos mixtos / Assess mixed fields"),
        ],
        label="Decisión / Decision",
    )
    basis = forms.ChoiceField(
        choices=[(x, x) for x in sorted(BASES)], label="Base jurídica / Lawful basis"
    )
    origin = forms.ChoiceField(choices=[(x, x) for x in sorted(ORIGINS)], label="Origen / Origin")
    automated = fact_field("Tratamiento automatizado / Automated processing")
    subject_related = fact_field("Datos del interesado / Data concerning the subject")
    third_party_reviewed = fact_field("Terceros revisados / Third parties reviewed")
    reason = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea,
        label="Justificación / Justification",
    )
    evidence = forms.CharField(
        required=False, max_length=2000, widget=forms.Textarea, label="Evidencia / Evidence"
    )


Datasets = forms.formset_factory(
    DatasetForm, extra=0, min_num=9, max_num=9, absolute_max=9, validate_min=True, validate_max=True
)


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    if not RightsRequest.objects.filter(pk=case_id).exists():
        raise Http404
    try:
        with transaction.atomic():
            case, person, listing = reviewer_case(request.user, case_id)
            actor = User.objects.get(pk=request.user.pk)
            fresh_authority(actor, case, request.user.session_version, request.user.mfa_version)
            if case.kind != "portability" or case.status != "reviewing":
                raise ValidationError("Current portability request required")
            can_prepare(actor, case, person)
            digest = fingerprint(canonical(source_copy(person, listing, case)))
            latest = (
                RightsPortabilityAssessment.objects.filter(request=case, actor=actor)
                .order_by("-version")
                .first()
            )
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    except ValidationError:
        return private(
            HttpResponse("Inspect assigned verified portability request first", status=409)
        )
    reading = request.method == "POST" and request.POST.get("operation") == "inspect"
    draft_data = request.POST if request.method == "POST" and not reading else None
    read_form = ReadForm(
        request.POST if reading else None, initial={"key": uuid4(), "case_version": case.version}
    )
    loaded = []
    form = DraftForm(
        draft_data,
        initial={
            "key": uuid4(),
            "case_version": case.version,
            "version": latest.version if latest else 0,
            "source_digest": digest,
        },
    )
    rows = Datasets(
        draft_data,
        prefix="datasets",
        initial=[
            {
                "dataset": name,
                "status": "pending",
                "basis": "unknown",
                "origin": "unknown",
                "automated": "unknown",
                "subject_related": "unknown",
                "third_party_reviewed": "unknown",
            }
            for name in DATASETS
        ],
    )
    status = 400 if request.method == "POST" else 200
    saved = None
    if reading and read_form.is_valid():
        try:
            _, body = inspect_assessment(
                request.user,
                case.pk,
                **{k: v for k, v in read_form.cleaned_data.items() if k != "operation"},
            )
            loaded = [
                {
                    "label": translated(name),
                    "decision": item["status"],
                    "basis": translated(item["basis"]),
                    "origin": translated(item["origin"]),
                    "reason": item["reason"],
                    "evidence": item["evidence"],
                }
                for name, item in body.items()
            ]
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            read_form.add_error(None, error)
            status = 409
        else:
            status = 200
    elif not reading and request.method == "POST" and form.is_valid() and rows.is_valid():
        decisions = {
            item["dataset"]: {k: v for k, v in item.items() if k != "dataset"}
            for item in rows.cleaned_data
        }
        try:
            saved = save_assessment(
                request.user,
                case.pk,
                assessment=decisions,
                expected_source_digest=form.cleaned_data["source_digest"],
                **{k: v for k, v in form.cleaned_data.items() if k != "source_digest"},
            )
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            status = 200
    return private(
        render(
            request,
            "safety/rights_portability.html",
            {
                "case": case,
                "form": form,
                "datasets": rows,
                "saved": saved,
                "read_form": read_form,
                "loaded": loaded,
            },
            status=status,
        )
    )
