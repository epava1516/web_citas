"""Scoped synthetic verification adapter. No real identity provider is connected."""

import json
import uuid
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import User

from .crypto import seal
from .models import RightsAccess, RightsProof, RightsProofEvent, RightsRequest
from .rights import allowed, fingerprint
from .rights_scope import locked_case, permitted
from .views import private

PROCEDURE = "rights-simulator-v1"


def enabled():
    return not settings.PRODUCTION and settings.RIGHTS_VERIFICATION_BACKEND == "simulator"


def current_read(user, case):
    return RightsAccess.objects.filter(
        request=case, actor=user, case_version=case.version, message_before__isnull=True
    ).exists()


def complete_read(user, case):
    # Locks on RightsRequest keep incoming messages from changing these pages.
    ids = list(case.messages.order_by("-pk").values_list("pk", flat=True))
    required = {None} | {ids[index] for index in range(49, len(ids) - 1, 50)}
    delivered = set(
        RightsAccess.objects.filter(
            request=case, actor=user, case_version=case.version
        ).values_list("message_before", flat=True)
    )
    return required <= delivered


@sensitive_variables()
def account_source_digest(case):
    """Fresh locked account state, HMAC only; no credentials projected."""
    from apps.core.accounts import token_user_state
    from apps.core.models import User

    if not connection.in_atomic_block:
        raise RuntimeError("Account authority requires case and account locks")
    account = User.objects.select_for_update().get(pk=case.account_subject_id)
    if account.account_erased_at:
        raise ValidationError("Account erased / Cuenta suprimida")
    return fingerprint(
        json.dumps(
            {
                "id": account.pk,
                "first_name": account.first_name,
                "last_name": account.last_name,
                "email": account.email,
                "active": account.is_active,
                "verified": str(account.email_verified_at),
                "authentication": token_user_state(account),
                "mfa_version": account.mfa_version,
            },
            sort_keys=True,
        )
    )


def compatible(case, person, proof, *, case_version=None):
    if case.account_subject_id:
        scoped = bool(
            not person
            and not case.person_id
            and not proof.person_id
            and proof.account_subject_id == case.account_subject_id
            and proof.subject_id_snapshot == str(case.account_subject_id)
            and proof.manager_version is None
            and case.manager_version is None
            and proof.account_source_digest == account_source_digest(case)
            and case.kind != "representation"
        )
    else:
        scoped = bool(
            person
            and not proof.account_subject_id
            and proof.person_id == case.person_id == person.pk
            and proof.person_rights_version == person.rights_version
            and proof.manager_version == case.manager_version == person.manager_version
            and proof.subject_id_snapshot == str(person.subject_id or "")
        )
    return bool(
        scoped
        and proof.scope == case.kind
        and proof.case_version == (case.version if case_version is None else case_version)
        and proof.channel_digest == case.receipt_digest
        and proof.expires_at > timezone.now()
        and case.receipt_expires_at > timezone.now()
        and case.status == "reviewing"
    )


def authorized_proof(case, person, scope):
    """Consumer must hold canonical case/person locks; simulation never passes production."""
    proof = case.proofs.order_by("-created_at", "-pk").first()
    if (
        not enabled()
        or scope != case.kind
        or not proof
        or proof.provider != "simulator"
        or proof.procedure != PROCEDURE
        or proof.status != "passed"
        or case.scope_status != "simulated_passed"
        or not compatible(case, person, proof)
    ):
        raise ValidationError(
            "Identity and scope not established / Identidad y alcance no comprobados"
        )
    return proof


def check_actor(user, case):
    if not user.has_perm("safety.review_rights_request") or not user.mfa_enabled:
        raise PermissionDenied("Rights permission and MFA required")
    if not permitted(user, case):
        raise PermissionDenied("Conflict of interest")


def current_verification_actor(user, session_version, mfa_version, *, verify=False):
    actor = User.objects.filter(pk=user.pk).first()
    if (
        actor is None
        or not actor.is_active
        or actor.account_erased_at is not None
        or not actor.mfa_enabled
        or actor.session_version != session_version
        or actor.mfa_version != mfa_version
        or not actor.has_perm("safety.review_rights_request")
        or (verify and not actor.has_perm("safety.verify_rights_scope"))
    ):
        raise PermissionDenied("Current rights verification authority required")
    return actor


@transaction.atomic
@sensitive_variables()
def start(user, case_id, key, version, reason):
    if not enabled():
        raise PermissionDenied("Rights verification adapter unavailable")
    session_version, mfa_version = user.session_version, user.mfa_version
    user = current_verification_actor(user, session_version, mfa_version)
    case, person, _ = locked_case(case_id)
    user = current_verification_actor(user, session_version, mfa_version)
    check_actor(user, case)
    signature = fingerprint(json.dumps({"version": version, "reason": reason}, sort_keys=True))
    previous = RightsProof.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.initiated_by_id == user.pk
            and previous.payload_digest == signature
        ):
            return previous
        raise ValidationError("Conflicting proof key / Clave de comprobación incompatible")
    if case.version != version or case.status != "reviewing" or case.assigned_to_id != user.pk:
        raise ValidationError("Request changed or not assigned / Solicitud cambiada o no asignada")
    if (
        (
            not case.account_subject_id
            and (not person or case.manager_version != person.manager_version)
        )
        or (case.account_subject_id and case.kind == "representation")
        or not current_read(user, case)
    ):
        raise ValidationError(
            "Link and inspect current reference first / Vincula y consulta la referencia actual"
        )
    if case.receipt_expires_at <= timezone.now() or not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Receipt or reason unavailable / Acuse o motivo no disponible")
    try:
        with transaction.atomic():
            proof = RightsProof.objects.create(
                key=key,
                request=case,
                person=person,
                initiated_by=user,
                case_version=case.version + 1,
                account_subject_id=case.account_subject_id,
                account_source_digest=account_source_digest(case)
                if case.account_subject_id
                else "",
                manager_version=person.manager_version if person else None,
                person_rights_version=person.rights_version if person else 1,
                subject_id_snapshot=str(person.subject_id or "")
                if person
                else str(case.account_subject_id),
                scope=case.kind,
                channel_digest=case.receipt_digest,
                provider="simulator",
                procedure=PROCEDURE,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
                expires_at=timezone.now() + timedelta(hours=24),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting proof key / Clave incompatible") from error
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return proof


def simulate_event(proof_id, key, version, outcome, reason):
    if not enabled():
        raise PermissionDenied("Rights simulator disabled")
    return signing.dumps(
        {
            "proof": str(proof_id),
            "key": str(key),
            "version": version,
            "outcome": outcome,
            "reason": reason,
        },
        salt=PROCEDURE,
    )


@transaction.atomic
@sensitive_variables()
def receive_event(user, payload):
    if not enabled():
        raise PermissionDenied("Rights simulator disabled")
    session_version, mfa_version = user.session_version, user.mfa_version
    data = signing.loads(payload, salt=PROCEDURE, max_age=300)
    user = current_verification_actor(user, session_version, mfa_version, verify=True)
    initial = RightsProof.objects.get(pk=data["proof"])
    case, person, _ = locked_case(initial.request_id)
    user = current_verification_actor(user, session_version, mfa_version, verify=True)
    check_actor(user, case)
    if not user.has_perm("safety.verify_rights_scope") or user.pk in {
        initial.initiated_by_id,
        case.assigned_to_id,
    }:
        raise PermissionDenied("Independent verifier required")
    proof = RightsProof.objects.select_for_update().get(pk=initial.pk)
    user = current_verification_actor(user, session_version, mfa_version, verify=True)
    check_actor(user, case)
    if user.pk in {proof.initiated_by_id, case.assigned_to_id}:
        raise PermissionDenied("Independent verifier required")
    signature = fingerprint(json.dumps(data, sort_keys=True))
    previous = RightsProofEvent.objects.filter(key=data["key"]).first()
    if previous:
        if (
            previous.proof_id == proof.pk
            and previous.verifier_id == user.pk
            and previous.payload_digest == signature
        ):
            return proof
        raise ValidationError("Conflicting event replay / Evento incompatible")
    if (
        data["outcome"] not in {"pending", "failed", "passed"}
        or not isinstance(data["reason"], str)
        or not 10 <= len(data["reason"].strip()) <= 2000
        or data["version"] != case.version
        or proof.status != "pending"
        or proof.provider != "simulator"
        or proof.procedure != PROCEDURE
        or not compatible(case, person, proof)
        or case.proofs.order_by("-created_at", "-pk").first().pk != proof.pk
        or not current_read(user, case)
        or (data["outcome"] == "passed" and not complete_read(user, case))
    ):
        raise ValidationError("Proof or evidence changed / Comprobación o evidencia cambiada")
    try:
        with transaction.atomic():
            RightsProofEvent.objects.create(
                key=data["key"],
                proof=proof,
                verifier=user,
                outcome=data["outcome"],
                expected_version=case.version,
                payload_digest=signature,
                encrypted_reason=seal({"reason": data["reason"]}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting event key / Clave de evento incompatible") from error
    case.version += 1
    case.scope_status = "simulated_passed" if data["outcome"] == "passed" else "unverified"
    proof.case_version = case.version
    proof.status = data["outcome"]
    proof.save(update_fields=["case_version", "status"])
    case.save(update_fields=["version", "scope_status"])
    return proof


class VerificationForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("start", "Iniciar comprobación simulada / Start simulated check"),
            (
                "result",
                "Registrar resultado simulado (otro revisor) / Record simulated outcome (another reviewer)",
            ),
        ]
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[
            ("", "---------"),
            ("pending", "Pendiente / Pending"),
            ("failed", "Fallido / Failed"),
            ("passed", "Aprobado simulado / Simulated pass"),
        ],
    )
    reason = forms.CharField(
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def verification(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    if not enabled():
        return private(HttpResponse("Rights verification adapter not integrated", status=503))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Conflict of interest", status=403))
    form = VerificationForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        values = dict(form.cleaned_data)
        operation, outcome = values.pop("operation"), values.pop("outcome")
        try:
            if operation == "start":
                if outcome:
                    raise ValidationError(
                        "Outcome belongs to independent result / Resultado separado"
                    )
                start(request.user, case_id, **values)
            else:
                proof = case.proofs.order_by("-created_at", "-pk").first()
                if not proof:
                    raise ValidationError("Start check first / Inicia primero la comprobación")
                receive_event(request.user, simulate_event(proof.pk, outcome=outcome, **values))
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("rights_inspect", case_id=case.pk))
    return private(
        render(
            request, "safety/rights_verification.html", {"case": case, "form": form}, status=status
        )
    )
