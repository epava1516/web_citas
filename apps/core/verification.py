import hashlib
import secrets
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.http import require_http_methods, require_POST

from .accounts import limited
from .agencies import PersonForm, pending_person_count, person_queryset
from .models import (
    Agency,
    LegalDocument,
    Person,
    PhoneChallenge,
    PhoneClaim,
    RepresentationAction,
    RepresentationInvitation,
    User,
)
from .verification_services import (
    normalize_phone,
    publication_ready,
    receive_event,
    simulate_event,
    start_age_check,
)


def locked_manager_person(user, person_id):
    snapshot = Person.objects.get(pk=person_id)
    if snapshot.agency_id:
        Agency.objects.select_for_update().get(pk=snapshot.agency_id)
    person = Person.objects.select_for_update().get(pk=person_id)
    if person.individual_id == user.pk or (person.agency_id and person.agency.owner_id == user.pk):
        return person
    if person.assigned_editor_id == user.pk and person.agency_id:
        from .models import AgencyMember

        if (
            AgencyMember.objects.select_for_update()
            .filter(agency_id=person.agency_id, user=user, active=True)
            .exists()
        ):
            return person
    from django.core.exceptions import PermissionDenied

    raise PermissionDenied("Manager access revoked")


class PhoneForm(forms.Form):
    phone = forms.CharField(label="Teléfono / Phone", max_length=30)

    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"])


class CodeForm(forms.Form):
    code = forms.CharField(label="Código / Code", max_length=6, min_length=6)


class ConsentInviteForm(forms.Form):
    email = forms.EmailField(label="Correo privado de la persona / Person's private email")


class ConsentForm(forms.Form):
    authorize = forms.BooleanField(
        label="Autorizo a este gestor para este perfil / I authorize this manager for this profile"
    )
    version = forms.CharField(widget=forms.HiddenInput)


class SimulationForm(forms.Form):
    outcome = forms.ChoiceField(
        label="Resultado simulado / Simulated result",
        choices=[("pending", "Pending"), ("failed", "Failed"), ("passed", "Passed")],
    )


class TransferForm(forms.Form):
    manager_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    target_agency = forms.UUIDField(
        required=False,
        label="ID de nueva agencia; vacío para gestionar personalmente / New agency ID; empty for self-management",
    )
    confirm = forms.BooleanField(
        label="Confirmo el cambio y una nueva autorización / I confirm the change and new authorization"
    )


@login_required
@require_http_methods(["GET", "POST"])
def individual(request):
    if request.user.role == "agency":
        return HttpResponse("Use agency management", status=409)
    existing = Person.objects.filter(individual=request.user).first()
    if existing:
        return redirect("person_verification", person_id=existing.pk)
    if Person.objects.filter(subject=request.user).exists():
        return HttpResponse("Use representation transfer", status=409)
    form = PersonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            person, _ = Person.objects.get_or_create(
                individual=user, defaults={"alias": form.cleaned_data["alias"], "subject": user}
            )
            user.role = "individual"
            user.save(update_fields=["role"])
        return redirect("person_verification", person_id=person.pk)
    return render(request, "core/form.html", {"form": form, "kind": "person"})


@login_required
def status(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    manager = person_queryset(request.user).filter(pk=person.pk).exists()
    subject = person.subject_id == request.user.pk
    if not manager and not subject:
        return HttpResponse("Forbidden", status=403)
    return render(
        request,
        "core/verification.html",
        {
            "person": person,
            "manager": manager,
            "subject": subject,
            "ready": publication_ready(person),
            "checks": person.verificationcheck_set.order_by("-created_at")[:5],
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def invite_consent(request, person_id):
    person = get_object_or_404(person_queryset(request.user), pk=person_id)
    if not person.agency_id or person.agency.owner_id != request.user.pk:
        return HttpResponse("Forbidden", status=403)
    form = ConsentInviteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if limited(request, "representation-invite", 5):
            return HttpResponse("Too many attempts", status=429)
        raw = secrets.token_urlsafe(32)
        invitation = RepresentationInvitation.objects.create(
            person=person,
            email=form.cleaned_data["email"].lower(),
            manager_version=person.manager_version,
            digest=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(days=2),
        )
        url = (
            settings.PUBLIC_ORIGIN
            + f"/{request.LANGUAGE_CODE}/representation/{invitation.pk}/{raw}/"
        )
        send_mail(
            "Autorización específica / Specific authorization",
            url,
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=True,
        )
        return redirect("person_verification", person_id=person.pk)
    return render(request, "core/form.html", {"form": form, "kind": "invite"})


@login_required
@require_http_methods(["GET", "POST"])
def accept_consent(request, invitation_id, raw):
    invitation = get_object_or_404(
        RepresentationInvitation, pk=invitation_id, digest=hashlib.sha256(raw.encode()).hexdigest()
    )
    if (
        invitation.email != request.user.email.lower()
        or invitation.used_at
        or invitation.expires_at <= timezone.now()
    ):
        return HttpResponse("Authorization unavailable", status=403)
    document = get_object_or_404(
        LegalDocument, slug="publishing", language=request.LANGUAGE_CODE, active=True
    )
    form = ConsentForm(request.POST or None, initial={"version": document.version})
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data["version"] != document.version:
            form.add_error(None, "Document updated / Documento actualizado")
        else:
            try:
                with transaction.atomic():
                    Person.objects.select_for_update().get(pk=invitation.person_id)
                    invitation = RepresentationInvitation.objects.select_for_update().get(
                        pk=invitation.pk
                    )
                    person = invitation.person
                    if (
                        invitation.used_at
                        or invitation.manager_version != person.manager_version
                        or invitation.expires_at <= timezone.now()
                    ):
                        return HttpResponse("Authorization obsolete", status=409)
                    if person.subject_id and person.subject_id != request.user.pk:
                        return HttpResponse("Subject conflict", status=409)
                    person.subject = request.user
                    person.consent_version = person.manager_version
                    person.consent_revoked_at = None
                    person.save(update_fields=["subject", "consent_version", "consent_revoked_at"])
                    RepresentationAction.objects.create(
                        person=person,
                        subject=request.user,
                        manager_version=person.manager_version,
                        action="grant",
                        document=document,
                    )
                    invitation.used_at = timezone.now()
                    invitation.save(update_fields=["used_at"])
                return redirect("person_verification", person_id=person.pk)
            except IntegrityError:
                return HttpResponse("Use transfer of existing person", status=409)
    return render(
        request,
        "core/representation.html",
        {"person": invitation.person, "form": form, "document": document},
    )


@login_required
@require_http_methods(["GET", "POST"])
def self_consent(request, person_id):
    person = get_object_or_404(Person, pk=person_id, individual=request.user, subject=request.user)
    document = get_object_or_404(
        LegalDocument, slug="publishing", language=request.LANGUAGE_CODE, active=True
    )
    form = ConsentForm(request.POST or None, initial={"version": document.version})
    if (
        request.method == "POST"
        and form.is_valid()
        and form.cleaned_data["version"] == document.version
    ):
        with transaction.atomic():
            person = Person.objects.select_for_update().get(pk=person.pk)
            if person.individual_id != request.user.pk:
                return HttpResponse("Manager changed", status=409)
            current_grant = RepresentationAction.objects.filter(
                person=person,
                subject=request.user,
                manager_version=person.manager_version,
                action="grant",
                document__slug="publishing",
                document__version=document.version,
            ).exists()
            if (
                person.consent_version != person.manager_version
                or person.consent_revoked_at
                or not current_grant
            ):
                person.consent_version = person.manager_version
                person.consent_revoked_at = None
                person.save(update_fields=["consent_version", "consent_revoked_at"])
                RepresentationAction.objects.create(
                    person=person,
                    subject=request.user,
                    manager_version=person.manager_version,
                    action="grant",
                    document=document,
                )
        return redirect("person_verification", person_id=person.pk)
    return render(
        request, "core/representation.html", {"person": person, "form": form, "document": document}
    )


@login_required
@require_http_methods(["GET", "POST"])
def age(request, person_id):
    person = get_object_or_404(Person, pk=person_id, subject=request.user)
    form = SimulationForm(request.POST or None)
    if settings.PRODUCTION or settings.VERIFICATION_PROVIDER != "simulator":
        return HttpResponse("Provider not yet integrated", status=503)
    if request.method == "POST" and form.is_valid():
        if limited(request, "age-simulator", 10):
            return HttpResponse("Too many attempts", status=429)
        with transaction.atomic():
            person = Person.objects.select_for_update().get(pk=person.pk)
            check = start_age_check(person, request.user)
            receive_event(simulate_event(check, form.cleaned_data["outcome"]))
        return redirect("person_verification", person_id=person.pk)
    return render(request, "core/simulator.html", {"form": form, "person": person})


@login_required
@require_http_methods(["GET", "POST"])
def phone_start(request, person_id):
    person = get_object_or_404(person_queryset(request.user), pk=person_id)
    form = PhoneForm(request.POST or None)
    if settings.PRODUCTION:
        return HttpResponse("SMS provider not integrated", status=503)
    if request.method == "POST" and form.is_valid():
        if limited(request, "phone-request", 5):
            return HttpResponse("Too many attempts", status=429)
        code = f"{secrets.randbelow(1000000):06}"
        with transaction.atomic():
            person = locked_manager_person(request.user, person.pk)
            PhoneChallenge.objects.filter(person=person, used_at__isnull=True).update(
                used_at=timezone.now()
            )
            challenge = PhoneChallenge.objects.create(
                person=person,
                manager_version=person.manager_version,
                phone=form.cleaned_data["phone"],
                digest=salted_hmac("phone-otp", code, algorithm="sha256").hexdigest(),
                expires_at=timezone.now() + timedelta(minutes=10),
            )
        send_mail(
            "SMS SIMULADO / SIMULATED SMS",
            code,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=True,
        )
        return redirect("phone_confirm", challenge_id=challenge.pk)
    return render(request, "core/form.html", {"form": form, "kind": "phone"})


@login_required
@require_http_methods(["GET", "POST"])
def phone_confirm(request, challenge_id):
    challenge = get_object_or_404(
        PhoneChallenge, pk=challenge_id, person__in=person_queryset(request.user)
    )
    form = CodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                person = locked_manager_person(request.user, challenge.person_id)
                challenge = PhoneChallenge.objects.select_for_update().get(pk=challenge.pk)
                if (
                    challenge.used_at
                    or challenge.expires_at <= timezone.now()
                    or challenge.manager_version != person.manager_version
                    or challenge.attempts >= 5
                ):
                    return HttpResponse("Code unavailable", status=400)
                challenge.attempts += 1
                challenge.save(update_fields=["attempts"])
                if not constant_time_compare(
                    challenge.digest,
                    salted_hmac(
                        "phone-otp", form.cleaned_data["code"], algorithm="sha256"
                    ).hexdigest(),
                ):
                    form.add_error(None, "Código inválido / Invalid code")
                else:
                    claim, _ = PhoneClaim.objects.get_or_create(
                        phone=challenge.phone,
                        defaults={
                            "individual_id": person.individual_id,
                            "agency_id": person.agency_id,
                        },
                    )
                    claim = PhoneClaim.objects.select_for_update().get(pk=claim.pk)
                    if (
                        claim.individual_id != person.individual_id
                        or claim.agency_id != person.agency_id
                    ):
                        return HttpResponse(
                            "Contact requires ownership review / Contacto requiere revisión",
                            status=409,
                        )
                    claim.verified_at = timezone.now()
                    claim.save(update_fields=["verified_at"])
                    person.phone_claim = claim
                    person.save(update_fields=["phone_claim"])
                    challenge.used_at = timezone.now()
                    challenge.save(update_fields=["used_at"])
                    return redirect("person_verification", person_id=person.pk)
        except IntegrityError:
            return HttpResponse("Contact conflict", status=409)
    return render(request, "core/form.html", {"form": form, "kind": "phone_confirm"})


@login_required
@require_POST
def revoke(request, person_id):
    with transaction.atomic():
        person = get_object_or_404(
            Person.objects.select_for_update(), pk=person_id, subject=request.user
        )
        person.consent_revoked_at = timezone.now()
        person.manager_version += 1
        person.age_status = "pending"
        person.save(update_fields=["consent_revoked_at", "manager_version", "age_status"])
        from apps.listings.models import Listing

        Listing.objects.filter(person=person, status="published").update(
            status="paused", available_until=None
        )
        RepresentationAction.objects.create(
            person=person,
            subject=request.user,
            manager_version=person.manager_version,
            action="revoke",
        )
    return redirect("person_verification", person_id=person.pk)


@login_required
@require_http_methods(["GET", "POST"])
def transfer(request, person_id):
    person = get_object_or_404(Person, pk=person_id, subject=request.user)
    form = TransferForm(request.POST or None, initial={"manager_version": person.manager_version})
    if request.method == "POST" and form.is_valid():
        agency = (
            get_object_or_404(Agency, pk=form.cleaned_data["target_agency"])
            if form.cleaned_data["target_agency"]
            else None
        )
        if not agency and request.user.role == "agency":
            return HttpResponse("Agency owner cannot become individual", status=409)
        with transaction.atomic():
            list(
                Agency.objects.select_for_update()
                .filter(
                    pk__in={
                        value
                        for value in [person.agency_id, agency.pk if agency else None]
                        if value
                    }
                )
                .order_by("pk")
            )
            person = Person.objects.select_for_update().get(pk=person.pk)
            if person.subject_id != request.user.pk:
                return HttpResponse("Subject changed", status=403)
            expected = form.cleaned_data["manager_version"]
            if person.manager_version != expected:
                repeated = (
                    person.manager_version == expected + 1
                    and person.agency_id == (agency.pk if agency else None)
                    and person.individual_id == (None if agency else request.user.pk)
                    and RepresentationAction.objects.filter(
                        person=person,
                        subject=request.user,
                        manager_version=person.manager_version,
                        action="transfer",
                    ).exists()
                )
                if repeated:
                    return redirect("person_verification", person_id=person.pk)
                return HttpResponse(
                    "Transfer changed; reload / Traslado cambiado; recarga", status=409
                )
            if agency and person.agency_id != agency.pk:
                if pending_person_count(agency) >= settings.AGENCY_PENDING_PERSON_LIMIT:
                    return HttpResponse(
                        "Cuota pendiente de revisión / Quota awaiting review", status=409
                    )
            previous_manager_kind = "agency" if person.agency_id else "individual"
            previous_manager_id = str(person.agency_id or person.individual_id)
            person.agency = agency
            person.individual = None if agency else request.user
            person.assigned_editor = None
            person.phone_claim = None
            person.manager_version += 1
            person.manager_review_status = "pending"
            person.consent_version = 0
            person.consent_revoked_at = timezone.now()
            person.age_status = "pending"
            person.save()
            from apps.listings.models import Listing

            Listing.objects.filter(person=person, status="published").update(
                status="paused", available_until=None
            )
            RepresentationAction.objects.create(
                person=person,
                subject=request.user,
                manager_version=person.manager_version,
                action="transfer",
                previous_manager_kind=previous_manager_kind,
                previous_manager_id=previous_manager_id,
            )
        return redirect("person_verification", person_id=person.pk)
    return render(
        request,
        "core/form.html",
        {"form": form, "kind": "transfer"},
        status=400 if request.method == "POST" else 200,
    )
