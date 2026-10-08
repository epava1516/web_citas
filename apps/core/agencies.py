import hashlib
import secrets
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from apps.listings.forms import validate_listing_text

from .accounts import limited
from .models import Agency, AgencyInvitation, AgencyMember, Person, User


def person_queryset(user):
    return (
        (
            Person.objects.filter(individual=user)
            | Person.objects.filter(agency__owner=user)
            | Person.objects.filter(
                agency__memberships__user=user,
                agency__memberships__active=True,
                assigned_editor=user,
            )
        )
        .filter(publication_erased_at__isnull=True)
        .distinct()
    )


def pending_person_count(agency):
    return agency.people.exclude(
        listing__approved_revision__manager_version=F("manager_version")
    ).count()


def can_manage_person(user, person):
    return person_queryset(user).filter(pk=person.pk).exists()


def owned_agency(user, agency_id):
    return get_object_or_404(Agency, pk=agency_id, owner=user)


class AgencyForm(forms.Form):
    name = forms.CharField(label="Nombre de agencia / Agency name", max_length=120)

    def clean_name(self):
        return validate_listing_text(self.cleaned_data["name"])

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].label = "Agency name" if language == "en" else "Nombre de agencia"


class InvitationForm(forms.Form):
    email = forms.EmailField(label="Email del editor / Editor email")

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "Editor email" if language == "en" else "Email del editor"


class PersonForm(forms.Form):
    alias = forms.CharField(label="Alias público / Public alias", max_length=80)

    def clean_alias(self):
        return validate_listing_text(self.cleaned_data["alias"])

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alias"].label = "Public alias" if language == "en" else "Alias público"


class AssignmentForm(forms.Form):
    editor = forms.ModelChoiceField(queryset=User.objects.none(), required=False, label="Editor")

    def __init__(self, *args, agency, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["editor"].queryset = User.objects.filter(
            agency_memberships__agency=agency, agency_memberships__active=True
        )


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if (
        not request.user.mfa_enabled
        or request.session.get("mfa_version") != request.user.mfa_version
    ):
        return redirect("mfa_enroll" if not request.user.mfa_enabled else "mfa_challenge")
    if Agency.objects.filter(owner=request.user).exists():
        return redirect("agency_panel", agency_id=request.user.owned_agency.pk)
    if Person.objects.filter(individual=request.user).exists():
        return HttpResponse(
            "Transferencia de gestor requerida / Manager transfer required", status=409
        )
    form = AgencyForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if user.account_erased_at or not user.is_active:
                return HttpResponse("Account access revoked", status=409)
            agency, _ = Agency.objects.get_or_create(
                owner=user, defaults={"name": form.cleaned_data["name"]}
            )
            user.role = "agency"
            user.save(update_fields=["role"])
        return redirect("agency_panel", agency_id=agency.pk)
    return render(request, "core/form.html", {"form": form, "kind": "agency"})


@login_required
def panel(request, agency_id):
    agency = get_object_or_404(Agency, pk=agency_id)
    owner = agency.owner_id == request.user.pk
    if (
        not owner
        and not AgencyMember.objects.filter(agency=agency, user=request.user, active=True).exists()
    ):
        return HttpResponse("Forbidden", status=403)
    people = agency.people.all() if owner else agency.people.filter(assigned_editor=request.user)
    return render(
        request,
        "core/agency.html",
        {
            "agency": agency,
            "people": people,
            "owner": owner,
            "members": agency.memberships.filter(active=True) if owner else [],
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def invite(request, agency_id):
    agency = owned_agency(request.user, agency_id)
    form = InvitationForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST":
        if limited(request, "agency-invite", 10):
            return HttpResponse("Too many attempts", status=429)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            raw = secrets.token_urlsafe(32)
            invitation = AgencyInvitation.objects.create(
                agency=agency,
                email=email,
                digest=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=timezone.now() + timedelta(days=2),
            )
            url = (
                settings.PUBLIC_ORIGIN
                + f"/{request.LANGUAGE_CODE}/agency/invitation/{invitation.pk}/{raw}/"
            )
            send_mail(
                "Invitación de editor / Editor invitation",
                url,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
            return redirect("agency_panel", agency_id=agency.pk)
    return render(request, "core/form.html", {"form": form, "kind": "invite"})


@login_required
@require_http_methods(["GET", "POST"])
def accept_invitation(request, invitation_id, raw):
    invitation = get_object_or_404(
        AgencyInvitation, pk=invitation_id, digest=hashlib.sha256(raw.encode()).hexdigest()
    )
    if (
        invitation.email != request.user.email.lower()
        or invitation.revoked_at
        or invitation.accepted_at
        or invitation.expires_at <= timezone.now()
    ):
        return HttpResponse("Invitación no disponible / Invitation unavailable", status=403)
    if (
        not request.user.mfa_enabled
        or request.session.get("mfa_version") != request.user.mfa_version
    ):
        return redirect("mfa_enroll" if not request.user.mfa_enabled else "mfa_challenge")
    if request.method == "POST":
        with transaction.atomic():
            Agency.objects.select_for_update().get(pk=invitation.agency_id)
            invitation = AgencyInvitation.objects.select_for_update().get(pk=invitation.pk)
            if (
                invitation.revoked_at
                or invitation.accepted_at
                or invitation.expires_at <= timezone.now()
            ):
                return HttpResponse("Invitation unavailable", status=409)
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if user.account_erased_at or not user.is_active:
                return HttpResponse("Account access revoked", status=409)
            AgencyMember.objects.update_or_create(
                agency=invitation.agency, user=user, defaults={"active": True}
            )
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["accepted_at"])
        return redirect("agency_panel", agency_id=invitation.agency_id)
    return render(request, "core/invitation.html", {"agency": invitation.agency})


@login_required
@require_POST
def revoke_member(request, agency_id, member_id):
    agency = owned_agency(request.user, agency_id)
    with transaction.atomic():
        Agency.objects.select_for_update().get(pk=agency.pk)
        membership = get_object_or_404(
            AgencyMember.objects.select_for_update(), pk=member_id, agency=agency
        )
        membership.active = False
        membership.save(update_fields=["active"])
        AgencyInvitation.objects.filter(
            agency=agency,
            email=membership.user.email,
            accepted_at__isnull=True,
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())
        Person.objects.filter(agency=agency, assigned_editor=membership.user).update(
            assigned_editor=None
        )
    return redirect("agency_panel", agency_id=agency.pk)


@login_required
@require_http_methods(["GET", "POST"])
def add_person(request, agency_id):
    agency = owned_agency(request.user, agency_id)
    form = PersonForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            Agency.objects.select_for_update().get(pk=agency.pk)
            pending_people = pending_person_count(agency)
            if pending_people >= settings.AGENCY_PENDING_PERSON_LIMIT:
                return HttpResponse(
                    "Cuota pendiente de revisión / Quota awaiting review", status=409
                )
            Person.objects.create(agency=agency, alias=form.cleaned_data["alias"])
        return redirect("agency_panel", agency_id=agency.pk)
    return render(request, "core/form.html", {"form": form, "kind": "person"})


@login_required
@require_http_methods(["GET", "POST"])
def assign(request, agency_id, person_id):
    agency = owned_agency(request.user, agency_id)
    person = get_object_or_404(Person, pk=person_id, agency=agency)
    form = AssignmentForm(
        request.POST or None, agency=agency, initial={"editor": person.assigned_editor_id}
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            Agency.objects.select_for_update().get(pk=agency.pk)
            # Lock membership to serialize with revocation; never trust the dropdown alone.
            editor = form.cleaned_data["editor"]
            if (
                editor
                and not AgencyMember.objects.select_for_update()
                .filter(agency=agency, user=editor, active=True)
                .exists()
            ):
                return HttpResponse("Editor revoked", status=409)
            person.assigned_editor = editor
            person.save(update_fields=["assigned_editor"])
        return redirect("agency_panel", agency_id=agency.pk)
    return render(request, "core/form.html", {"form": form, "kind": "assign"})
